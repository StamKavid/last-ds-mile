# Stage 7½ — Iteration Log (`/ds-iterate`)

Diagnoses `.last-ds-mile/stages/07-evaluate.md`'s findings and decides whether to loop
back or proceed. Per `ds-iterate`'s process, each loop is appended below, not
overwritten.

## Revision note

Loop 1 was originally tested against the pre-fix single one-hot CatBoost model. Since
`/ds-model` now ships `Blend(LightGBM + CatBoost-native)`, this loop was re-run against
the actual corrected, shipped model — a diagnosis and fix are only as trustworthy as
the model they were tested on, and the shipped model changed underneath this
experiment. Loop 2's finding (abnormal-sale rate) doesn't depend on model choice at
all — it's a property of the data slice — so it wasn't re-run.

---

## Loop 1 (re-run against the corrected Blend model)

**Evidence read:** `/ds-evaluate`'s error analysis traced the two worst mispredictions
(Ids 1299, 524) to the documented Ames-dataset `GrLivArea > 4000` outliers — two
`OverallQual=10` Edwards homes that sold far below what their quality/size would
predict. Unchanged finding, now confirmed against the Blend's own OOF predictions.

**Diagnosis:** slice-specific weakness, with a named, testable cause (two anomalous
training rows), per the routing table's "slice-specific weakness" row.

**Route back to:** `/ds-prep` — test excluding the two documented outliers from the
training portion of the pipeline. Re-tested exactly as before, but now refitting both
blend components (LightGBM one-hot, CatBoost-native) per fold with `Id ∈ {524, 1299}`
excluded from training rows only — they remain in whichever validation fold they
naturally fall into.

**Result, paired per-fold (before → after, Blend model):**

| Fold | Before | After | Diff |
|---|---|---|---|
| 0 | 0.1103 | 0.1109 | **−0.0006** |
| 1 | 0.1197 | 0.1169 | 0.0027 |
| 2 | 0.1137 | 0.1116 | 0.0021 |
| 3 | 0.1288 | 0.1277 | 0.0010 |
| 4 | 0.1495 | 0.1495 | 0.0000 |

Mean RMSE: **0.1244 → 0.1233** (mean paired diff **0.0010**). Edwards-slice RMSE:
0.2126 → 0.2113 (near-zero change). Overall pooled OOF RMSE: 0.1252 → 0.1242.

**Verdict, per `uncertainty-quantification`:** the Blend's own fold std is 0.0141 —
the mean paired improvement here (0.0010) is roughly **1/14th of that std**, an even
smaller fraction than the original run found against the old single-model pipeline
(which was ~1/6th). **Fold 0 got very slightly *worse*, not better** — the sign isn't
even consistent across folds, which is stronger evidence against adoption than v1 had:
a real fix should help most folds and hurt none; this one helps three, is flat on one,
and mildly hurts one. **The rejection is not just reconfirmed under the corrected
model — it's reconfirmed more strongly.**

**Decision: do not adopt this change into the shipped model.** Same conclusion as the
original run, now verified against the model that's actually shipping rather than a
superseded one. Recorded here so the next person doesn't re-try the identical
experiment expecting a different answer under the new pipeline.

## Loop 2 — considered, not run (unchanged; not model-dependent)

**Evidence read:** the Q1 (cheapest) quintile and `IDOTRR`/`Edwards` neighborhoods
remain the dataset's clearest weaknesses under the corrected model too (see
`07-evaluate.md`).

**Diagnosis attempted:** checked whether `SaleCondition` (already a feature in the
pipeline — `Abnorml`, `Family`, `Alloca`, etc.) explains the gap. Abnormal-sale rate in
the cheapest quintile is **15.3%** vs. **6.9%** dataset-wide — a real, ~2.2x elevated
rate of non-arms-length sales among cheap homes. This is a genuine partial explanation
of *why* this slice is harder, but `SaleCondition` is already in the model — not a
missing-feature gap `/ds-prep` can close, it's inherent heterogeneity within a
category the model already sees. This diagnosis is about the data slice, not about
which model is fit to it, so it carries forward unchanged.

**No further route-back attempted within this run's scope.** No untried, specific
diagnosis left to test — looping again with "try a different model" or "try a
different seed" would be exactly the noise-chasing rationalization `ds-iterate` and
`uncertainty-quantification` both warn against.

**Decision: stop iterating. Carry the Q1/IDOTRR/Edwards weakness forward to
`/ds-report` as a named, evidence-backed limitation** (elevated abnormal-sale rate in
the cheapest segment), not a vague "the model isn't perfect" caveat.

---

## Final verdict

**Proceed to `/ds-explain`.** The shipped model is `/ds-model`'s
`Blend(LightGBM + CatBoost-native)` (mean RMSE 0.1244 ± 0.0141), unchanged by Loop 1's
rejected experiment — now on both counts: rejected originally, and rejected again
under the corrected pipeline. Two named limitations carry forward: the two documented
`GrLivArea>4000` Edwards outliers, and the cheapest-quintile weakness tied to a higher
abnormal-sale rate.
