Challenge: Find the Best Judge
The task
You're given three source documents describing the policies of a fictional company, Nimbus Cloud, and six real customer questions with an AI-generated answer to each. Your job is not to evaluate the answers yourself. Your job is to find out which of 8 different LLMs, used as an automated judge, is best at evaluating those answers accurately — and to prove it.

Companies increasingly use one LLM to grade the outputs of another (e.g. checking customer-support answers for accuracy before they go out, or grading answers at scale where a human can't review everything). But not all models are equally good at judging — some are lenient, some are inconsistent, some get swayed by confident tone over actual accuracy. Your challenge is to find out which one you'd actually trust for this job, and why.

What you're given
`inputs/knowledge-base.md` — the three source documents. This is the only source of truth. Nothing outside these documents should be treated as correct, no matter how plausible it sounds.
2-candidate-answers.md — six customer questions, each with one AI-generated answer (labelled A–F). These are the artifacts your judges will evaluate. `run_judges.py` reads the matching rows from `inputs/candidate_answers.csv`.
You do not know in advance which of the six answers are fully correct and which contain errors. That's for your judges to figure out — and for you to check.

What you need to do
Pick 8 models via OpenRouter to act as judges. Try to get some diversity (different labs, different sizes/price points) — a lineup of 8 near-identical models won't teach you much.
Design a judge prompt. You decide the method: rubric-based scoring (see below), pairwise comparison, binary faithful/not-faithful classification, or a combination. Document your prompt design and reasoning.
Run all 8 judges against all 6 answers, using the Candidate Response Rubric as the scoring framework you ask each judge to apply.
Evaluate the judges themselves using the Judge Evaluation Rubric — this is the real deliverable. You're not just collecting 8 sets of scores, you're determining which judge is most trustworthy.
Make a recommendation: if Nimbus Cloud had to deploy exactly one of these 8 models as an automated answer-checker, which would you pick, and why? Back this with evidence from at least 3 of the criteria in the Judge Evaluation Rubric — "it agreed with the majority" is not sufficient justification on its own.