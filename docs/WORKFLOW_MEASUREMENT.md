# AARI Nexus workflow measurement

AARI should never put an unmeasured AI-efficiency claim onstage, in a proposal,
or in a grant report. Nexus therefore records the full operating chain:

- source document count and page count
- wall-clock runtime
- model and token counts returned by Ollama
- direct model/API cost
- human-review time
- corrections made
- final reviewer and approval state
- SHA-256 hash of the final local report

The log stores aggregate metrics only. It does **not** store resumes, names,
filenames, prompts, or model responses.

## Run the resume workflow

```bash
python3 -m pip install -r requirements-workflows.txt
ollama pull qwen2.5:3b

python3 scripts/resume_assessment.py run ~/AARI/resumes \
  --model qwen2.5:3b \
  --output reports/cohort_resume_assessment.md
```

The command prints the run ID and appends an aggregate record to
`logs/workflow_runs.jsonl`.

## Record human review

```bash
python3 scripts/resume_assessment.py finalize RUN_ID \
  --review-minutes 37.5 \
  --corrections 4 \
  --approved-by "Nolan Code" \
  --approved
```

## Generate stage-ready numbers

```bash
python3 scripts/resume_assessment.py show RUN_ID
```

## What the August 2026 records actually support

The historical AARI record supports these facts:

- The source set contained **13 submitted PDF resumes totaling 18 source pages**.
- The 18 pages describe the source material, not the length of the generated report.
- A recorded human review session lasted **52 minutes 11 seconds** and discussed
  six individual resumes, plus shared coaching and questions.
- At the same observed session pace, the linear 13-resume equivalent is
  **1 hour 53 minutes 4 seconds**. This is an extrapolation, not a measured
  13-resume manual run.
- The historical AI generation runtime and provider cost were not logged and
  must not be invented.
- The historical tool was described as using Anthropic, ChatGPT, Gemini, and
  Grok. Treat it as the precursor and benchmark corpus for Nexus, not as a
  measured local Nexus run.
- Local Nexus runs through Ollama incur **$0.00 in direct token/API charges**.
  Hardware, electricity, setup, maintenance, and human review are separate costs.

## Safe keynote wording before the measured rerun

> We tested the standard on ourselves. We had 13 student resumes totaling 18
> pages. A 52-minute human review session reached six of them. AI gave us a
> structured first pass across all 13, but the first system did not log model
> time or cost. That was a measurement failure, so we fixed the workflow in
> Nexus. Every run now records elapsed time, token usage, direct cost, reviewer
> time, corrections, and final sign-off. Execution is not pretending the first
> workflow was perfect. It is making the next claim auditable.

## Keynote wording after the measured rerun

Replace only the bracketed values with output from `show`:

> At our observed human-review pace, 13 resumes would take about 1 hour and 53
> minutes before rewriting. Nexus processed all 13 resumes, 18 source pages, in
> **[MEASURED WALL-CLOCK TIME]**, with **$0.00 in direct model/API charges**.
> Human review then took **[MEASURED REVIEW TIME]** and produced
> **[CORRECTIONS] corrections** before sign-off. That is not adoption. That is
> a measured workflow with an accountable outcome.
