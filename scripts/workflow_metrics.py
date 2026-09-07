#!/usr/bin/env python3
"""Aggregate-only workflow telemetry for AARI Nexus.

This module deliberately avoids storing prompts, model responses, filenames, or
student names. Detailed reports stay local; the metrics log contains only the
numbers needed to audit time, cost, review, and quality.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = 1


@dataclass
class OllamaCallMetrics:
    """Metrics returned by one non-streaming Ollama generation call."""

    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_duration_ns: int = 0
    load_duration_ns: int = 0
    prompt_eval_duration_ns: int = 0
    eval_duration_ns: int = 0

    @classmethod
    def from_response(cls, model: str, response: dict[str, Any]) -> "OllamaCallMetrics":
        return cls(
            model=model,
            prompt_tokens=int(response.get("prompt_eval_count") or 0),
            completion_tokens=int(response.get("eval_count") or 0),
            total_duration_ns=int(response.get("total_duration") or 0),
            load_duration_ns=int(response.get("load_duration") or 0),
            prompt_eval_duration_ns=int(response.get("prompt_eval_duration") or 0),
            eval_duration_ns=int(response.get("eval_duration") or 0),
        )


@dataclass
class WorkflowRun:
    """One auditable Nexus workflow run."""

    run_id: str
    workflow: str
    status: str
    started_at: str
    completed_at: str
    wall_clock_seconds: float
    input_document_count: int
    input_page_count: int
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    ollama_total_duration_seconds: float
    direct_model_cost_usd: float
    output_sha256: str | None = None
    output_name: str | None = None
    human_review_seconds: float | None = None
    corrections_count: int | None = None
    approved: bool | None = None
    approved_by: str | None = None
    notes: str | None = None
    schema_version: int = SCHEMA_VERSION
    recorded_at: str = field(default_factory=lambda: utc_now_iso())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def aggregate_ollama_metrics(calls: Iterable[OllamaCallMetrics]) -> dict[str, Any]:
    call_list = list(calls)
    models = sorted({item.model for item in call_list})
    prompt_tokens = sum(item.prompt_tokens for item in call_list)
    completion_tokens = sum(item.completion_tokens for item in call_list)
    return {
        "model": ",".join(models),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "ollama_total_duration_seconds": round(
            sum(item.total_duration_ns for item in call_list) / 1_000_000_000,
            6,
        ),
    }


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} of {path}") from exc
    return records


def get_run(path: Path, run_id: str) -> dict[str, Any]:
    for record in read_jsonl(path):
        if record.get("run_id") == run_id:
            return record
    raise KeyError(f"Run ID not found: {run_id}")


def update_run(path: Path, run_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    records = read_jsonl(path)
    updated_record: dict[str, Any] | None = None

    for record in records:
        if record.get("run_id") == run_id:
            record.update(updates)
            record["recorded_at"] = utc_now_iso()
            updated_record = record
            break

    if updated_record is None:
        raise KeyError(f"Run ID not found: {run_id}")

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=str(path.parent),
        text=True,
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise

    return updated_record


def format_duration(seconds: float | int | None) -> str:
    if seconds is None:
        return "not recorded"
    rounded = max(0, int(round(float(seconds))))
    hours, remainder = divmod(rounded, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def linear_projection(sample_seconds: float, sample_count: int, target_count: int) -> float:
    if sample_count <= 0:
        raise ValueError("sample_count must be greater than zero")
    if target_count < 0:
        raise ValueError("target_count cannot be negative")
    return (sample_seconds / sample_count) * target_count
