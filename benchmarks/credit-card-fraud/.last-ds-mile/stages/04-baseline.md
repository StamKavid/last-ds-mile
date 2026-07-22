# Stage 4 — Honest Baseline

## Baseline definition

Majority-class / no-skill classifier: predict `Class=0` (genuine) for every
transaction, or equivalently, a classifier with zero discriminative ability.

## Score, using the exact metric from `/ds-frame`

A no-skill classifier's **PR-AUC equals the base rate** — a well-known identity, not
approximated: with 0.167% fraud, **baseline PR-AUC = 0.00167**. Its ROC-AUC is
exactly **0.5** by construction (random ranking).

**This is the sharpest possible illustration of `ds-method`'s Red Flag "model
accuracy matches the majority-class rate to 2 decimal places"**: the majority-class
baseline's *accuracy* would be 99.83% — a number that sounds like a near-perfect
model and is actually the *worst possible* classifier for this problem. Reporting
accuracy at all for this dataset would be actively misleading; it isn't reported
anywhere in this run's stages for exactly that reason.

## What "beating it" means

Any real candidate must clear PR-AUC meaningfully above 0.00167 by more than fold
noise — a PR-AUC of even 0.05 would already be a ~30x lift over this baseline, so the
bar here is about ranking real candidates against each other and against fold noise,
not about squeezing lift out of an already-trivial anchor.
