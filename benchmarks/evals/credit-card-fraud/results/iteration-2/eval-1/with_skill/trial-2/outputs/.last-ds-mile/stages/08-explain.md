# 08 — Interpretation

The Random Forest relies most on `V14`, `V10`, `V4`, `V12`, `V17` (PCA-anonymized
components — no business meaning is recoverable, since these were anonymized before
this dataset was published). This matches the linear-correlation screen from
`02-explore.md`, so the tree model isn't picking up some entirely different, harder-
to-trust signal than a simpler model would.

`Amount` and `Time` are minor contributors relative to the top PCA features —
consistent with `02-explore.md` finding fraud isn't simply "bigger transactions" or
concentrated in a clear time window.

Because the top features are anonymized, this model can flag *that* a transaction
looks anomalous but can't be explained back to a human reviewer in business terms
(e.g. "flagged because of unusual merchant category") — a real limitation if this
were used to justify individual fraud-review decisions to a customer or auditor.
