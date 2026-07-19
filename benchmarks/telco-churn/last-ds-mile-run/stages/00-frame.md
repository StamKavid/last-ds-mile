# 00 — Problem Framing

**Source:** IBM's public Telco Customer Churn sample dataset (fetched via
`sklearn.datasets.fetch_openml("Telco-Customer-Churn")`) — the canonical enterprise
subscription-churn benchmark, widely used and benchmarked in industry and on Kaggle.

**Decision this feeds:** a retention team deciding which customers to target with a
proactive save offer (a discount, a callback) before their next billing cycle — a
targeting problem, not just a scoring exercise. Wrong in either direction costs real
money: missing a genuine churn risk loses a customer worth their remaining lifetime
value; targeting a loyal customer wastes the offer's cost.

**Unit of analysis:** one active subscription account, at a snapshot in time.

**Target definition:** `Churn` — whether the customer left within the last billing
period, as recorded in this snapshot (binary Yes/No).

**Do we even need ML?** A simple rule ("target every month-to-month customer") would
catch a lot of true churners (42.7% churn rate for month-to-month vs. 2.8%/11.3% for
two-year/one-year contracts — see `02-explore.md`) but at very low precision, since
most month-to-month customers still don't churn. Worth quantifying against a real
baseline rather than assuming — see `04-baseline.md`.

**Success metric:** ROC-AUC — this is the metric `sealed_bet` supports for binary
classification (see `BENCHMARKS.md` for a note on why AUPRC would arguably be a better
choice for a retention-targeting problem specifically, and why that's a real, current
gap rather than a deliberate choice for this exact case).

**Non-goals:** no claim of generalizing beyond this snapshot's pricing/contract
structure or beyond a US telecom-like subscription business; no per-customer lifetime
value modeling (that's a separate, harder problem this run doesn't attempt).
