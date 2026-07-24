# without_skill run (reproducible naive baseline)

Real output of [`naive_run.py`](naive_run.py) in this directory (sklearn 1.8.0). A
scripted stand-in for a common un-disciplined approach — **not** an observed
LLM-without-skill agent, but its numbers are real and reproducible.

```
$ python naive_run.py
Accuracy: 0.9995
ROC-AUC : 0.9440
Conclusion: "The model is 99.9% accurate with a 0.94 ROC-AUC - it performs
excellently at detecting fraud and looks ready to ship."
```

No baseline, no PR-AUC, no operating threshold, no stratified split — which is exactly
what the grading marks it down for.
