# Stage 0 — Problem Framing

## Problem statement

A telecom operator's customer base (7043 accounts, IBM's public "Telco Customer
Churn" dataset). A retention-targeting tool: given an active customer's account
attributes, produce a churn-risk score the retention team uses to prioritize outreach.

## Decision this feeds

A retention team has limited outreach capacity (calls, discount offers) and needs to
decide who to contact this cycle. Today, without this tool, outreach is either
untargeted (expensive, low hit rate) or based on simple tenure/contract-type rules
that miss less obvious risk patterns. A false negative (missed at-risk customer)
costs the customer's future revenue if they churn unretained; a false positive
(unnecessary outreach to a loyal customer) costs a discount/contact that didn't need
to happen — cheaper per-incident, but the volume matters.

## Unit of analysis and target

One row = one customer account, snapshotted at a point in time. Target: `Churn`
(Yes/No, whether the customer left within the observed period) — a direct column,
not a derived definition.

## Do we even need ML?

A single-feature rule was checked: `Contract == "Month-to-month"` alone. Churn rate
among month-to-month customers is real signal, but nowhere close to sufficient on its
own — `tenure`, `InternetService` type, and several service add-ons all visibly move
churn risk within the month-to-month segment too (confirmed in `/ds-explore`), so a
single-rule cut would leave most of the model's eventual lift on the table. A model
combining multiple features is justified.

## Success metric

**ROC-AUC** as the primary ranking metric — at 26.5% churn, the imbalance is real but
not severe enough for ROC-AUC to be the misleading choice it would be at, say,
credit-card-fraud's 0.17% (per `metric-selection`). **PR-AUC reported alongside as
the stricter secondary check regardless** — checking it anyway, not skipping it just
because the imbalance is milder, per `metric-selection`'s own rationalization table.

**Business framing:** `/ds-model` freezes an operating threshold chosen to maximize
**F2** (recall weighted over precision, since a missed at-risk customer is assumed
costlier to the business than one avoidable retention contact) — the frozen
threshold's precision/recall directly maps to "how many churners does this catch,
and how many unnecessary contacts does that cost," which is what the retention team
actually needs to plan capacity against.

## Non-goals

- Not a lifetime-value or discount-sizing model — this scores churn risk only, not
  what retention offer to make.
- Not a real-time system; this is a per-billing-cycle batch scoring use case.
- This is a static snapshot dataset, not a rolling deployment — a real rollout would
  need continuous retraining as the customer base and product mix evolve.
