---
title: The Time-Traveling Feature
skills: [target-leakage-detection]
stages: [ds-prep]
---

# The Time-Traveling Feature

A churn model kept scoring an implausible AUC of 0.99 in every experiment, no
matter what algorithm the team tried. The culprit was a single engineered
feature: `days_since_last_purchase`, computed once as an aggregate over the
*entire* dataset's date range — every row's value included information from
purchases that happened after the row's own prediction date.

At training time, that meant the model was effectively being told "this
customer bought again soon" for the exact customers who churned around the
same window the feature aggregated over. The offline metric looked
spectacular. In production, where "days since last purchase" can only ever
look backward from *right now*, the same feature produced garbage, and the
model's real-world recall on churners was barely above a coin flip.

The fix was mechanical once the leak was named: recompute the aggregate as an
as-of-date, expanding-window statistic — using only purchase history available
strictly before each row's own timestamp — and re-run the full pipeline. AUC
dropped from 0.99 to 0.81. The team treated that drop as the actual finding,
not a regression: 0.81 was the first honest number the project had produced.

**Lesson**: any full-dataset aggregate feature is a leakage candidate until
proven otherwise — recompute it as an as-of statistic and diff against the
original. If the numbers differ, the original was time-traveling.
