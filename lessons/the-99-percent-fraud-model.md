---
title: The 99%-Accurate Fraud Model
skills: [imbalanced-data, metric-selection]
stages: []
---

# The 99%-Accurate Fraud Model

A fraud-detection model reported 99.1% accuracy in the sprint demo and the
team was ready to ship. The target was fraud/not-fraud, and fraud was 0.9% of
transactions. A model that predicted "not fraud" for every single transaction
would have scored 99.1% accuracy too — the reported number said nothing about
whether the model caught a single actual fraud case.

Someone finally asked for the confusion matrix instead of the headline number.
Recall on the fraud class was 3%. The model was, in practice, almost never
firing — it had learned that predicting the majority class was the easiest way
to minimize loss on a metric that rewarded exactly that.

The fix had two parts: switch the reported metric from accuracy to PR-AUC
(precision-recall, not ROC-AUC, since ROC-AUC also stays misleadingly high
under this kind of imbalance) and refit with `class_weight="balanced"` instead
of the default. PR-AUC went from an unreported 0.09 (implied by the useless
model) to 0.41 after the fix — still not great, but for the first time an
honest number the team could actually improve on.

**Lesson**: on a target this imbalanced, accuracy is not a diagnostic, it's a
trap — a model can look excellent by accuracy while catching almost nothing.
Ask for recall/precision (or PR-AUC) on the minority class before trusting any
headline accuracy number.
