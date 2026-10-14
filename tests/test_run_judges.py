import csv
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import run_judges


class RunJudgesTests(unittest.TestCase):
    def test_truncated_response_does_not_stop_remaining_calls(self):
        truncated = {
            "response_status": "truncated",
            "raw_response": '{"accuracy":',
            "finish_reason": "length",
        }
        successful = {
            "response_status": "ok",
            "parsed": {
                "accuracy": 4,
                "brevity": 4,
                "coverage": 4,
                "tone_clarity": 4,
                "reasoning": "The response follows the source.",
            },
        }
        old_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            answers_path = temporary_path / "answers.csv"
            with answers_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=["answer_id", "question", "answer"]
                )
                writer.writeheader()
                writer.writerow(
                    {"answer_id": "A", "question": "Question", "answer": "Answer"}
                )
            (temporary_path / "outputs").mkdir()
            os.chdir(temporary_path)
            try:
                session = MagicMock()
                session.__enter__.return_value = session
                with (
                    patch.object(run_judges, "OPENROUTER_API_KEY", "test-key"),
                    patch.object(run_judges, "CANDIDATE_ANSWERS_PATH", answers_path),
                    patch.object(run_judges, "JUDGE_MODELS", ["test/model"]),
                    patch.object(run_judges, "REPEATS", 2),
                    patch.object(
                        run_judges,
                        "call_judge",
                        side_effect=[truncated, successful],
                    ) as call_judge,
                    patch.object(run_judges.requests, "Session", return_value=session),
                ):
                    exit_code = run_judges.run()

                self.assertEqual(call_judge.call_count, 2)
                self.assertEqual(exit_code, 1)
                with Path("outputs/judge_responses.csv").open(
                    encoding="utf-8", newline=""
                ) as handle:
                    rows = list(csv.DictReader(handle))
                self.assertEqual(
                    [row["response_status"] for row in rows], ["truncated", "ok"]
                )
            finally:
                os.chdir(old_cwd)


if __name__ == "__main__":
    unittest.main()
