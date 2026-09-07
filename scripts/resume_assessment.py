#!/usr/bin/env python3
"""Run and measure the local AARI Nexus resume-assessment workflow.

No resume content, student names, prompts, or generated analysis is written to
the metrics log. Reports stay in a local, gitignored directory. The metrics log
captures volume, elapsed time, Ollama token counts, direct model cost, output
hash, reviewer time, corrections, and approval.

Examples:
  python3 scripts/resume_assessment.py run ~/AARI/resumes \
      --model qwen2.5:3b --output reports/cohort_assessment.md

  python3 scripts/resume_assessment.py finalize RUN_ID \
      --review-minutes 37.5 --corrections 4 --approved-by "Nolan Code" --approved

  python3 scripts/resume_assessment.py show RUN_ID
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

try:
    from pypdf import PdfReader
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency: pypdf. Install it with "
        "`python3 -m pip install -r requirements-workflows.txt`."
    ) from exc

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.workflow_metrics import (  # noqa: E402
    OllamaCallMetrics,
    WorkflowRun,
    aggregate_ollama_metrics,
    append_jsonl,
    format_duration,
    get_run,
    sha256_file,
    update_run,
    utc_now_iso,
)

DEFAULT_MODEL = "qwen2.5:3b"
DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_METRICS_PATH = ROOT / "logs" / "workflow_runs.jsonl"
DEFAULT_REPORTS_DIR = ROOT / "reports"
MAX_RESUME_CHARACTERS = 18_000
MAX_COHORT_CHARACTERS = 60_000

INDIVIDUAL_PROMPT = """You are supporting the Atlanta AI & Robotics Initiative.
Analyze the resume below using only evidence present in the resume. Do not infer
credentials, employment, outcomes, or technical depth that are not documented.

Return these exact headings:
1. Positioning snapshot
2. Strongest documented evidence
3. Evidence gaps or risks
4. Recommended role lane
5. Three prioritized next actions
6. Questions for human review

Keep the response concise, specific, and suitable for a human reviewer.

RESUME:
{resume_text}
"""

COHORT_PROMPT = """You are supporting the Atlanta AI & Robotics Initiative.
Synthesize the anonymized individual resume assessments below. Do not invent
facts. Return these exact headings:
1. Cohort strengths
2. Recurring evidence gaps
3. Prioritized interventions
4. Suggested mentorship lanes
5. Decisions that still require human judgment

ASSESSMENTS:
{assessments}
"""


def read_pdf(path: Path) -> tuple[str, int]:
    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        raise RuntimeError(f"Could not open PDF: {path}") from exc

    pages: list[str] = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception as exc:
            raise RuntimeError(f"Could not extract text from {path}") from exc
    return "\n".join(pages).strip(), len(reader.pages)


def ollama_generate(
    *,
    model: str,
    prompt: str,
    url: str,
    timeout_seconds: int,
) -> tuple[str, OllamaCallMetrics]:
    payload = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            data: dict[str, Any] = json.loads(response.read())
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Ollama request failed at {url}. Confirm Ollama is running and the model is installed."
        ) from exc

    if data.get("error"):
        raise RuntimeError(f"Ollama returned an error: {data['error']}")

    return str(data.get("response") or "").strip(), OllamaCallMetrics.from_response(model, data)


def make_run_id() -> str:
    timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    return f"resume-{timestamp}-{uuid.uuid4().hex[:8]}"


def build_report(
    *,
    run_id: str,
    model: str,
    document_count: int,
    page_count: int,
    individual_assessments: list[str],
    cohort_assessment: str,
) -> str:
    lines = [
        "# AARI Nexus Cohort Resume Assessment",
        "",
        f"- Run ID: `{run_id}`",
        f"- Model: `{model}`",
        f"- Source resumes: **{document_count}**",
        f"- Source pages: **{page_count}**",
        "- Direct model/API charge: **$0.00** (local Ollama; excludes hardware, electricity, and human review)",
        "",
        "## Cohort synthesis",
        "",
        cohort_assessment,
        "",
        "## Individual assessments",
        "",
    ]

    for index, assessment in enumerate(individual_assessments, start=1):
        lines.extend([f"### Candidate {index}", "", assessment, ""])

    lines.extend(
        [
            "## Human-review requirement",
            "",
            "This report is decision support. A person must verify every recommendation before it is used for coaching, selection, placement, or rejection.",
            "",
        ]
    )
    return "\n".join(lines)


def run_assessment(args: argparse.Namespace) -> int:
    input_dir = Path(args.input_dir).expanduser().resolve()
    if not input_dir.is_dir():
        raise SystemExit(f"Input directory does not exist: {input_dir}")

    pdf_paths = sorted(path for path in input_dir.rglob("*.pdf") if path.is_file())
    if not pdf_paths:
        raise SystemExit(f"No PDF resumes found in: {input_dir}")

    output_path = Path(args.output).expanduser()
    if not output_path.is_absolute():
        output_path = (ROOT / output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    metrics_path = Path(args.metrics_path).expanduser()
    if not metrics_path.is_absolute():
        metrics_path = (ROOT / metrics_path).resolve()

    run_id = make_run_id()
    started_at = utc_now_iso()
    start = time.perf_counter()
    page_count = 0
    assessments: list[str] = []
    calls: list[OllamaCallMetrics] = []

    print(f"Run ID: {run_id}")
    print(f"Found {len(pdf_paths)} PDF resumes.")

    for index, path in enumerate(pdf_paths, start=1):
        resume_text, pages = read_pdf(path)
        page_count += pages
        if not resume_text:
            raise RuntimeError(f"No extractable text found in PDF #{index}")

        prompt = INDIVIDUAL_PROMPT.format(
            resume_text=resume_text[: args.max_resume_characters]
        )
        print(f"Assessing resume {index}/{len(pdf_paths)} ({pages} page(s))...")
        response, call_metrics = ollama_generate(
            model=args.model,
            prompt=prompt,
            url=args.ollama_url,
            timeout_seconds=args.timeout_seconds,
        )
        assessments.append(response)
        calls.append(call_metrics)

    cohort_input = "\n\n".join(
        f"CANDIDATE {index}\n{assessment}"
        for index, assessment in enumerate(assessments, start=1)
    )[: args.max_cohort_characters]
    print("Building cohort synthesis...")
    cohort_assessment, cohort_metrics = ollama_generate(
        model=args.model,
        prompt=COHORT_PROMPT.format(assessments=cohort_input),
        url=args.ollama_url,
        timeout_seconds=args.timeout_seconds,
    )
    calls.append(cohort_metrics)

    report = build_report(
        run_id=run_id,
        model=args.model,
        document_count=len(pdf_paths),
        page_count=page_count,
        individual_assessments=assessments,
        cohort_assessment=cohort_assessment,
    )
    output_path.write_text(report, encoding="utf-8")

    wall_clock_seconds = round(time.perf_counter() - start, 6)
    completed_at = utc_now_iso()
    totals = aggregate_ollama_metrics(calls)
    run = WorkflowRun(
        run_id=run_id,
        workflow="cohort_resume_assessment",
        status="awaiting_human_review",
        started_at=started_at,
        completed_at=completed_at,
        wall_clock_seconds=wall_clock_seconds,
        input_document_count=len(pdf_paths),
        input_page_count=page_count,
        model=totals["model"],
        prompt_tokens=totals["prompt_tokens"],
        completion_tokens=totals["completion_tokens"],
        total_tokens=totals["total_tokens"],
        ollama_total_duration_seconds=totals["ollama_total_duration_seconds"],
        direct_model_cost_usd=0.0,
        output_sha256=sha256_file(output_path),
        output_name=output_path.name,
        notes="Local Ollama direct model/API cost only; excludes hardware, electricity, and human labor.",
    )
    append_jsonl(metrics_path, run.to_dict())

    print("\nAssessment complete.")
    print(f"Source documents : {len(pdf_paths)}")
    print(f"Source pages     : {page_count}")
    print(f"Wall-clock time  : {format_duration(wall_clock_seconds)}")
    print(f"Total tokens     : {totals['total_tokens']}")
    print("Direct API cost  : $0.00")
    print(f"Report           : {output_path}")
    print(f"Metrics          : {metrics_path}")
    print("\nFinalize after human review with:")
    print(
        f"python3 scripts/resume_assessment.py finalize {run_id} "
        "--review-minutes MINUTES --corrections COUNT --approved-by NAME --approved"
    )
    return 0


def finalize_run(args: argparse.Namespace) -> int:
    metrics_path = Path(args.metrics_path).expanduser()
    if not metrics_path.is_absolute():
        metrics_path = (ROOT / metrics_path).resolve()

    review_seconds: float | None = None
    if args.review_seconds is not None:
        review_seconds = args.review_seconds
    elif args.review_minutes is not None:
        review_seconds = args.review_minutes * 60

    updates: dict[str, Any] = {
        "status": "approved" if args.approved else "reviewed",
        "human_review_seconds": review_seconds,
        "corrections_count": args.corrections,
        "approved": bool(args.approved),
        "approved_by": args.approved_by,
    }
    if args.notes:
        updates["notes"] = args.notes

    record = update_run(metrics_path, args.run_id, updates)
    print(f"Finalized {args.run_id}.")
    print(f"Human review     : {format_duration(record.get('human_review_seconds'))}")
    print(f"Corrections      : {record.get('corrections_count')}")
    print(f"Approved         : {record.get('approved')}")
    return 0


def show_run(args: argparse.Namespace) -> int:
    metrics_path = Path(args.metrics_path).expanduser()
    if not metrics_path.is_absolute():
        metrics_path = (ROOT / metrics_path).resolve()
    record = get_run(metrics_path, args.run_id)

    print(json.dumps(record, indent=2, sort_keys=True))
    print("\nStage-ready proof:")
    print(
        "Nexus processed "
        f"{record['input_document_count']} resumes totaling "
        f"{record['input_page_count']} pages in "
        f"{format_duration(record['wall_clock_seconds'])}, with "
        f"${record['direct_model_cost_usd']:.2f} in direct model/API charges. "
        f"Human review took {format_duration(record.get('human_review_seconds'))} "
        f"and produced {record.get('corrections_count', 'not recorded')} corrections."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Measured AARI Nexus resume workflow")
    parser.add_argument(
        "--metrics-path",
        default=str(DEFAULT_METRICS_PATH),
        help=f"JSONL metrics path (default: {DEFAULT_METRICS_PATH})",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a measured local assessment")
    run_parser.add_argument("input_dir", help="Directory containing PDF resumes")
    run_parser.add_argument(
        "--output",
        default=str(DEFAULT_REPORTS_DIR / "cohort_resume_assessment.md"),
        help="Local Markdown report path",
    )
    run_parser.add_argument("--model", default=DEFAULT_MODEL)
    run_parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL)
    run_parser.add_argument("--timeout-seconds", type=int, default=300)
    run_parser.add_argument(
        "--max-resume-characters", type=int, default=MAX_RESUME_CHARACTERS
    )
    run_parser.add_argument(
        "--max-cohort-characters", type=int, default=MAX_COHORT_CHARACTERS
    )
    run_parser.set_defaults(handler=run_assessment)

    finalize_parser = subparsers.add_parser(
        "finalize", help="Attach human-review and quality metrics"
    )
    finalize_parser.add_argument("run_id")
    review_group = finalize_parser.add_mutually_exclusive_group(required=True)
    review_group.add_argument("--review-minutes", type=float)
    review_group.add_argument("--review-seconds", type=float)
    finalize_parser.add_argument("--corrections", type=int, required=True)
    finalize_parser.add_argument("--approved-by", required=True)
    finalize_parser.add_argument("--approved", action="store_true")
    finalize_parser.add_argument("--notes")
    finalize_parser.set_defaults(handler=finalize_run)

    show_parser = subparsers.add_parser("show", help="Show one run and stage copy")
    show_parser.add_argument("run_id")
    show_parser.set_defaults(handler=show_run)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.handler(args))
    except (KeyError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
