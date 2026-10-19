# Finding a Reliable LLM Judge

Which language model is the most trustworthy judge of customer-support answers? This project compares eight LLMs as judges of seven AI-written answers for **Nimbus Cloud**, a fictional company. Three short policy documents are the only ground truth, so every claim in an answer can be checked against them.

Each judge scores every answer from 1 to 5 on **accuracy**, **brevity**, **coverage** and **tone/clarity**. Its scores are compared with a hand-written gold reference, and it is also compared on error rate, cost, speed and run-to-run consistency.

**Full results and discussion: [REPORT.md](REPORT.md)**

## Headline result

| Judge | MAE vs gold (lower is better) | Verdict exact match | Verdict partial credit | Error rate | Mean cost per call | Mean latency | Consistency |
|---|---|---|---|---|---|---|---|
| Gemini 3.8 Flash | **0.560** | 76.19% | 88.10% | 0% | 0.32¢ | 6.0 s | 0.034 |
| Claude Sonnet 5.5 | 0.588 | **100%** | **100%** | 4.76% | 0.57¢ | 3.4 s | 0.095 |
| Llama 4 Maverick | 0.619 | 42.86% | 71.43% | 0% | 0.03¢ | 1.9 s | 0.017 |
| GPT-6.1 Sol | 0.655 | 71.43% | 85.71% | 0% | 0.24¢ | 7.7 s | 0.095 |
| Mistral Large 4 | 0.702 | 61.90% | 80.95% | 0% | 0.83¢ | 72.3 s | 0.193 |
| Qwen3.5 397B-A17B | 0.762 | 52.38% | 76.19% | 0% | 1.61¢ | 166.2 s | 0.195 |
| Qwen3.5 35B-A3B | 0.763 | 47.37% | 73.68% | 9.52% | 0.51¢ | 49.3 s | 0.067 |
| Cohere Command A+ | 0.881 | 42.86% | 69.05% | 0% | 0.19¢ | 4.8 s | 0.170 |

Gemini 3.8 Flash had the lowest overall MAE against the gold rubric, while Claude Sonnet 5.5 achieved the strongest verdict agreement on valid calls (100% exact, 100% partial). Cheaper models were often fast and consistent but lenient on style, and the slowest, most expensive models were not more accurate. This is a small case study (7 answers × 3 repeats per model), not a general ranking of models. See [Limitations](REPORT.md#limitations).

## How the evaluation works

- **Inputs** (`inputs/`): `knowledge-base.md` (the three source documents), `candidate_answers.csv` (7 question/answer pairs) and `gold_reference.csv` (answer-level reference scores and notes, kept separate from the judge prompt).
- **Judging** (`run_judges.py`): every model scores every answer 3 times through OpenRouter, giving 8 × 7 × 3 = 168 calls. Judges see only the source documents, the question and the answer, and return JSON with four integer scores and a one-sentence rationale. Every response is validated locally. Results are checkpointed to `outputs/judge_responses.csv` after each call, so a rerun skips successful calls and retries failed ones. Each call allows up to 20,000 completion tokens and leaves reasoning at the provider default.
- **Scoring** (`evaluate_judges.py`): compares judge scores with the gold reference and writes two tables.

### Metrics

`outputs/judge_evaluation.csv` has one row per judge:

| Column | Meaning |
|---|---|
| `mae_overall` | Mean absolute error between judge and gold scores across all four dimensions. **Headline measure.** |
| `verdict_exact_match` | Percentage of calls whose PASS / PARTIAL / FAIL verdict matches the gold verdict. |
| `verdict_partial` | Partial-credit verdict agreement: an exact match earns full credit, a one-level miss earns half credit, and a two-level miss earns none. |
| `error_rate` | Percentage of calls without a valid parsed response (`response_status` other than `ok`). |
| `mean_cost_cents` | Mean cost per call in US cents. |
| `mean_latency` | Mean seconds per call. |
| `consistency` | Spread of a judge's overall score across the three repeats of the same answer (mean population standard deviation across answers). Lower is more consistent. |

`outputs/judge_dimension_diagnostics.csv` has one row per judge and dimension: `mae`, `bias` (positive means more lenient than gold), and flag counts with `flag_precision`. A call "flags" a dimension when it scores it as a problem (2 or below); precision is the share of judge flags the gold also flags. Precision is blank when a judge never flagged that dimension.

Failed calls are excluded from the accuracy-style metrics but counted in `error_rate`.

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
