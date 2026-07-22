---
title: The Contract That Wasn't the Cause
skills: [ds-explain, ds-report]
stages: []
---

# The Contract That Wasn't the Cause

A churn-prediction project found that customers on two-year contracts churned at
2.8%, versus 42.7% for month-to-month customers — a huge, clean, monotonic gap. The
EDA writeup recorded it as: "Hypothesis: contract commitment reduces churn.
Confirmed strongly." Everyone moved on, and the finding sat in the project's
evidence trail as settled.

It wasn't settled. It was correlational, and it got written up as causal. Customers
who choose a two-year contract are not a random sample of the customer base — they
plausibly already skew more stable, more satisfied, or more price-committed
*before* they ever sign anything. The contract length is at least partly a *symptom*
of low churn propensity, not necessarily its *cause*. Nothing in the dataset — no
random assignment, no natural experiment, no instrument — rules that explanation
out. A model can be excellent at predicting who churns using `Contract` as a
feature (it was) while being completely silent on what happens if you *change*
someone's contract length who wouldn't have chosen it themselves.

The gap only mattered because of what it was quietly setting up: the natural next
move for a retention team reading "commitment reduces churn, confirmed" is to start
pushing reluctant month-to-month customers onto longer contracts. If the real
causal effect of contract length on an individual's churn probability is much
smaller than the observed group gap — plausible, given the self-selection story —
that intervention could cost money in discounts and deliver little of the promised
retention. The predictive model was never wrong. The write-up's causal language was.

The fix was to re-read every "driver," "reduces," or "causes" claim in the
project's evidence trail and ask: is this describing what predicts the outcome, or
what would change it if you intervened? Only the second question needs a causal
identification strategy. The corrected version says "associated with," names the
self-selection confound explicitly, and states plainly that the dataset can't
settle the causal question — a smaller, less satisfying claim, and the honest one.

**Lesson:** a strong, clean, monotonic correlation between a feature and the target
is not evidence that changing the feature would change the target — especially
when the feature is something the subject themselves chose (a contract, a plan
tier, a loyalty program). Before writing "X reduces/causes/drives Y" anywhere in a
findings doc, ask what would have to be true for that to be a causal claim rather
than a predictive one, and whether this dataset can actually support it. If it
can't, say "associated with" and name the plausible confound — a smaller claim
survives contact with a skeptical reader; an inflated one gets acted on.
