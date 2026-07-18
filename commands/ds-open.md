---
description: Open the sealed holdout exactly once and settle the bet by lift over baseline
---

Open the seal — this is irreversible and happens exactly once.

1. Ensure the trained model has produced predictions for every row of
   `.last-ds-mile/held/features.csv`, written as a one-column CSV (e.g. `preds.csv`).
2. Run: `python -m sealed_bet.score --preds preds.csv`
3. Report the verdict from `LEDGER.md`: `lift = (sealed − baseline)/σ`, ship iff
   `> 2σ`. If the dev−sealed gap is large, say so plainly — the model overfit the
   dev data or the dev estimate was optimistic; do not rationalize it.
4. This step also writes `.last-ds-mile/held/revealed.csv` (the true target plus your
   submitted predictions) — the sanctioned source for `/ds-evaluate`'s slice/calibration
   analysis and `/ds-explain`'s held-set feature importance. Do not read
   `.last-ds-mile/held/_sealed_target.csv` directly for that; it stays guard-blocked.
