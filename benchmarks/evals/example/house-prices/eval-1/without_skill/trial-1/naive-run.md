# without_skill run (reproducible naive baseline)

Real output of [`naive_run.py`](naive_run.py) in this directory (sklearn 1.8.0). A
scripted stand-in for a common un-disciplined approach — **not** an observed
LLM-without-skill agent, but its numbers are real and reproducible.

```
$ python naive_run.py
RMSE: $11,058
R^2 : 0.9806
Conclusion: "The model predicts sale price within about $11,058 with an
R-squared of 0.98 - very accurate."
```

RMSE and R^2 are computed on the same rows the model trained on (in-sample), in raw
dollars on a target spanning orders of magnitude, with no baseline — which is exactly
what the grading marks it down for.
