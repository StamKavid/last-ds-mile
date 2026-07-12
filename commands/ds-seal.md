---
description: Seal a holdout and write the Contract — the one human signature of the Sealed Bet
---

Seal the dataset so the rest of the work is honest by construction.

1. Confirm with the user: the target column, the task (regression/classification),
   the metric, and the split strategy (`random`, or `group`/`time` with a key/column).
   If a column repeats per entity, recommend `group`; if there is a date and the
   prediction is forward-looking, recommend `time`. (Full auto-recommendation lands
   in a later release; for now confirm these explicitly.)
2. Run:
   `python -m sealed_bet.seal --data <path> --target <col> --task <task> --metric <metric> --strategy <strategy> [--group-key <col>] [--time-col <col>]`
3. Tell the user the seal is set: they may now build freely on `.last-ds-mile/dev.csv`;
   the holdout labels are locked and `seal_guard` will refuse to read them. When ready,
   `/ds-open` settles the bet — once.
