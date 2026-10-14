Judge Evaluation Rubric
(This is what you use to score the 8 judges against each other. This is the actual challenge deliverable.)

Criterion	What it measures	How to test it
Consistency	Does the judge give the same verdict on the exact same input, run repeatedly?	Re-run the same judgment 3–5 times per answer, same settings, and compare
Position/order bias	If you ask it to compare two answers pairwise, does swapping which one comes first change the verdict?	Run pairwise comparisons both ways (A-then-B, then B-then-A) and check for flips
Cost & latency	Is this judge actually practical to deploy at scale?	Log tokens used and response time per judgment call
Format reliability	Does it reliably follow whatever output format you ask for (e.g. JSON scores)?	Track how often its output fails to parse or needs manual cleanup across all your runs

Reasoning quality	Is the justification specific and checkable against the source, or generic filler?	Read the judge's stated reasoning for a few answers — does it cite the actual document content?


You decide how to weight these — and you should be able to justify your weighting. A judge that's cheap and consistent but easily fooled by confident wrong answers is not a good judge, no matter how fast or affordable it is. A judge that's excellent at spotting problems but incredibly slow and expensive might also be the wrong practical choice — that's your call to make and defend.