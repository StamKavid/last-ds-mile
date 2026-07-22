---
name: causal-vs-predictive
description: Distinguishes predictive/associational feature importance from causal claims about what would happen if a feature were changed. Catches "X reduces/causes/drives Y" language stated as confirmed when only a correlational comparison was run. Use during /ds-explain when describing driver importance, or during /ds-report when a recommendation implies intervening on a feature (targeting a segment, changing a policy, pushing customers toward an option) rather than just ranking or scoring them.
---

# causal-vs-predictive

## Overview

A model can be an excellent predictor of an outcome while being silent on what
causes it — and the two get conflated constantly, because the same word
("driver," "important feature") is used for both. This skill is the check that
catches "X reduces/causes/drives Y, confirmed" language when only an associational
comparison actually ran.

## When to Use

- Writing up feature importance, SHAP findings, or a bivariate/EDA relationship in
  `/ds-explain` or `/ds-explore`.
- Writing a recommendation in `/ds-report` that implies *intervening* on a feature
  (targeting a segment for a changed offer, pushing customers toward an option,
  recommending a policy change) — as opposed to *ranking or scoring* individuals
  using that feature, which doesn't need this check.
- NOT for: the model's predictive validity itself (that's `/ds-evaluate`) — a model
  can be a perfectly valid predictor and still say nothing about causal effects.
  Using a score to prioritize outreach or flag transactions needs the score to be
  predictively valid, not causally identified.

## Core Process

1. For every feature described as a "driver" of the target, ask which of two claims
   is actually being made:
   - **Predictive/ranking claim**: "this feature helps distinguish who is more
     likely to have outcome Y" — supported directly by permutation
     importance/SHAP/correlation. No further check needed.
   - **Causal/interventional claim**: "changing this feature (for a given
     individual) would change their outcome" — this is what "reduces," "causes,"
     "drives" (in the active sense), or a recommendation to intervene actually
     asserts.
2. If it's a causal claim, ask what would have to be true for the correlation to
   reflect a real causal effect rather than a confound. The single most common
   confound to check explicitly: **self-selection** — did the subject choose this
   feature's value themselves (a contract length, a plan tier, a loyalty program,
   an opt-in)? If so, the feature may be a *symptom* of the outcome's underlying
   propensity, not a cause of it.
3. If no causal identification strategy is available or stated (a randomized
   experiment, a natural experiment, an instrument, or at minimum an explicit,
   defensible argument for why the obvious confound doesn't apply), **reword the
   claim as an association**: "X is associated with Y," not "X reduces/causes/
   drives Y."
4. Effect size is not evidence either way — a large, clean, monotonic correlation
   is exactly as consistent with a large confound as with a large causal effect.
   Don't let a dramatic effect size substitute for the identification argument.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The effect is huge and monotonic, it must be real" | Effect size doesn't distinguish correlation from causation — a strong confound produces a strong spurious correlation just as easily as a real causal effect does. |
| "Everyone knows 'driver' just means important feature, not literally causal" | Not reliably true for the actual reader six months later — this exact phrasing is what gets copied into a slide deck or turned into a policy recommendation. |
| "We're not recommending an intervention, just describing the finding" | The distinction has to be made *at the point the finding is written down*, not deferred to whoever reads it later and decides to act on it — by then the causal-sounding language has already done its work. |

See `ds-method` for the shared Rationalizations that apply to every stage.

## Red Flags

| Red Flag | What it usually means |
|---|---|
| A feature the subject themselves chose (a contract, a plan, a loyalty tier, an opt-in) is described as "reducing" or "causing" the outcome, with no self-selection argument | The correlation may be explained entirely by who chooses that feature value, not by the feature's own causal effect. |
| A report recommends intervening on a feature ("push customers toward X," "target the Y segment for a changed offer") whose importance was established only via SHAP, permutation importance, or a bivariate correlation | The recommendation has smuggled in a causal claim the analysis never made. |

See `lessons/the-contract-that-wasnt-the-cause.md` for a real example of this exact
failure mode.

## Verification

- [ ] Every "reduces/causes/drives" claim about a feature is either backed by a
      stated causal-identification argument, or reworded as "associated with."
- [ ] Self-selection was explicitly considered for any feature whose value the
      subject chose themselves.
- [ ] Any recommendation that implies intervening on a feature (not just ranking or
      scoring with it) was checked against this distinction before it shipped.
