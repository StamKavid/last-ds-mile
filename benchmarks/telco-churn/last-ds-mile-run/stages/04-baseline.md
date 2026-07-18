# 04 — Honest Baseline

**Baseline definition (revised):** the real non-ML rival this stage originally only
described in prose — the historical churn rate per `Contract` type, computed on dev data
alone and applied to held rows by their `Contract` value
(`benchmarks/telco-churn/baseline.py:contract_churn_rate`) — is now the Contract's
actual sealed baseline, via `sealed_bet.seal`'s `--baseline-py` flag. A constant
probability baseline (`roc_auc`'s previous default) scores exactly 0.5 AUC on *every*
binary classification dataset by construction — it isn't a floor specific to this
problem, and a "lift over baseline" measured against it was really just "lift over a
coin flip," which every non-broken model clears. This closes that gap.

**Sealed score:** `baseline_score = 0.7420` (ROC-AUC) — `baseline_kind: heuristic` in
`contract.json`. This is the scored version of "target by contract type using the
historical rate": rank/prioritize by how much a customer's `Contract` segment has
historically churned, no model required. It substantially outperforms a constant
prediction precisely because `Contract` is this dataset's single strongest driver
(`02-explore.md`) — an analyst with a spreadsheet and last quarter's churn-by-segment
numbers gets a large share of the way to the sealed model's eventual AUC (`06-model.md`)
before any modeling starts.

**"Do we even need ML?" check** (from `00-frame.md`): "target every month-to-month
customer" (a binary rule, not a ranking) is still the simplest non-ML alternative and
still has the precision problem described here originally. But its *scored* analogue —
rank by segment churn rate — is what actually sets the honest floor now, and it is a
real, credible floor (0.7420), not the near-meaningless 0.5 constant this run originally
measured against. (This number moved from an earlier re-seal's 0.7283 once a
stratified-split fix landed in `sealed_bet` — see `05-validate.md` — which changed
exactly which rows land in dev vs. held; both are legitimate seals of the same
heuristic, just over different row samples.)

**What "beating it" means:** the ship gate is `lift > 2σ`, where σ is the standard
deviation of the *paired* bootstrap difference between the model's score and this same
heuristic's score on the same held rows (`sealed_bet.metrics.paired_bootstrap_sigma`),
not the model's own score variance in isolation — a model has to be reliably better than
"know last quarter's churn rate per contract type," not just reliably better than a coin
flip.
