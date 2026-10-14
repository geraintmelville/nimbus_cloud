# Finding a Reliable LLM Judge

Which LLM is the most trustworthy judge of customer-support answers? This project compares eight LLMs as judges of seven AI-written answers for **Nimbus Cloud**, a fictional company. Three short policy documents are the only ground truth, so every claim in an answer can be checked against them.

Each judge scores every answer from 1 to 5 on **accuracy**, **brevity**, **coverage** and **tone/clarity** . Its scores are compared with a human-written gold reference, and it is also compared on error rate, cost, speed and run-to-run consistency.

**Full results and discussion: [REPORT.md](REPORT.md)**

## Headline result

| Judge | MAE vs gold (lower is better) | Scores within ±1 of gold | Verdict match | Error rate | Mean cost per call | Mean latency |
|---|---|---|---|---|---|---|
| Claude Sonnet 5.5 | **0.725** | **88.75%** | **100%** | 4.76% | 0.57¢ | 3.4 s |
| Llama 4 Maverick | 0.810 | 78.57% | 42.86% | 0% | **0.03¢** | **1.9 s** |
| GPT-6.1 Sol | 0.821 | 76.19% | 71.43% | 0% | 0.24¢ | 7.7 s |
| Gemini 3.8 Flash | 0.917 | 72.62% | 76.19% | 0% | 0.32¢ | 6.0 s |
| Mistral Large 4 | 0.940 | 71.43% | 61.90% | 0% | 0.83¢ | 72.3 s |
| Cohere Command A+ | 1.048 | 63.10% | 42.86% | 0% | 0.19¢ | 4.8 s |
| Qwen3.5 397B-A17B | 1.095 | 64.29% | 52.38% | 0% | 1.61¢ | 166.2 s |
| Qwen3.5 35B-A3B | 1.105 | 63.16% | 47.37% | 9.52% | 0.51¢ | 49.3 s |

Claude Sonnet 5.5 agreed most closely with the gold scores and reached the correct verdict on every valid call. Cheaper models were often fast and consistent but lenient on style, and the slowest, most expensive models were not more accurate. This is a small case study (7 answers × 3 repeats per model), not a general ranking of models. See [Limitations](REPORT.md#limitations).

## How the evaluation works

- **Inputs** (`inputs/`): `knowledge-base.md` (the three source documents), `candidate_answers.csv` (7 question/answer pairs) and `gold_reference.csv` (answer-level reference scores and notes, kept separate from the judge prompt).
- **Judging** (`run_judges.py`): every model scores every answer 3 times through OpenRouter, giving 8 × 7 × 3 = 168 calls. Judges see only the source documents, the question and the answer, and return JSON with four integer scores and a one-sentence rationale. Every response is validated locally. Results are checkpointed to `outputs/judge_responses.csv` after each call, so a rerun skips successful calls and retries failed ones. Each call allows up to 20,000 completion tokens and leaves reasoning at the provider default.
- **Scoring** (`evaluate_judges.py`): compares judge scores with the gold reference and writes two tables.

### Metrics

`outputs/judge_evaluation.csv` has one row per judge:

| Column | Meaning |
|---|---|
| `mae_overall` | Mean absolute error between judge and gold scores across all four dimensions. **Headline measure.** |
| `within1_overall` | Percentage of dimension scores within ±1 of gold. **Headline measure.** |
| `verdict_exact_match` | Percentage of calls whose PASS / PARTIAL / FAIL verdict matches the gold verdict. <!-- CHECK: confirm the PARTIAL cutoff in evaluate_judges.py --> |
| `verdict_partial_credit` | As above, but a one-level miss (e.g. PARTIAL vs FAIL) earns half credit. |
| `error_rate` | Percentage of calls without a valid parsed response (`response_status` other than `ok`). |
| `mean_cost_cents` | Mean cost per call in US cents. |
| `mean_latency_s` | Mean seconds per call. |
| `mean_token_spend` | Mean prompt + completion tokens per call. |
| `within1_per_cent_second` | `within1_overall ÷ (mean cost in cents × mean latency in seconds)`. A rough value-for-money figure that rewards cheap, fast models whatever their accuracy, so read it alongside the accuracy columns. |
| `consistency` | Spread of a judge's overall score across the three repeats of the same answer (mean population standard deviation across answers). Lower is more consistent. |

`outputs/judge_dimension_diagnostics.csv` has one row per judge and dimension: `mae`, `bias` (positive means more lenient than gold), `within1`, and flag counts with `flag_precision` and `flag_recall`. A call "flags" a dimension when it scores it as a problem (below 3) <!-- CHECK: confirm flag threshold in evaluate_judges.py -->; precision is the share of judge flags the gold also flags, and recall is the share of gold flags the judge caught. Precision is blank when a judge never flagged that dimension.

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
