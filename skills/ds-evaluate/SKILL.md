---
name: ds-evaluate
description: Evaluates the chosen model on metrics aligned to the /ds-frame decision, including calibration and slice/subgroup performance, not just one aggregate leaderboard number. Use after modeling, before writing conclusions or a report.
---

# ds-evaluate — Evaluation & Error Analysis

## Overview

Produces the full evidence picture for the chosen model: the decision-aligned metric,
calibration, subgroup performance, and where it fails — not a single leaderboard number.

## When to Use

- After `/ds-model` has produced a best candidate.
- Before writing conclusions or a stakeholder report.
- NOT for: writing the stakeholder narrative itself (that's `/ds-report`) — this stage
  produces the evidence `/ds-report` is required to draw on.

## Core Process

1. Re-confirm the metric being reported is the one chosen in `/ds-frame`, not a
   different, more flattering metric picked after the fact. Report it as a mean ±
   spread across folds, not a bare point estimate — see `uncertainty-quantification`.
2. Check calibration where relevant (predicted probabilities vs. observed frequencies),
   not only discrimination (e.g. AUC).
3. Slice performance by meaningful subgroups: segment, time period, geography, or
   whatever the decision depends on — **and, whenever the dataset includes attributes
   like age, gender, race/ethnicity, disability, or another protected/sensitive
   characteristic (or a close proxy, e.g. zip code), slice by those explicitly too**,
   not only by business-convenience segments. A single aggregate number can hide a
   subgroup where the model fails badly, and for protected attributes that gap is a
   fairness and often a regulatory finding, not just a modeling curiosity — flag any
   material gap plainly rather than only noting it in passing.
4. Run error analysis: look at the worst mispredictions and look for a pattern.
5. If a fixed test set or a real deployment population is in scope, check for
   distribution shift between training data and that population — see
   `distribution-shift` — before trusting that CV performance will transfer.
6. Export the slice-performance comparison (bar chart of the metric per subgroup, always
   against the overall number so the gap is visible) and, for a probabilistic
   classifier, the calibration curve (predicted-decile vs. actual-rate) as figures to
   `.last-ds-mile/figures/07-<name>.png` — per `data-viz-standards`. These are the two
   plots this stage's own findings are least readable as prose.
7. Write to `.last-ds-mile/stages/07-evaluate.md`: the aggregate metric with its spread,
   the calibration check, the slice table (including any protected-attribute slices),
   error-analysis notes, any distribution-shift check, and a reference to each exported
   figure.
8. Proceed to `/ds-iterate` next, not directly to `/ds-explain` — it reads this stage's
   findings and decides whether a fixable weakness warrants another pass.

## Common Rationalizations

See `ds-method` for the shared Rationalizations that apply to every stage, in particular
"one aggregate metric is enough to report" — this stage exists specifically to prevent
that shortcut from reaching `/ds-report`.

## Red Flags

| Red Flag | What it usually means |
|---|---|
| The overall metric is good but was never checked per-slice | This is exactly the condition `/ds-report`'s Hard Gate checks for — resolve it here, not there. |
| The dataset has a protected/sensitive attribute (or a close proxy) and it was never used as a slice | An aggregate metric can be good overall while the model performs materially worse for one group — this is a fairness finding a business-segment slice table won't surface on its own. |
| A metric or comparison is reported with no fold spread, or two numbers are called "consistent" with no spread shown | See `uncertainty-quantification` — a gap smaller than the noise is not a finding. |

See `ds-method` for the shared Red Flags that apply to every stage.

## Verification

- [ ] The metric reported is the one chosen in `/ds-frame`, not a substituted one, and
      reported with its fold spread, not a bare point estimate.
- [ ] Calibration checked where the problem type makes it relevant.
- [ ] A slice/subgroup performance table exists, not only an aggregate number —
      including protected/sensitive-attribute slices if any such column exists in the
      dataset.
- [ ] Error analysis performed on the worst mispredictions.
- [ ] If a fixed test set or deployment population is in scope, distribution shift
      against training data was checked, not assumed absent.
- [ ] Slice-performance (and, if classification, calibration) exported as a figure to
      `.last-ds-mile/figures/`, not only a table in prose.
- [ ] `.last-ds-mile/stages/07-evaluate.md` written.
