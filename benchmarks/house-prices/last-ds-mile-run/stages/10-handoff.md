# 10 — Reproducibility & Handoff

**Gate check:** environment pinned with exact versions (below) — confirmed before
packaging.

**Model card:**
- **Predicts:** `log1p(SalePrice)` for a residential property sale in Ames, Iowa
  (back-transform with `expm1` for a dollar figure).
- **Training data:** 1,171 sales (the dev split; 289 held out and never touched until
  `/ds-open`), Kaggle "House Prices: Advanced Regression Techniques" `train.csv`,
  76 features (see `03-prep.md` for the exact list and exclusions).
- **Metric and baseline lift:** RMSE (log scale) = 0.131 sealed vs. 0.408 flat-median
  baseline — lift = 26.4σ (see `09-report.md`).
- **Intended use:** a suggested list-price signal shown to a seller before they set an
  asking price, for Ames-market-like residential sales.
- **Out-of-scope use:** any other market/region, any claim about post-sale transaction
  terms (financing, sale condition), and low-tier/older-neighborhood homes without the
  explicit lower-confidence caveat from `09-report.md`.

**Environment (pinned, exact versions installed for this run):**
```
pandas==2.3.3
numpy==2.3.5
scikit-learn==1.7.2
autogluon.tabular==1.5.0
```
(Managed by this repo's own `uv`-based `requirements-dev.txt` — see the main
`last-ds-mile` README's Development section.)

**Rerun confirmation:** this entire run — `/ds-seal` → `/ds-auto` (6 iterations,
1 accepted) → `/ds-open` — reruns cleanly from `prepared_with_sale_period.csv` using
only the pinned environment above; no manual/interactive steps beyond what's documented
in stages 00–08.

**Artifact location:** refit predictor at `.last-ds-mile/auto/refit/` (AutoGluon
`TabularPredictor` directory — not committed to git, regenerable from
`prepared_with_sale_period.csv` + this stage log); `Contract`/`LEDGER.md` (the durable,
committed evidence) at `.last-ds-mile/contract.json` / `.last-ds-mile/LEDGER.md`;
training-data hash recorded in the Contract (`data_hash`).
