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
- **Baseline comparison (revised — see `04-baseline.md`/`06-model.md`):** the sealed
  model clears a real, scored non-ML rival — a neighborhood-median $/sqft lookup,
  RMSE 0.2487 — by **lift = 9.46σ**, using the paired bootstrap difference between the
  model's and baseline's scores on the same held rows as σ. This is a smaller, more
  honest lift than the 26.4σ this report originally cited: that number was measured
  against a flat median (a much weaker floor) using the model's own score variance in
  isolation as σ, not the paired difference against a real rival. Still decisively above
  the 2σ ship threshold.
- **Ceiling context:** sealed RMSE (0.1311) sits close to the human-provided ceiling
  estimate (0.115) informed by the Kaggle community's known "genuinely honest, not
  overfit-to-public-test" range for this exact competition/metric — this is a strong
  result relative to what's understood to be achievable here, not just relative to a
  weak baseline.
- **Slice performance:** see `07-evaluate.md` — the low-price tier is the one place this
  recommendation should be qualified. (Freshly recomputed via `sealed_bet.score.reveal()`;
  see that stage's note.)

**Assumptions and limitations:**
- Trained on 2006–2010 Ames, Iowa sales only — no claim of generalization to other
  markets, price regimes, or time periods (validated with a time-based split
  specifically to be honest about this, per `05-validate.md`).
- Excludes sale-transaction fields (`SaleType`/`SaleCondition`/timing) by design, since
  they aren't known before a list price is suggested — this model answers "what should
  we suggest," not "what did similar homes actually sell for under similar deal terms."
- Weakest on low-priced, older-neighborhood homes — the segment where idiosyncratic
  condition issues matter more than the structural features capture.
- The split-adversary Probe now runs (a categorical-encoding/missing-value bug that
  previously crashed it on every real dataset is fixed — see `BENCHMARKS.md`), but it
  reports "⚠ SUSPECT" here — expected and correct for a deliberate *time* split, where
  dev and held are supposed to look different (see `05-validate.md`'s "Verified after
  sealing" note). The manual sanity check (the time-based split reasoning, the slice
  table, and the feature-importance sanity check) still carries the actual argument for
  why this split isn't leaky; the automated probe's verdict just doesn't apply cleanly
  to a `time` strategy yet.
- The leakage-adversary Probe now also runs (previously dead code, never wired into
  `seal()` — see `BENCHMARKS.md`) and reports CLEAR: no feature solo-predicts the target
  above the 0.95 threshold (top: `OverallQual` at 0.669), consistent with `08-explain.md`'s
  feature-importance sanity check.
