---
description: Open the sealed holdout exactly once and settle the bet by lift over baseline
---

Open the seal — this is irreversible and happens exactly once.

1. Ensure the trained model has produced predictions for every row of
   `.last-ds-mile/held/features.csv`, written as a **two-column** CSV (e.g.
   `preds.csv`): `row_id` echoed from `.last-ds-mile/held/row_ids.csv`, plus the
   prediction itself.

       held = pd.read_csv(".last-ds-mile/held/features.csv")
       ids = pd.read_csv(".last-ds-mile/held/row_ids.csv")["row_id"]
       pd.DataFrame({"row_id": ids, "pred": model.predict(held)}).to_csv(
           "preds.csv", index=False
       )

   Predictions are joined to the sealed labels on `row_id`, not on row position,
   so a pipeline that sorts or reindexes can't silently score against the wrong
   rows. Every held row must appear exactly once; the order in `preds.csv` does
   not matter. `row_id` is deliberately kept out of `features.csv` — it's a
   row-order proxy and would be a leakage vector inside the feature matrix.
2. Run: `python -m sealed_bet.score --preds preds.csv`
3. Report the verdict from `LEDGER.md`: `lift = (sealed − baseline)/σ`, ship iff
   `> 2σ`. If the dev−sealed gap is large, say so plainly — the model overfit the
   dev data or the dev estimate was optimistic; do not rationalize it.
4. This step also writes `.last-ds-mile/held/revealed.csv` (the true target plus your
   submitted predictions) — the sanctioned source for `/ds-evaluate`'s slice/calibration
   analysis and `/ds-explain`'s held-set feature importance. Do not read
   `.last-ds-mile/held/_sealed_target.csv` directly for that; it stays guard-blocked.
