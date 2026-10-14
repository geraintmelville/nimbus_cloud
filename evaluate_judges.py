"""Evaluate LLM judges against the gold reference.

Three layers of measurement, from most to least robust:

1. Headline - raw-score agreement. Every judge score is compared directly with the
   gold score for the same answer and rubric dimension (mean absolute error, and the
   share of scores within +/-1 of gold). No thresholds are involved.
2. Diagnostic - per-dimension problem flags. A score of 2 or below counts as a
   flagged problem; precision and recall of the judge's flags are measured against
   the gold flags, along with signed bias (positive = more lenient than gold).
3. Comparison - three-level verdict. The lowest rubric score decides the verdict:
   2 or below = FAIL, exactly 3 = PARTIAL, 4 or above = PASS. The gold verdict is
   derived from the gold scores with the same rule.

Only judge calls with parse_ok == "true" are used for the agreement measures;
every call counts towards error rate, cost, latency and token use.

Writes:
  outputs/judge_evaluation.csv             one row per judge
  outputs/judge_dimension_diagnostics.csv  one row per judge and rubric dimension
"""

import csv
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from run_judges import JUDGE_MODELS, RUBRIC


RESPONSES_PATH = Path("outputs/judge_responses.csv")
REFERENCE_PATH = Path("inputs/gold_reference.csv")
SUMMARY_PATH = Path("outputs/judge_evaluation.csv")
DIMENSION_PATH = Path("outputs/judge_dimension_diagnostics.csv")

FLAG_AT_OR_BELOW = 2  # a rubric score this low counts as a flagged problem
PARTIAL_SCORE = 3  # a lowest score of exactly this gives a PARTIAL verdict
TOLERANCE = 1  # "close enough" distance from the gold score
VERDICT_LEVEL = {"FAIL": 0, "PARTIAL": 1, "PASS": 2}


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


def verdict(scores):
    """FAIL if the lowest score is 2 or below, PARTIAL if it is 3, otherwise PASS."""
    lowest = min(scores)
    if lowest <= FLAG_AT_OR_BELOW:
        return "FAIL"
    if lowest == PARTIAL_SCORE:
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
    gold_verdicts = {
        answer_id: verdict(scores.values()) for answer_id, scores in gold_scores.items()
    }
    # The gold verdict is derived from the gold scores. Warn if the file disagrees.
    for row in reference_rows:
        listed = row.get("verdict", "").strip().upper()
        derived = gold_verdicts[row["answer_id"]]
        if listed != derived:
            print(
                f"Warning: gold_reference.csv lists answer {row['answer_id']} as "
                f"{listed or 'blank'}, but its scores give {derived}. Using {derived}."
            )

    calls = defaultdict(list)
    for row in responses:
        calls[row["judge_model"]].append(row)

    summary_fields = [
        "judge_model",
        "mae_overall",
        "within1_overall",
        "verdict_exact_match",
        "verdict_partial_credit",
        "error_rate",
        "mean_cost_cents",
        "mean_latency_s",
        "mean_token_spend",
        "within1_per_cent_second",
        "consistency",
    ]
    dimension_fields = [
        "judge_model",
        "dimension",
        "mae",
        "bias",
        "within1",
        "gold_flagged_calls",
        "judge_flagged_calls",
        "true_flags",
        "flag_precision",
        "flag_recall",
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

        # Option 1 (headline) and option 2 (diagnostic): per-dimension measures.
        all_errors = []
        for dimension in RUBRIC:
            errors = [
                int(row[dimension]) - gold_scores[row["answer_id"]][dimension]
                for row in valid
            ]
            all_errors.extend(errors)

            judge_flags = [int(row[dimension]) <= FLAG_AT_OR_BELOW for row in valid]
            gold_flags = [
                gold_scores[row["answer_id"]][dimension] <= FLAG_AT_OR_BELOW
                for row in valid
            ]
            true_flags = sum(j and g for j, g in zip(judge_flags, gold_flags))

            dimension_rows.append(
                {
                    "judge_model": model,
                    "dimension": dimension,
                    "mae": (
                        round(statistics.mean(abs(e) for e in errors), 3)
                        if errors
                        else ""
                    ),
                    "bias": round(statistics.mean(errors), 3) if errors else "",
                    "within1": percent(
                        sum(abs(e) <= TOLERANCE for e in errors), len(errors)
                    ),
                    "gold_flagged_calls": sum(gold_flags),
                    "judge_flagged_calls": sum(judge_flags),
                    "true_flags": true_flags,
                    "flag_precision": percent(true_flags, sum(judge_flags)),
                    "flag_recall": percent(true_flags, sum(gold_flags)),
                }
            )

        # Option 3 (comparison): three-level verdict.
        exact_matches = 0
        credits = []
        for row in valid:
            judged = verdict(int(row[field]) for field in RUBRIC)
            gold = gold_verdicts[row["answer_id"]]
            exact_matches += judged == gold
            credits.append(verdict_credit(judged, gold))

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

        token_spend = [
            int(row["prompt_tokens"]) + int(row["completion_tokens"])
            for row in model_calls
            if row["prompt_tokens"] and row["completion_tokens"]
        ]
        mean_cost = (
            round(mean_measure(model_calls, "cost_usd", 8) * 100, 8)
            if any(row["cost_usd"] for row in model_calls)
            else ""
        )
        mean_latency = mean_measure(model_calls, "latency_seconds", 3)
        within1_overall = percent(
            sum(abs(e) <= TOLERANCE for e in all_errors), len(all_errors)
        )
        value_for_money = (
            round(within1_overall / (mean_cost * mean_latency), 8)
            if within1_overall != ""
            and mean_cost not in ("", 0)
            and mean_latency not in ("", 0)
            else ""
        )

        summary_rows.append(
            {
                "judge_model": model,
                "mae_overall": (
                    round(statistics.mean(abs(e) for e in all_errors), 3)
                    if all_errors
                    else ""
                ),
                "within1_overall": within1_overall,
                "verdict_exact_match": percent(exact_matches, len(valid)),
                "verdict_partial_credit": percent(sum(credits), len(credits)),
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
                "mean_latency_s": mean_latency,
                "mean_token_spend": (
                    round(statistics.mean(token_spend), 2) if token_spend else ""
                ),
                "within1_per_cent_second": value_for_money,
                "consistency": (
                    round(statistics.mean(repeat_spreads), 3) if repeat_spreads else ""
                ),
            }
        )

    write_csv(SUMMARY_PATH, summary_fields, summary_rows)
    write_csv(DIMENSION_PATH, dimension_fields, dimension_rows)
    print(f"Wrote judge evaluation table to {SUMMARY_PATH}")
    print(f"Wrote per-dimension diagnostics to {DIMENSION_PATH}")

    # Baselines: what a judge scores by giving every answer the same verdict.
    print(f"Gold verdicts: {dict(Counter(gold_verdicts.values()))}")
    for constant in VERDICT_LEVEL:
        exact = sum(gold == constant for gold in gold_verdicts.values())
        credit = sum(verdict_credit(constant, gold) for gold in gold_verdicts.values())
        print(
            f"Baseline, always {constant}: exact match "
            f"{percent(exact, len(gold_verdicts))}%, partial credit "
            f"{percent(credit, len(gold_verdicts))}%"
        )


if __name__ == "__main__":
    main()
