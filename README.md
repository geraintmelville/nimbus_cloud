# Finding a Reliable LLM Judge

Which language model is the most trustworthy judge of customer-support answers? This project compares eight LLMs as judges of seven AI-written answers for **Nimbus Cloud**, a fictional company. Three short policy documents are the only ground truth, so every claim in an answer can be checked against them.

Each judge scores every answer from 1 to 5 on **accuracy**, **brevity**, **coverage** and **tone/clarity** using a rubric which is included in the prompt. A verdict is derived from the scores using the lowest score - <3: FAIL, <4 PARTIAL, else: PASS. Its scores and verdicts are compared with a hand-written gold reference. Error rate, cost, speed and consistency across repeats are also reported.

## Recommendations

- **High budget** - Claude Sonnet 5.5
- **Mid budget** - GPT-6.1 Sol
- **Low budget** - LLama 4 Maverick

**Full results and discussion: [REPORT.md](REPORT.md)**

## Headline result

| Judge | Verdict partial | Verdict exact | MAE | Error rate | Cost (¢/call) | Latency (s) | Consistency (mean SD) |
|---|---|---|---|---|---|---|---|
| Claude Sonnet 5.5 | **100.00%** | **100.00%** | 0.588 | 4.8% | 0.568 | 3.44 | 0.095 |
| Gemini 3.8 Flash | 88.1% | 76.2% | **0.560**| 0% | 0.322 | 5.99 | **0.034** |
| GPT-6.1 Sol | 85.7% | 71.43% | 0.66 | 0% | 0.243 | 7.68 | 0.095 |
| Mistral Large 4 | 81.0% | 61.9% | 0.702 | 0% | 0.831 | 72.33 | 0.193 |
| Qwen3.5 397B-A17B | 76.2% | 52.4% | 0.762 | 0% | 1.607 | 166.20 | 0.195 |
| Qwen3.5 35B-A3B | 73.7% | 47.4% | 0.763 | 9.5% | 0.514 | 49.30 | 0.067 |
| Llama 4 Maverick | 71.4% | 42.86% | 0.62 | 0% | **0.028** | **1.94** | 0.017 |
| Cohere Command A+ | 69.05% | 42.9% | 0.881 | 0% | 0.193 | 4.77 | 0.170 |

- **Claude Sonnet 5.5** was the best quality judge, but was the most expensive out of the best performers (0.57 ¢/call). It had perfect verdict agreement, benefiting from strictness.
- **GPT-6.1 Sol** was the next best, and was much cheaper than Claude (0.24 ¢/call). It was also strict, meaning despite ranking 4th in MAE, it only failed to catch the coverage FAIL, making it more useful in a practical setting.
- **Gemini 3.8 Flash** also performed well and was fairly cheap (0.32 ¢/call). While it ranked first in MAE, its leniency meant it did not reliably catch both the coverage and tone/clarity FAILs.
- - **Mistral Large 4 and both Qwen3.5 models** used extended reasoning, pushing their cost up considerably, but failed to perform as well as the above models.
- **Llama 4 Maverick** could be considered for a low budget option (0.03 ¢/call). Its verdict agreement was poor due to leniency, missing one of the accuracy FAILs, but it ranked 3rd in MAE.
- **Cohere Command A** also missed one of the accuracy FAILs, which were caught by almost all models. Its MAE was also comfortably the worst.
- This is a small case study (7 answers × 3 repeats per model), not a general ranking of models. See [Limitations](REPORT.md#limitations).

## How the evaluation works

- **Inputs** (`inputs/`): `knowledge-base.md` (the three source documents), `candidate_answers.csv` (7 question/answer pairs) and `gold_reference.csv` (answer-level reference scores and notes, kept separate from the judge prompt).
- **Judging** (`run_judges.py`): every model scores every answer 3 times through OpenRouter, giving 8 × 7 × 3 = 168 calls. Judges see only the source documents, the rubric, the question and the answer, and return JSON with four integer scores and a one-sentence rationale. Every response is validated locally. Results are checkpointed to `outputs/judge_responses.csv` after each call, so a rerun skips successful calls and retries failed ones. Each call allows up to 20,000 completion tokens and leaves reasoning at the provider default.
- **Evaluating** (`evaluate_judges.py`): compares judge scores with the gold reference and writes two tables, the metrics for each judge and the diagnostic breakdown of each judge's performance on each dimension.

### Evaluation Tables

`outputs/judge_evaluation.csv` has one row per judge:

| Column | Meaning |
|---|---|
| `verdict_partial` | Partial-credit verdict agreement with gold reference: an exact match earns full credit, a one-level miss earns half credit, and a two-level miss earns none. **Headline measure.** |
| `verdict_exact_match` | Percentage of calls whose PASS / PARTIAL / FAIL verdict matches the gold verdict. |
| `mae_overall` | Mean absolute error between judge and gold scores across all four dimensions. |
| `error_rate` | Percentage of calls without a valid parsed response (`response_status` other than `ok`). |
| `mean_cost_cents` | Mean cost per API call in US cents, including calls with invalid responses. |
| `mean_latency` | Mean seconds per API call, including calls with invalid responses. |
| `consistency` | Mean population standard deviation of each answer's overall scores across its valid repeats. Lower is more consistent. |

`outputs/judge_dimension_diagnostics.csv` has one row per judge and rubric dimension.

- `bias` is the mean of (judge score − gold score), so a positive value means the judge scores higher than the gold on average. All calculations use valid parsed calls (`parse_ok == "true"`).
- In the candidate answers there are the following FAILs: accuracy x3, coverage x1, tone/clarity x1. For these failure dimensions, the csv contains `judge_fail_calls`, `judge_partial_or_fail_calls` and `gold_fail_calls` which count, respectively, calls where both the judge and gold scored 2 or below, calls where the gold scored 2 or below and the judge scored 3 or below, and calls where the gold scored 2 or below. These are the counts shown in `REPORT.md` under FAIL detection.
- Failed calls are excluded from score and verdict agreement, bias and FAIL-detection calculations.

## Reproduce

1. Install Python 3.10+ and dependencies: `python -m pip install -r requirements.txt`.
2. Put `OPENROUTER_API_KEY=your-key` in a local `.env` file. Never commit `.env`.
3. `python run_judges.py` — runs or resumes the 168 calls. It exits nonzero while calls remain unusable; authentication, billing and invalid-request errors stop it immediately.
4. `python evaluate_judges.py` — writes the two tables above to `outputs/`.

Run both from the project directory. Check model availability and current pricing on OpenRouter before a full run, since costs in this report reflect the prices at the time of the run.

## Repository layout

```
README.md                          this file
REPORT.md                          results, analysis and limitations
run_judges.py                      OpenRouter runner with checkpointing
evaluate_judges.py                 builds the two evaluation tables
inputs/
  knowledge-base.md                Nimbus Cloud policy documents (ground truth)
  candidate_answers.csv            questions and candidate answers
  gold_reference.csv               reference verdicts, scores and notes
outputs/
  judge_responses.csv              every judge call: scores, rationale, status, tokens, cost
  judge_evaluation.csv             one row per judge
  judge_dimension_diagnostics.csv  one row per judge and dimension
```
