# Judge Evaluation Plan

This plan applies the criteria in [`Judge Evaluation Rubric.md`](Judge%20Evaluation%20Rubric.md) to the single-answer, rubric-scoring experiment in `run_judges.py`. Run `python analyze_judges.py` to write one comparison table to `outputs/evaluation/judge_evaluation.csv`.

## Reference data

[`gold_reference.csv`](../inputs/gold_reference.csv) contains answer-level reference verdicts and scores using the same rubric fields as the judge responses: accuracy, brevity, coverage, and tone clarity. The three supplied Nimbus Cloud documents are the only ground truth. Keep the reference file out of the judge prompt.

Use the same explicit verdict rule for reference labels and judge outcomes: PASS when all three dimension scores are 4 or 5; FAIL when any dimension is 1 or 2; PARTIAL otherwise. This keeps a strong tone or broad coverage from compensating for a major source error. Apply the rule before examining model results.

The RMSE columns in the output use the rubric field names: `rmse_accuracy`, `rmse_brevity`, `rmse_coverage`, and `rmse_tone_clarity`.

## Criteria and measures

| Judge Evaluation Rubric criterion | Measure for this experiment | Interpretation / limitation |
|---|---|---|
| Accuracy | RMSE of answer-level mean scores against the reference for all four rubric dimensions; total RMSE pools errors across those dimensions. | Repeats are averaged for each answer before calculating RMSE; unparsed responses are excluded from score-based measures. |
| Discrimination | Population standard deviation of each judge's answer-level mean across the three rubric dimensions. | Higher spread means less clustering; it does not show whether score differences are correct. |
| Consistency | Mean population standard deviation across the three repeated composite scores for each answer. Each composite is the mean of the three rubric dimensions. | Lower spread means more repeatable scores. The seven answers, not the repeats, are the evaluation cases. |
| Position/order bias | Mark **not tested / not applicable** for this single-answer scoring design. | The current experiment never presents two answers in an ordered pair. To test this criterion, add a separate pairwise experiment and repeat each pair with positions reversed. Do not present single-answer results as evidence of no order bias. |
| Verbosity/style bias | Compare faithfulness and correctness scores with the reference on fluent but incorrect answers A, C, and E; compare with accurate but poorly toned D and polite but incomplete F. Audit the associated rationales for style-driven praise. | This is a qualitative diagnostic on six naturally different answers, not a causal test. A stronger follow-up would compare manually checked, meaning-preserving style variants of the same answer. |
| Reasoning quality | Human-audit explanations for source specificity, factual correctness, whether they catch the material contradiction/omission, and whether they invent evidence. Score each dimension 0 (absent/wrong), 1 (partial), or 2 (specific and correct), and retain examples. | Do not use keyword overlap or explanation length as a substitute for evidence quality. Record the audit rubric and reviewer. |
| Format reliability | Report parse success (`parse_ok`) and HTTP/request failures separately. A parse is successful only when all five criterion scores, overall score, and reasoning are present in the requested format. | Parse failures and API failures have different causes and should not be combined. |
| Cost & latency | Mean `cost_usd`, `latency_seconds`, and combined prompt plus completion tokens per judgment, where recorded. | The runner requests OpenRouter's per-response usage cost and records the model returned by the API. Missing measurements are left blank. |

## Recommendation

Show the criteria separately. Give accuracy against the reference and false-pass behavior priority for an automated answer checker, then discuss consistency, audited evidence quality, format reliability, and cost/latency. The current run uses provider-default reasoning and a 4,000-token cap. Re-run any calls that previously exhausted or were stopped by the old cap; a cap increase does not affect calls that completed naturally below it. If a composite score is used, publish the weights and a sensitivity check; do not let a low price or high score spread compensate for incorrect policy judgments without justification.

The reference set has seven answers, including a fully supported 5/5/5 PASS example. Treat every ranking as a small case study, not a general claim about model quality.
