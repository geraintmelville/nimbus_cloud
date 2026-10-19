import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import evaluate_judges


class AnalyzeJudgesTests(unittest.TestCase):
    def test_verdict_uses_lowest_dimension_score(self):
        self.assertEqual(evaluate_judges.verdict([2, 5]), "FAIL")
        self.assertEqual(evaluate_judges.verdict([3, 5]), "PARTIAL")
        self.assertEqual(evaluate_judges.verdict([4, 5]), "PASS")

    def test_writes_requested_summary_and_bias_without_recall(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            responses_path = temporary_path / "responses.csv"
            references_path = temporary_path / "references.csv"
            output_path = temporary_path / "evaluation.csv"
            dimension_path = temporary_path / "diagnostics.csv"
            fields = [
                "judge_model",
                "answer_id",
                "response_status",
                "parse_ok",
                *evaluate_judges.RUBRIC,
                "cost_usd",
                "latency_seconds",
                "prompt_tokens",
                "completion_tokens",
            ]
            score_fields = list(evaluate_judges.RUBRIC)
            with responses_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                for status in ("ok", "format_error", "format_error", "format_error"):
                    writer.writerow({
                        "judge_model": "test/model",
                        "answer_id": "A",
                        "response_status": status,
                        "parse_ok": str(status == "ok").lower(),
                        **dict.fromkeys(score_fields, "4"),
                        "cost_usd": "0.01",
                        "latency_seconds": "1.5",
                        "prompt_tokens": "100",
                        "completion_tokens": "20",
                    })
            with references_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "answer_id",
                        "verdict",
                        *evaluate_judges.RUBRIC,
                    ],
                )
                writer.writeheader()
                writer.writerow({
                    "answer_id": "A",
                    "verdict": "PASS",
                    **dict.fromkeys(evaluate_judges.RUBRIC, "4"),
                })

            with (
                patch.object(evaluate_judges, "RESPONSES_PATH", responses_path),
                patch.object(evaluate_judges, "REFERENCE_PATH", references_path),
                patch.object(evaluate_judges, "SUMMARY_PATH", output_path),
                patch.object(evaluate_judges, "DIMENSION_PATH", dimension_path),
                patch.object(evaluate_judges, "JUDGE_MODELS", ["test/model"]),
            ):
                evaluate_judges.main()

            with output_path.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                result = next(reader)
            self.assertEqual(
                reader.fieldnames,
                [
                    "judge_model",
                    "mae_overall",
                    "verdict_exact_match",
                    "verdict_partial",
                    "error_rate",
                    "mean_cost_cents",
                    "mean_latency",
                    "consistency",
                ],
            )
            self.assertEqual(result["judge_model"], "test/model")
            self.assertEqual(result["mae_overall"], "0")
            self.assertEqual(result["verdict_exact_match"], "100.0")
            self.assertEqual(result["verdict_partial"], "100.0")
            self.assertEqual(result["error_rate"], "75.0")
            self.assertEqual(result["mean_cost_cents"], "1.0")
            self.assertEqual(result["mean_latency"], "1.5")

            with dimension_path.open(encoding="utf-8", newline="") as handle:
                diagnostics = csv.DictReader(handle)
                diagnostic = next(diagnostics)
            self.assertEqual(
                diagnostics.fieldnames,
                [
                    "judge_model",
                    "dimension",
                    "mae",
                    "bias",
                    "gold_flagged_calls",
                    "judge_flagged_calls",
                    "true_flags",
                    "flag_precision",
                ],
            )
            self.assertIn("bias", diagnostics.fieldnames)
            self.assertNotIn("within1", diagnostics.fieldnames)
            self.assertNotIn("flag_recall", diagnostics.fieldnames)
            self.assertEqual(diagnostic["bias"], "0")


if __name__ == "__main__":
    unittest.main()
