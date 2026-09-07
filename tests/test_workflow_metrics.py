import json
import tempfile
import unittest
from pathlib import Path

from scripts.workflow_metrics import (
    OllamaCallMetrics,
    aggregate_ollama_metrics,
    format_duration,
    get_run,
    linear_projection,
    update_run,
)


class WorkflowMetricsTests(unittest.TestCase):
    def test_aggregate_ollama_metrics(self):
        totals = aggregate_ollama_metrics(
            [
                OllamaCallMetrics(
                    model="qwen2.5:3b",
                    prompt_tokens=100,
                    completion_tokens=25,
                    total_duration_ns=1_500_000_000,
                ),
                OllamaCallMetrics(
                    model="qwen2.5:3b",
                    prompt_tokens=40,
                    completion_tokens=10,
                    total_duration_ns=500_000_000,
                ),
            ]
        )
        self.assertEqual(totals["prompt_tokens"], 140)
        self.assertEqual(totals["completion_tokens"], 35)
        self.assertEqual(totals["total_tokens"], 175)
        self.assertEqual(totals["ollama_total_duration_seconds"], 2.0)

    def test_historical_projection(self):
        projected = linear_projection(52 * 60 + 11, 6, 13)
        self.assertAlmostEqual(projected, 6783.833333333333)
        self.assertEqual(format_duration(projected), "1h 53m 4s")

    def test_update_run(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runs.jsonl"
            path.write_text(json.dumps({"run_id": "abc", "status": "new"}) + "\n")
            updated = update_run(path, "abc", {"status": "approved"})
            self.assertEqual(updated["status"], "approved")
            self.assertEqual(get_run(path, "abc")["status"], "approved")


if __name__ == "__main__":
    unittest.main()
