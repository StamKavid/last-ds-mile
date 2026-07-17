# 09 — Report

**Gate check:** `07-evaluate.md` includes slice/subgroup performance (by price tier), not
only an aggregate number — confirmed before writing this report.

**Decision this informs** (from `00-frame.md`): a suggested list price shown to a
seller before they set an asking price.

**Recommendation:** ship this model for mid- and high-priced homes (RMSE ≈ 0.10 on the
log scale, i.e. typically within roughly ±10% of true value); show suggested prices for
low-tier homes (< ~$137k, concentrated in Ames's older neighborhoods) with an explicit
lower-confidence flag rather than the same fixed-precision number, since the model's
error there (RMSE 0.176) is materially worse.

**Evidence:**
- **Baseline comparison:** the sealed model clears the honest floor baseline (flat
  median prediction, RMSE 0.408) by **lift = 26.4σ** — decisively real, not noise, and
  far above the 2σ ship threshold.
- **Ceiling context:** sealed RMSE (0.131) sits close to the human-provided ceiling
  estimate (0.115) informed by the Kaggle community's known "genuinely honest, not
  overfit-to-public-test" range for this exact competition/metric — this is a strong
  result relative to what's understood to be achievable here, not just relative to a
  weak baseline.
- **Slice performance:** see `07-evaluate.md` — the low-price tier is the one place this
  recommendation should be qualified.

**Assumptions and limitations:**
- Trained on 2006–2010 Ames, Iowa sales only — no claim of generalization to other
  markets, price regimes, or time periods (validated with a time-based split
  specifically to be honest about this, per `05-validate.md`).
- Excludes sale-transaction fields (`SaleType`/`SaleCondition`/timing) by design, since
  they aren't known before a list price is suggested — this model answers "what should
  we suggest," not "what did similar homes actually sell for under similar deal terms."
- Weakest on low-priced, older-neighborhood homes — the segment where idiosyncratic
  condition issues matter more than the structural features capture.
- The split-adversary Probe (an automated check that the dev/held split itself isn't
  distinguishable/leaky) did not run for this dataset — it errored on categorical
  columns (a real, current limitation of `sealed_bet.adversary.split_adversary`,
  discovered by this run; see `BENCHMARKS.md`). The seal itself is unaffected (the Probe
  is warn-only by design), but that specific automated cross-check simply didn't execute
  here — a manual sanity check (the time-based split, the slice table, and the feature
  importance sanity check above) stands in for it in this report.
