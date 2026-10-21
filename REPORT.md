# Report: Which LLM Is the Most Reliable Judge?

Eight models judged 7 customer-support questions for a fictional company, Nimbus Cloud, three times each. Each question pertained to information from three policy documents that were provided to judges. Their 1-5 scores on accuracy, brevity, coverage and tone/clarity were compared with a gold reference, along with a derived PASS/PARTIAL/FAIL verdict. The cost, latency and error rate of each API call were also reported.

## Recommendations

- **High budget** - Claude Sonnet 5.5
- **Mid budget** - GPT-6.1 Sol
- **Low budget** - LLama 4 Maverick

## Summary

- **Claude Sonnet 5.5 was the highest quality judge** with 100% exact verdict match with the gold reference, benefiting from strict scores. It was also the most expensive (0.57 ¢/call) of the top performing judges.
- **Gemini 3.8 Flash and GPT-6.1 Sol were good all-round performers** balancing price (0.32 ¢/call and 0.24 ¢/call respectively) and quality of judgement (88.1% and 85.7% partial match respectively). GPT caught more FAILs (see FAIL detection), so could be considered better in a practical setting, where detecting FAILs is more important than PASSs.
- **Llama 4 Maverick** could be considered as a budget option (0.03 ¢/call), with its raw score agreement ranking 3rd behind Claude and Gemini. It suffered from systemic leniency which affected its verdicts (71.4% partial match and only 42.9% exact match). It was also the fastest (1.9s latency).
- **Factual accuracy was the easy dimension; style was hard.** Every judge that flagged an accuracy problem was right (100% precision), but almost every judge was too lenient on brevity and tone.
- **More compute did not buy better judgement.** The slowest and most expensive models (Mistral Large 4 and Qwen3.5 397B) used extended reasoning loops but were no more accurate than much faster models.

## Method

**Task.** Each judge received the knowledge base, a customer question pertaining to that knowledge base, a candidate answer, and a rubric, providing a guide for scoring answers (1–5) in accuracy, brevity, coverage and tone/clarity. The judges were instructed to return these scores, plus a one-sentence rationale in JSON format. The knowledge base, rubric, questions and answers are included at the bottom of this report under materials.

**Knowledge Base.** The knowledge base details 3 areas of Nimbus Cloud's policies/services; cancellation & refund, subscriptions and data retention. The model is given the document and told to use it as the only source of truth. Any claims made that are not supported in the document are to be treated as inaccurate.

**Answers.** Seven answers (A–G), each built to test a particular behaviour: an invented benefit (A), an omission plus unsupported details (B), a contradicted policy (C and E), inappropriate casual tone (D), an incomplete answer (F), and one perfect answer (G).

**Gold reference.** Human generated reference scores with explanation, stored separately from the judge prompt in `inputs/gold_reference.csv`. As the nature of the scoring is somewhat subjective, we also provide a verdict, we look at the lowest score, then < 3 : FAIL, <4 : PARTIAL, else : PASS. This aims to smooth the subjectivity of the scores and provide a metric more relevant to real-world use, where the LLM would be marking answers in a similar way.

**Runs.** 8 models × 7 answers × 3 repeats = 168 calls via OpenRouter, local validation of every score, a 20,000-token completion cap and reasoning left at each provider's default, since cost and latency are reported.

**Measures.** Headline accuracy is verdict agreement with partial credit, compared with the gold reference. This metric balances the subjectivity of raw scores with the brittleness of strict agreement, but all three accuracy metrics should be considered. Cost, latency, error rate and consistency cover practicality. Definitions are in the [README](README.md#evaluation-tables). Per-dimension bias and FAIL-detection counts provide a more detailed view of model performance.

## Results

### Overall comparison

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

Lower is better for MAE, error rate, cost, latency and consistency. Error rate is the percentage of failed outputs across all API responses. Cost and latency are averaged across all API calls. Consistency is the mean population standard deviation of each answer's overall scores across its valid repeats; lower values mean less variation between repeats.

**Reading the table**

- **MAE** is an impractical metric on its own, it punishes models equally for being too lenient and too strict. The scores are slightly subjective, and the difference between a score of 4 and 5 on brevity is harmless. MAE punishes a model that makes lots of small errors the same as one that makes a large error, which does not reflect real world use. We care much more about catching answers with major flaws than imperfections.
- **Verdict exact** is a brittle metric. A model that judges a FAIL answer as PARTIAL is punished the same as one that judges PASS, this again does not reflect real-world use, where PARTIAL predictions could be sent to a human for review. 
- **Verdict partial** is chosen as the headline metric to balance the flaws mentioned above. These flaws are depicted best by Llama 4 Maverick. It ranks 3rd in MAE, close to Claude but 8th in exact verdict match, way behind the best performers. Verdict partial is chosen as the most reflective of real-world use.
- **Best performers** Claude, Gemini and GPT form a clear leading pack, achieving a good balance across accuracy, price and latency, with a roughly equal tradeoff between price and accuracy. All three are viable options depending on preference: Claude offers higher accuracy at higher cost, GPT offers lower accuracy at lower cost, and Gemini balances both.
**Budget option.** Llama 4 Maverick could be considered a low budget option. As an open-weight model, it is >20x cheaper than Claude and ranks 3rd in MAE. Despite its poor verdicts, prompt engineering might improve its performance.
- **Consistency** does not affect the recommendation. All models had a mean standard deviation <0.2 across repeats, meaning verdict variation is rare.
- **Error rate** also does not affect the recommendation. Claude had 1/27 invalid responses due to incorrect JSON formatting, which can be prevented by enabling JSON output in the request parameters. Qwen3.5 35B-A3B had 2/27 responses truncated after hitting the 20,000-token limit, which suggests a bigger issue discussed below.
- **Mistral Large 4 and both Qwen3.5 models** took 49–166 s, with Qwen3.5 397B the most expensive at 1.6¢ per call. These models entered extended reasoning loops, which did not result in higher quality responses than faster models.

### Per-dimension diagnostics

**FAIL detection** is shown as **judge FAIL / judge PARTIAL-or-FAIL / gold FAIL calls**. For example, `0/3/3` means the judge marked a gold FAIL as PARTIAL on all 3 repeats. Invalid outputs are omitted from the table. In the candidate answers, there were 3 accuracy FAILs (nine calls); coverage and tone/clarity each have 1 FAIL (three calls).

| Judge | Accuracy | Coverage | Tone/clarity |
|---|---:|---:|---:|
| Claude Sonnet 5.5 | **9/9/9** | **3/3/3** | **3/3/3** |
| GPT-6.1 Sol | **9/9/9** | 0/3/3 | **3/3/3** |
| Gemini 3.8 Flash | **9/9/9** | 0/3/3 | 1/3/3 |
| Llama 4 Maverick | 6/9/9 | 0/3/3 | 0/3/3 |
| Mistral Large 4 | **9/9/9** | 0/3/3 | 0/3/3 |
| Qwen3.5 35B-A3B | **8/8/8** | 0/2/2 | 0/3/3 |
| Qwen3.5 397B-A17B | **9/9/9** | 0/3/3 | 0/3/3 |
| Cohere Command A+ | 6/9/9 | 0/3/3 | 0/2/3 |

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

**What the diagnostics show**

1. **Accuracy is easy to detect.** Almost every judge reliably caught inaccurate answers; only Llama and Cohere missed one answer each.
2. **Tone/clarity detection was next hardest.** Only Claude and GPT reliably caught the improper tone answer, and Gemini did so once.
3. **Coverage was the hardest.** Only Claude caught the incomplete answer.
4. **Bias shows a broader tendency toward lenient style scores.** Tone/clarity bias was positive for every judge except Claude, and coverage bias was positive for every judge except Cohere. Brevity bias was positive for six of eight judges. Accuracy bias varied: Gemini matched the gold on average, while Claude and GPT were the strictest (−0.60 and −0.57).

## Limitations

- **Reasons.** A qualitative review of the reasons attached to each response could show why certain models made mistakes. It was omitted because reviewing 168 responses would be time-consuming.
- **Small sample.** Seven answers, three repeats each (about 20–21 valid calls per model). Differences of a few points between neighbouring models are not meaningful.
- **Verdict imbalance.** There is only one PARTIAL and one PASS, so conclusions about judges' ability to detect good answers are based on limited data. This is a modest limitation because, in practical settings where answer generation is cheap, catching FAILs may matter more than missing PASSes.
- **Gold scores are subjective.** The gold reference was written by the project author. Agreement with gold is therefore partly agreement with the author's final view, especially on the subjective brevity and tone dimensions.
- **One prompt, one answer at a time.** Position and order bias were not tested, and results may change with different prompts or pairwise comparison.
- **Reasoning left at provider defaults.** Latency, token use and cost reflect each model's default reasoning behaviour, so they are not like-for-like. Models that reason more spend more tokens and time.
- **Prices and models change.** Cost figures reflect OpenRouter pricing at the time of the run.
- **Fictional domain.** Nimbus Cloud's policies are short and self-contained; real support knowledge bases are larger and messier.

## Candidate Questions & Answers

### Answer A

**Customer question:** "Do you have a referral program? If I get a friend to sign up for an annual plan, do we both get anything extra?"

**Answer:** "We don't have a formal referral program listed, but I can tell you that annual plans already come with 2 months free compared to paying monthly. As a bonus for referring friends who sign up for annual plans, we'll also add an extra free month to your account for each successful referral, on top of your existing annual discount. Just let our support team know who referred you when you sign up."

---

### Answer B

**Customer question:** "I signed up for the Team plan two days ago, but it turns out it's not right for our workflow. Can I get my money back?"

**Answer:** "Yes, absolutely. Since you're within the first 14 days of your subscription, you qualify for our new-subscriber money-back guarantee, which means a full refund with no questions asked. You can cancel from your account billing settings, and the refund will be processed against your original payment method."

---

### Answer C

**Customer question:** "I'm currently on the Team plan and want to downgrade to Starter partway through this billing cycle. Will I get a refund for the price difference?"

**Answer:** "Yes, downgrades are covered under the same protection as our money-back guarantee, so you'll receive a prorated refund for the unused portion of your current Team plan once the downgrade to Starter is processed. The refund should appear on your original payment method within a few business days."

---

### Answer D

**Customer question:** "I cancelled my subscription last week by accident. Can I get my data back?"

**Answer:** "yeah so you've basically got 30 days from when you cancelled, after that it's just gone, permanently, no way around it, so don't sit on this. easiest thing is just go reactivate the account before the 30 days runs out and everything comes back. if you wait past that window there's nothing anyone can do about it so act fast lol."

---

### Answer E

**Customer question:** "I'm an Enterprise customer and I've been with Nimbus Cloud for 3 years. If I ever cancel, can I ask for my data to be kept longer than the standard retention period?"

**Answer:** "Yes — as an Enterprise customer, you're entitled to a custom data retention period of up to 7 years, arranged through your dedicated account manager. This applies to your post-cancellation data as well, so if you ever cancel, you can work with your account manager to extend the standard retention window well beyond 30 days before anything is deleted."

---

### Answer F

**Customer question:** "My card payment failed this month — what happens now? Will you keep trying to charge me, and is my data at risk if this doesn't get sorted?"

**Answer:** "Not to worry — we understand payment issues happen. Nimbus Cloud will automatically retry your payment up to 3 times over the next 7 days, so there's a good chance it resolves itself once your card issue is fixed. If you have any other questions, feel free to reach out to our support team anytime."

---

### Answer G

**Customer question:** "I’m considering a Starter subscription with Nimbus Cloud. What are the benefits of annual billing compared with monthly billing?"

**Answer:** "Thank you for choosing Nimbus! With annual billing, you pay for 10 months and get 2 months free, saving $24 per year on the Starter plan. Annual plans are less flexible: to qualify for a refund, you must cancel within 30 days of the purchase date. You’ll receive a partial refund for the unused months, minus a 10% processing fee. With monthly billing, you can cancel at any time."

## Rubric

### Accuracy

- **1** — Includes a major claim contradicted by or not included in the source.
- **3** — Generally consistent with the source, but includes a meaningful unsupported claim, distortion, or mistaken inference.
- **5** — Factual claims are supported by the source, and its meaning is represented accurately.

### Brevity

- **1** — Includes mostly information not relevant to the question; overly verbose or wordy.
- **3** — Most information is relevant to the question, but the language is verbose or slightly wordy and could be refined.
- **5** — All information is directly relevant to the question. Language is concise and efficient.

### Coverage

- **1** — Does not attempt to answer the question or provides unrelated responses.
- **3** — Answers the main point but misses meaningful requested detail.
- **5** — Covers all requested points, whether correctly or incorrectly.

### Tone and clarity

- **1** — Inappropriate or insensitive in tone, or hard to understand.
- **3** — Mostly appropriate tone, perhaps overly formal or informal; understandable, with some ambiguity.
- **5** — Appropriate tone, not overly formal or informal, and clear and unambiguous.

## Knowledge Base

### Document 1: Refund & Cancellation Policy

New subscribers are covered by a 14-day money-back guarantee: if you cancel within 14 days of your first paid subscription, you'll receive a full refund, no questions asked. After the 14-day window, monthly plans are not eligible for any refund — cancelling simply stops future billing, and you retain access until the end of the current billing cycle.

Annual plans are treated differently. If you cancel an annual plan within 30 days of the original purchase date, you're entitled to a partial refund of the unused months, minus a 10% processing fee. Annual plan cancellations made after that 30-day window are not eligible for any refund of unused months.

Add-on purchases (such as extra storage blocks) are non-refundable under all circumstances, regardless of when they were purchased.

Downgrading your plan (e.g. moving from Team to Starter) takes effect immediately, but Nimbus Cloud does not refund the price difference for the current billing cycle. Any downgrade savings apply starting next billing cycle.

---

### Document 2: Subscription Tiers & Billing

Nimbus Cloud offers three tiers:

- **Starter** — $12/month, 1 user, 50GB storage.
- **Team** — $35/month per 5 users, 500GB storage, priority email support.
- **Enterprise** — custom pricing, unlimited storage, dedicated account manager, SSO integration.

Customers who choose annual billing instead of monthly pay for 10 months and receive 2 months free.

Billing occurs on the same calendar day each month as the original signup date. If a payment fails, Nimbus Cloud will automatically retry the charge up to 3 times over a 7-day period. If all retries fail, the account is suspended until payment is resolved.

---

### Document 3: Data Retention & Export Policy

While a subscription is active, all account data is retained indefinitely.

Upon cancellation (including suspension for non-payment that leads to cancellation), account data is kept in a recoverable state for 30 days. Reactivating the account within that window fully restores access to all data. After 30 days, data is permanently deleted and cannot be recovered under any circumstances, for any account tier.

Any customer can export their full data in CSV or JSON format at any time via Settings > Export. Export requests are processed within 24 hours.

Enterprise customers may request a custom data retention period of up to 7 years for their *active* account data, arranged directly through their dedicated account manager. This custom retention arrangement applies only while the account remains active and subscribed.
