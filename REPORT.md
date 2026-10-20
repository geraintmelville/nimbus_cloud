# Report: Which LLM Is the Most Reliable Judge?

## Summary

Eight models judged 7 customer-support questions for a fictional company, Nimbus Cloud, three times each. Each question pertained to information from three policy documents that were provided to judges. Their 1-5 scores on accuracy, brevity, coverage and tone/clarity were compared with a gold reference, along with a derived PASS/PARTIAL/FAIL verdict. The cost, latency and error rate of each API call were also reported.

- **Claude Sonnet 5.5 was the highest quality judge** with 100% exact verdict match with the gold reference, benefiting from strict scores. It was also the most expensive (0.57¢ per response) of the top performing judges. Gemini 3.8 Flash actually had better raw score agreement, but its leniency affected its verdicts, (76.2% exact).
**Gemini 3.8 Flash and GPT-6.1 Sol were good all-round performers** balancing price (¢0.32 and ¢0.24 respectively) and quality of judgement (88.1% and 85.7% partial match respectively), along with Claude, they form a clear group of winners with final recommendation depending on the user's price/accuracy preference (GPT/Gemini/Claude respectively).
**Llama 4 Maverick** was the best budget option (¢0.03 per call), with its raw score agreement ranking 3rd behind Claude and Gemini. It suffered from systemic leniency which affected its verdicts (71.4% partial match and only 42.9% exact match). It was also the fastest (1.9s latency).
- **Factual accuracy was the easy dimension; style was hard.** Every judge that flagged an accuracy problem was right (100% precision), but almost every judge was too lenient on brevity and tone.
- **More compute did not buy better judgement.** The slowest and most expensive models (Mistral Large 4 and Qwen3.5 397B) used extended reasoning loops but were no more accurate than much faster models.

## Method

**Task.** Each judge received the knowledge base, a customer question pertaining to that knowledge base, a candidate answer, and a rubric, providing a guide for scoring answers (1–5) in accuracy, brevity, coverage and tone/clarity. The judges were instructed to return these scores, plus a one-sentence rationale in json format. The knowledge base, rubric, questions and answers are included at the bottom of this report under materials.

**Knowledge Base** The knowledge base details 3 areas of Nimbus Cloud's policies/services; cancellation & refund, subscriptions and data retention. The document is inserted into each prompt, which instructs the model to use it as the only source of truth, where any claims made that are not supported in the document are to be treated as inaccurate.

**Answers.** Seven answers (A–G), each built to test a particular behaviour: an invented benefit (A), an omission plus unsupported details (B), a contradicted policy (C and E), inappropriate casual tone (D), an incomplete answer (F), and one perfect answer (G).

**Gold reference.** Human generated reference scores with explanation, stored separately from the judge prompt in `inputs/gold_reference.csv`. As the nature of the scoring is somewhat subjective, we also provide a verdict, we look at the lowest score, then < 3 : FAIL, <4 : PARTIAL, else : PASS. This aims to smooth the subjectivity of the scores and provide a metric more relevant to real-world use, where the LLM would be marking answers in a similar way.

**Runs.** 8 models × 7 answers × 3 repeats = 168 calls via OpenRouter, local validation of every score, a 20,000-token completion cap and reasoning left at each provider's default, since cost and latency are reported.

**Measures.** Headline accuracy is verdict agreement with partial credit, compared with gold reference. This metric is chosen as it balances the subjectivity of the raw scores, with the brittleness of strict agreement, but all 3 accuracy metrics should be taken in to account. Cost, latency, error rate and consistency cover practicality. Definitions are in the [README](README.md#metrics). The per-dimension model bias is reported as a diagnostic for a more detailed view of model scores compared with the gold reference.

## Results

### Overall comparison

| Judge | Verdict partial | Verdict exact | MAE | Error rate | Cost (¢/call) | Latency (s) | Variance |
|---|---|---|---|---|---|---|---|
| Claude Sonnet 5.5 | **100.00%** | **100.00%** | 0.588 | 4.8% | 0.568 | 3.44 | 0.095 |
| Gemini 3.8 Flash | 88.1% | 76.2% | **0.560**| 0% | 0.322 | 5.99 | **0.034** |
| GPT-6.1 Sol | 85.7% | 71.43% | 0.66 | 0% | 0.243 | 7.68 | 0.095 |
| Mistral Large 4 | 81.0% | 61.9% | 0.702 | 0% | 0.831 | 72.33 | 0.193 |
| Qwen3.5 397B-A17B | 76.2% | 52.4% | 0.762 | 0% | 1.607 | 166.20 | 0.195 |
| Qwen3.5 35B-A3B | 73.7% | 47.4% | 0.763 | 9.5% | 0.514 | 49.30 | 0.067 |
| Llama 4 Maverick | 71.4% | 42.86% | 0.62 | 0% | **0.028** | **1.94** | 0.017 |
| Cohere Command A+ | 69.05% | 42.9% | 0.881 | 0% | 0.193 | 4.77 | 0.170 |

Lower is better for MAE, Error rate, cost, latency and variance. Error rate is the % failed outputs across all API responses. Cost and latency are averaged over all valid responses. Variance is the average variance per answer e.g. how much a judge scores the same answer differently across repeats.

**Reading the table**

- **MAE** is an impractical metric on its own, it punishes models equally for being too lenient and too strict. The scores are slightly subjective, the difference between a score of 4 and 5 on brevity is harmless. MAE punishes a model that makes lots of small errors the same as one that makes a large error, which does not reflect real world use. We care much more about catching answers with major flaws than imperfections.
- **Verdict exact** is a brittle metric. A model that judges a FAIL answer as PARTIAL is punished the same as one that judges PASS, this again does not reflect real-world use, where PARTIAL predictions could be sent to human for review. 
- **Verdict partial** is chosen as the headline metric to balance the flaws mentioned above. These flaws are depicted best by LLama 4 Maverick. It ranks 3rd in MAE, close to Claude but 8th in exact verdict match, way behind the best performers. Verdict partial is chosen as the most reflective of real-world use.
- **Best performers** Claude, Gemini and GPT form a clear leading pack, achieving a good balance across accuracy, price and latency, with a roughly equal tradeoff between price and accuracy. This means all 3 are viable options for recommendation, depending on ones preferences, Claude - higher accuracy/higher cost, GPT - lower accuracy/lower cost, Gemini - balances both.
**Budget option** LLama 4 Maverick could be considered as an ultra low budget option. As an open weight model, it is >20x cheaper than Claude and ranks 1st in latency. Despite its poor verdicts, it has good raw score agreement, so perhaps with some prompt engineering, its verdicts could be improved to make it viable.
- **Consistency** does not affect recommendation. All models had a mean variance of <0.2 across repeats, meaning verdict disagreement across repeats are very rare.
- **Error rate** also does not affect recommendation. Claude had 1/27 due to incorrect json formatting, which can be easily fixed by switching on json output in the request parameters. Qwen3.5 35B-A3B had 2/27 responses truncated due to hitting the 20,000 token limit, which is indicative of a deeper issue discussed below.
- **Mistral Large 4 and both Qwen3.5 models** took 49–166 s, with Qwen3.5 397B the most expensive at 1.6¢ per call. This suggest the model's entered into extended reasoning loops, which did not result in higher quality responses compared with faster models.

### Per-dimension diagnostics

**Bias** is the mean of (judge score − gold score), so positive means more lenient than gold.

| Judge | Accuracy bias | Brevity bias | Coverage bias | Tone/clarity bias |
|---|---|---|---|---|
| Claude Sonnet 5.5 | −0.60 | **+0.05** | −0.20 | **−0.10** |
| GPT-6.1 Sol | −0.57 | +0.29 | **+0.19** | +0.43 |
| Gemini 3.8 Flash | **0.00** | +0.71 | +0.57 | +0.67 |
| Llama 4 Maverick | +0.57 | −0.33 | +0.29 | +0.71 |
| Mistral Large 4 | −0.33 | +0.62 | +0.24 | +0.29 |
| Qwen3.5 35B-A3B | −0.11 | +0.95 | +0.32 | +0.74 |
| Qwen3.5 397B-A17B | −0.10 | +0.86 | +0.48 | +0.57 |
| Cohere Command A+ | +0.38 | −0.19 | **−0.19** | +0.76 |

**Gold FAIL detection** is shown as **judge FAIL / judge PARTIAL-or-FAIL / gold FAIL calls**. For example, `0/3/3` means the judge marked none of the three gold FAIL calls as FAIL, and none as PARTIAL or FAIL. Invalid outputs count in the final number but not the first two. Accuracy has three gold FAIL answers (nine calls); coverage and tone/clarity each have one (three calls).

| Judge | Accuracy | Coverage | Tone/clarity |
|---|---:|---:|---:|
| Claude Sonnet 5.5 | **9/9/9** | **3/3/3** | **3/3/3** |
| GPT-6.1 Sol | **9/9/9** | 0/3/3 | **3/3/3** |
| Gemini 3.8 Flash | **9/9/9** | 0/3/3 | 1/3/3 |
| Llama 4 Maverick | 6/9/9 | 0/3/3 | 0/3/3 |
| Mistral Large 4 | **9/9/9** | 0/3/3 | 0/3/3 |
| Qwen3.5 35B-A3B | 8/8/9 | 0/2/3 | 0/3/3 |
| Qwen3.5 397B-A17B | **9/9/9** | 0/3/3 | 0/3/3 |
| Cohere Command A+ | 6/9/9 | 0/3/3 | 0/2/3 |

**What the diagnostics show**

1. **Accuracy flags were precise, but strict detection varied.** Every judge's accuracy flags matched the gold reference. Five judges marked all nine gold FAIL calls as FAIL; Qwen3.5 35B marked eight, while Llama and Cohere marked six. Llama and Cohere marked the remaining calls PARTIAL, so their PARTIAL-or-FAIL counts were still 9/9.
2. **Coverage was rarely caught.** Claude marked the coverage FAIL as FAIL on all three repeats. The other judges did not mark it even PARTIAL; Qwen3.5 35B had two valid calls and one invalid output.
3. **Tone/clarity detection was mixed.** Claude and GPT marked the gold FAIL as FAIL on all three repeats, and Gemini did so once. The remaining judges did not mark it PARTIAL or FAIL; Cohere had one invalid output.
4. **Bias shows a broader tendency toward lenient style scores.** Tone/clarity bias was positive for every judge except Claude, and coverage bias was positive for every judge except Cohere. Brevity bias was positive for six of eight judges. Accuracy bias varied: Gemini matched the gold on average, while Claude and GPT were the strictest (−0.60 and −0.57).

## Qualitative review of judge reasoning

<!-- To be written: read the `reasoning` column in outputs/judge_responses.csv and add your own observations. Prompts to consider:
- Do the rationales cite the right policy detail (e.g. the 30-day recovery window, the Enterprise retention limit)?
- Where judges disagreed with gold, who was right?
- Which judges follow the 40-word limit, and which pad or hedge?
- Which models were fooled by plausible-sounding unsupported claims (answers A, B, C, E)?
- Any rationales that contradict the judge's own scores? -->

## Limitations

- **Small sample.** Seven answers, three repeats each (about 20–21 valid calls per model). Differences of a few points between neighbouring models are not meaningful.
- **Verdict Imbalance** There is only 1 PARTIAL and 1 PASS, 
- **Gold scores are subjective.** The gold reference was written by the project author. Agreement with gold is therefore partly agreement with the author's final view, especially on the subjective brevity and tone dimensions.
- **One prompt, one answer at a time.** Position and order bias were not tested, and results may change with different prompts or pairwise comparison.
- **Reasoning left at provider defaults.** Latency, token use and cost reflect each model's default reasoning behaviour, so they are not like-for-like. Models that reason more spend more tokens and time.
- **Prices and models change.** Cost figures reflect OpenRouter pricing at the time of the run.
- **Fictional domain.** Nimbus Cloud's policies are short and self-contained; real support knowledge bases are larger and messier.
