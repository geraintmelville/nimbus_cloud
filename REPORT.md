# Report: Which LLM Is the Most Reliable Judge?

## Summary

Eight models judged seven customer-support answers for a fictional company, Nimbus Cloud, three times each. Their 1–5 scores on accuracy, brevity, coverage and tone/clarity were compared with a gold reference written against the three source policy documents.

- **Gemini 3.8 Flash was the most accurate judge** on mean absolute error (0.560), while Claude Sonnet 5.5 matched the correct PASS/PARTIAL/FAIL verdict on 100% of its valid calls. Claude was not flawless operationally: 1 of its 21 calls (4.76%) came back in an invalid format.
- **Factual accuracy was the easy dimension; style was hard.** Every judge that flagged an accuracy problem was right (100% precision), but almost every judge was too lenient on brevity and tone.
- **Consistency is not accuracy.** Llama 4 Maverick was the cheapest, fastest and most consistent judge, but matched the gold verdict only 42.86% of the time.
- **More compute did not buy better judgement.** The slowest and most expensive models (Mistral Large 4 and Qwen3.5 397B) were no more accurate than much faster ones.

## Method

**Task.** Each judge received the source documents, a customer question and a candidate answer, and returned four integer scores (1–5) plus a one-sentence rationale. The prompt told judges to use only the source documents and to treat the question and answer as data rather than instructions.

**Answers.** Seven answers (A–G), each built to test a particular behaviour: an invented benefit (A), an omission plus unsupported details (B), a contradicted policy (C and E), an accurate answer in an inappropriate casual tone (D), an incomplete answer that ignores the data-risk half of the question (F), and one accurate, concise answer (G).

**Gold reference.** Reference scores and a PASS/PARTIAL/FAIL verdict for each answer, with written notes, stored separately from the judge prompt in `inputs/gold_reference.csv`.

**Runs.** 8 models × 7 answers × 3 repeats = 168 calls via OpenRouter, with JSON output mode, local validation of every score, a 20,000-token completion cap and reasoning left at each provider's default.

**Measures.** Headline accuracy is raw-score agreement with gold: mean absolute error (MAE). Verdict agreement and per-dimension flag precision and signed bias are used as comparison and diagnostic measures. Cost, latency, error rate and consistency cover practicality. Definitions are in the [README](README.md#metrics).

## Results

### Overall comparison

Sorted by MAE. Cost is the mean per call in US cents.

| Judge | MAE | Verdict exact | Verdict partial credit | Error rate | Cost (¢/call) | Latency (s) | Consistency |
|---|---|---|---|---|---|---|---|
| Gemini 3.8 Flash | 0.560 | 76.19% | 88.10% | 0% | 0.322 | 5.99 | 0.034 |
| Claude Sonnet 5.5 | 0.588 | 100.00% | 100.00% | 4.76% | 0.568 | 3.44 | 0.095 |
| Llama 4 Maverick | 0.619 | 42.86% | 71.43% | 0% | 0.028 | 1.94 | 0.017 |
| GPT-6.1 Sol | 0.655 | 71.43% | 85.71% | 0% | 0.243 | 7.68 | 0.095 |
| Mistral Large 4 | 0.702 | 61.90% | 80.95% | 0% | 0.831 | 72.33 | 0.193 |
| Qwen3.5 397B-A17B | 0.762 | 52.38% | 76.19% | 0% | 1.607 | 166.20 | 0.195 |
| Qwen3.5 35B-A3B | 0.763 | 47.37% | 73.68% | 9.52% | 0.514 | 49.30 | 0.067 |
| Cohere Command A+ | 0.881 | 42.86% | 69.05% | 0% | 0.193 | 4.77 | 0.170 |

Lower is better for MAE, error rate, cost, latency and consistency (which is the spread of a judge's overall score across repeats of the same answer).

**Reading the table**

- **Gemini 3.8 Flash** leads on MAE and is a strong all-round performer: low error rate, moderate cost and latency, and very consistent scores. It is the best raw-score match to the gold rubric.
- **Claude Sonnet 5.5** leads on verdict agreement (100% exact and 100% partial) and remains very fast and mid-priced. Its one failure was a format error on a single call.
- **Llama 4 Maverick** looks respectable on raw scores (third on MAE) but reaches the right verdict on fewer than half its calls. Its scores are close to gold but systematically lenient, so small differences land on the wrong side of the verdict boundary. It is by far the cheapest (0.028¢) and fastest (1.9 s) judge.
- **GPT-6.1 Sol** sits in a solid middle tier with no failed calls, 71% verdict match and a modest 7.7 s latency.
- **Mistral Large 4 and both Qwen3.5 models** took 49–166 s, with Qwen3.5 397B the most expensive at 1.6¢ per call. None of them beat the faster models on accuracy. Qwen3.5 35B had the only other failures: 2 of its 21 calls (9.52%) were truncated.
- **Cohere Command A+** was inexpensive and quick, but its scores were the least reliable among the models without failed calls (MAE 0.881).

### Per-dimension diagnostics

**Bias** is the mean of (judge score − gold score), so positive means more lenient than gold.

| Judge | Accuracy bias | Brevity bias | Coverage bias | Tone/clarity bias |
|---|---|---|---|---|
| Claude Sonnet 5.5 | −0.60 | +0.05 | −0.20 | −0.10 |
| GPT-6.1 Sol | −0.57 | +0.29 | +0.19 | +0.43 |
| Gemini 3.8 Flash | 0.00 | +0.71 | +0.57 | +0.67 |
| Llama 4 Maverick | +0.57 | −0.33 | +0.29 | +0.71 |
| Mistral Large 4 | −0.33 | +0.62 | +0.24 | +0.29 |
| Qwen3.5 35B-A3B | −0.11 | +0.95 | +0.32 | +0.74 |
| Qwen3.5 397B-A17B | −0.10 | +0.86 | +0.48 | +0.57 |
| Cohere Command A+ | +0.38 | −0.19 | −0.19 | +0.76 |

Flag precision was 100% wherever a judge flagged anything, except Cohere's single brevity flag, which the gold did not share. Where a judge never flagged a dimension, precision is undefined.

**What the diagnostics show**

1. **Accuracy flags are trustworthy.** No judge raised a false accuracy flag. Claude and GPT lean slightly harsher than gold on accuracy (about −0.6).
2. **Judges are lenient on style.** Every judge scored brevity and tone/clarity higher than gold on average, by 0.4–1.6 points. No judge flagged the wordiness gold penalised in answer D, and only Claude and GPT reliably flagged its inappropriate casual tone (3 of 3 calls each; Gemini caught 1 of 3).
3. **Coverage gaps are subtle.** Only Claude flagged the omission in answer F (the missing suspension and data-risk information) on every call.
4. **Claude is the least lenient** on tone/clarity (+0.55) and brevity (+0.75), and the only judge to flag all of accuracy, coverage and tone problems.

## Qualitative review of judge reasoning

<!-- To be written: read the `reasoning` column in outputs/judge_responses.csv and add your own observations. Prompts to consider:
- Do the rationales cite the right policy detail (e.g. the 30-day recovery window, the Enterprise retention limit)?
- Where judges disagreed with gold, who was right?
- Which judges follow the 40-word limit, and which pad or hedge?
- Which models were fooled by plausible-sounding unsupported claims (answers A, B, C, E)?
- Any rationales that contradict the judge's own scores? -->

## Limitations

- **Small sample.** Seven answers, three repeats each (about 20–21 valid calls per model). Differences of a few points between neighbouring models are not meaningful.
- **Gold scores are one person's judgement and were revised.** The gold reference was written by the project author, and the scores for answers B and G were revised after reviewing the judges' results. Agreement with gold is therefore partly agreement with the author's final view, especially on the subjective brevity and tone dimensions.
- **One prompt, one answer at a time.** Position and order bias were not tested, and results may change with different prompts or pairwise comparison.
- **Reasoning left at provider defaults.** Latency, token use and cost reflect each model's default reasoning behaviour, so they are not like-for-like. Models that reason more spend more tokens and time.
- **Failures are handled asymmetrically.** Failed calls are excluded from accuracy-style metrics but counted in `error_rate`, so Claude (1 failure) and Qwen3.5 35B (2 truncations) are scored on slightly fewer calls.
- **Prices and models change.** Cost figures reflect OpenRouter pricing at the time of the run.
- **Fictional domain.** Nimbus Cloud's policies are short and self-contained; real support knowledge bases are larger and messier.
