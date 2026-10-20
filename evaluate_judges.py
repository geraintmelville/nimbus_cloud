"""Evaluate LLM judges against the gold reference.

The summary compares scores, verdicts, operational errors, cost, latency and
consistency. Dimension diagnostics report per-dimension bias and, for accuracy,
coverage and tone/clarity, counts in the order judge FAIL / judge
PARTIAL-or-FAIL / gold FAIL calls. Only valid parsed calls are included.
The lowest score for an answer determines its verdict: 2 or below = FAIL,
exactly 3 = PARTIAL, and 4 or above = PASS.

Only judge calls with parse_ok == "true" are used for the agreement measures;
every call counts towards error rate, cost and latency.

Writes:
  outputs/judge_evaluation.csv             one row per judge
  outputs/judge_dimension_diagnostics.csv  one row per judge and rubric dimension
"""

import csv
import statistics
from collections import defaultdict
from pathlib import Path

from run_judges import JUDGE_MODELS, RUBRIC


RESPONSES_PATH = Path("outputs/judge_responses.csv")
REFERENCE_PATH = Path("inputs/gold_reference.csv")
SUMMARY_PATH = Path("outputs/judge_evaluation.csv")
DIMENSION_PATH = Path("outputs/judge_dimension_diagnostics.csv")

FAIL = 2  # a rubric score this low counts as a flagged problem
PARTIAL = 3  # a lowest score of exactly this gives a PARTIAL verdict
VERDICT_LEVEL = {"FAIL": 0, "PARTIAL": 1, "PASS": 2}
FAIL_DIMENSIONS = {
    "Accuracy": "accuracy",
    "Coverage": "coverage",
    "Tone/Clarity": "tone_clarity",
}


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def mean_measure(rows, field, precision):
    values = [float(row[field]) for row in rows if row[field]]
    return round(statistics.mean(values), precision) if values else ""


def percent(numerator, denominator, precision=2):
    return round(100 * numerator / denominator, precision) if denominator else ""


def is_flagged(score):
    return score <= FAIL


def verdict(scores):
    """FAIL if the lowest score is 2 or below, PARTIAL if it is 3, otherwise PASS."""
    lowest = min(scores)
    if is_flagged(lowest):
        return "FAIL"
    if lowest == PARTIAL:
        return "PARTIAL"
    return "PASS"


def verdict_credit(judged, gold):
    """1 for an exact match, 0.5 if one level away, 0 if two levels away."""
    return 1 - 0.5 * abs(VERDICT_LEVEL[judged] - VERDICT_LEVEL[gold])


def main():
    responses = read_csv(RESPONSES_PATH)
    reference_rows = read_csv(REFERENCE_PATH)

    gold_scores = {
        row["answer_id"]: {field: int(row[field]) for field in RUBRIC}
        for row in reference_rows
    }
    gold_verdicts = {row["answer_id"]: row["verdict"] for row in reference_rows}
    calls = defaultdict(list)
    for row in responses:
        calls[row["judge_model"]].append(row)

    summary_fields = [
        "judge_model",
        "mae_overall",
        "verdict_exact_match",
        "verdict_partial",
        "error_rate",
        "mean_cost_cents",
        "mean_latency",
        "consistency",
    ]
    dimension_fields = [
        "judge_model",
        "dimension",
        "bias",
        "judge_fail_calls",
        "judge_partial_or_fail_calls",
        "gold_fail_calls",
    ]
    summary_rows = []
    dimension_rows = []

    for model in JUDGE_MODELS:
        model_calls = calls[model]
        valid = [
            row
            for row in model_calls
            if row["parse_ok"].strip().lower() == "true"
            and row["answer_id"] in gold_scores
        ]

        # Compare scores with gold and calculate per-dimension bias.
        all_errors = []
        for dimension in RUBRIC:
            errors = [
                int(row[dimension]) - gold_scores[row["answer_id"]][dimension]
                for row in valid
            ]
            all_errors.extend(errors)

            gold_flags = [
                is_flagged(gold_scores[row["answer_id"]][dimension])
                for row in valid
            ]
            if dimension in FAIL_DIMENSIONS.values():
                judge_fail_calls = sum(
                    int(row[dimension]) <= FAIL and gold_flag
                    for row, gold_flag in zip(valid, gold_flags)
                )
                judge_partial_or_fail_calls = sum(
                    int(row[dimension]) <= PARTIAL and gold_flag
                    for row, gold_flag in zip(valid, gold_flags)
                )
                gold_fail_calls = sum(gold_flags)
            else:
                judge_fail_calls = ""
                judge_partial_or_fail_calls = ""
                gold_fail_calls = ""

            dimension_rows.append(
                {
                    "judge_model": model,
                    "dimension": dimension,
                    "bias": round(statistics.mean(errors), 3) if errors else "",
                    "judge_fail_calls": judge_fail_calls,
                    "judge_partial_or_fail_calls": judge_partial_or_fail_calls,
                    "gold_fail_calls": gold_fail_calls,
                }
            )

        # Compare each answer's verdict with the verdict derived from gold scores.
        exact_matches = 0
        partial_credit_total = 0
        for row in valid:
            judged = verdict(int(row[field]) for field in RUBRIC)
            gold = gold_verdicts[row["answer_id"]]
            exact_matches += judged == gold
            partial_credit_total += verdict_credit(judged, gold)

        # Consistency: spread of the overall score across repeats of each answer.
        repeats_by_answer = defaultdict(list)
        for row in valid:
            repeats_by_answer[row["answer_id"]].append(
                statistics.mean(int(row[field]) for field in RUBRIC)
            )
        repeat_spreads = [
            statistics.pstdev(scores)
            for scores in repeats_by_answer.values()
            if len(scores) > 1
        ]

        mean_cost_usd = mean_measure(model_calls, "cost_usd", 8)
        mean_cost = (
            round(mean_cost_usd * 100, 8)
            if mean_cost_usd != ""
            else ""
        )
        mean_latency = mean_measure(model_calls, "latency_seconds", 3)

        summary_rows.append(
            {
                "judge_model": model,
                "mae_overall": (
                    round(statistics.mean(abs(e) for e in all_errors), 3)
                    if all_errors
                    else ""
                ),
                "verdict_exact_match": percent(exact_matches, len(valid)),
                "verdict_partial": percent(partial_credit_total, len(valid)),
                "error_rate": (
                    round(
                        100
                        - 100
                        * sum(
                            row.get("response_status", "").strip().lower() == "ok"
                            for row in model_calls
                        )
                        / len(model_calls),
                        2,
                    )
                    if model_calls
                    else ""
                ),
                "mean_cost_cents": mean_cost,
                "mean_latency": mean_latency,
                "consistency": (
                    round(statistics.mean(repeat_spreads), 3) if repeat_spreads else ""
                ),
            }
        )

    write_csv(SUMMARY_PATH, summary_fields, summary_rows)
    write_csv(DIMENSION_PATH, dimension_fields, dimension_rows)
    print(f"Wrote judge evaluation table to {SUMMARY_PATH}")
    print(f"Wrote per-dimension diagnostics to {DIMENSION_PATH}")


if __name__ == "__main__":
    main()
