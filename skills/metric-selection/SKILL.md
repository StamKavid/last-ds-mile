---
name: metric-selection
description: Chooses an evaluation metric matched to the decision and the target's class balance or distribution shape. Use when picking or defending a metric for classification, regression, ranking, or probabilistic predictions, or when a metric choice seems arbitrary or disconnected from the actual decision.
---

# metric-selection

## Overview

The metric is not a technical afterthought — it's the operational definition of
"good," and the wrong one can make an actively harmful model look great. This skill
is a decision table, not a philosophy essay.

## When to Use

- Picking the metric during `/ds-frame`, or defending/re-checking it during
  `/ds-evaluate`.
- The target is imbalanced (classification) or skewed (regression) and accuracy/plain
  RMSE feels wrong.
- NOT for: picking the validation split (see `validation-strategy`) — this skill is
  about how a prediction is scored, not how data is split for scoring.

## Core Process

1. Start from the decision this feeds (from `/ds-frame`) — what does a false
   positive cost vs. a false negative? What does a $10,000 prediction error cost vs.
   a $1,000 one?
2. Match the problem type + cost asymmetry to a metric family in the table below.
3. State explicitly why the chosen metric fits the decision — "we use F2 because
   missing a fraud case costs 5x more than a false alarm," not "F1 is standard."

## Techniques/Patterns — metric decision table

| Problem type | Situation | Metric | Why |
|---|---|---|---|
| Binary classification | Balanced classes, symmetric cost | Accuracy, ROC-AUC | Both classes matter equally, straightforward to interpret |
| Binary classification | Imbalanced classes | PR-AUC (precision-recall AUC), not ROC-AUC | ROC-AUC stays misleadingly high under severe imbalance because it's dominated by the (easy) majority-class true-negative rate; PR-AUC focuses on the minority class |
| Binary classification | Asymmetric cost (e.g. missing fraud costs more than a false alarm) | F-beta (beta>1 weights recall higher; beta<1 weights precision higher), or a custom cost-weighted score | Directly encodes the real cost ratio instead of assuming false positives and negatives are equally bad |
| Binary classification | Need calibrated probabilities, not just ranking | Log loss / Brier score | Rewards a model for well-calibrated probabilities, not just correct ordering |
| Regression | Target spans multiple orders of magnitude (e.g. house prices) | RMSE/MAE on `log(target)` | Keeps large-value errors from dominating the loss in relative terms |
| Regression | Outliers should not dominate the score | MAE (or Huber loss) over RMSE | RMSE squares errors, so a few large misses can swamp the average; MAE weighs every error linearly |
| Regression | Need an intuitive "% off" number for stakeholders | MAPE (with care — undefined/unstable near zero targets) | Communicates error in relative, business-readable terms |
| Regression | Cost of over- vs under-prediction is asymmetric (e.g. understaffing costs more than overstaffing) | Quantile (pinball) loss at a chosen service level, or an explicit asymmetric cost function | Symmetric RMSE/MAE assume a unit over-shoot and a unit under-shoot cost the same; a quantile target lets you deliberately bias predictions to the cheaper side and set the over/under rate on purpose, instead of bolting an arbitrary "buffer" onto a symmetric forecast |
| Ranking / recommendation | Position of correct items matters, not just presence | NDCG, MAP@k | Rewards getting the right answer near the top, not just somewhere in the list |

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "ROC-AUC is standard, I'll just report that" | Standard isn't the same as right — under real imbalance, ROC-AUC can look excellent while the model is useless for the minority class. Check PR-AUC too. |
| "The metric is a modeling detail, the business team doesn't need to weigh in" | The metric IS the business decision's cost structure translated into math — this is exactly the "success metric is a pure ML metric with no tie to a business cost" Red Flag from `/ds-frame`. |

See `ds-method` for the shared Rationalizations that apply to every stage.

## Red Flags

See `ds-method`'s Red Flags and `/ds-frame`'s — a metric with no stated tie to the
actual decision cost is the clearest sign this skill was skipped.

See `lessons/the-99-percent-fraud-model.md` for a real example of accuracy
hiding a model that was effectively useless.

## Verification

- [ ] The chosen metric is explicitly tied to the decision's real cost asymmetry,
      not picked by convention.
- [ ] For imbalanced classification, PR-AUC (or an equivalent) was checked
      alongside/instead of ROC-AUC.
- [ ] For skewed regression targets, the metric operates in log-space or another
      scale-appropriate transform.
