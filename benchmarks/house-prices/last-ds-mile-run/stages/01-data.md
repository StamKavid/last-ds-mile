# 01 — Data Understanding

**Sanitization gate:** `train.csv`/`test.csv` are plain CSV, no pickled/serialized
objects. Provenance: Kaggle's official competition data page (a well-known, long-public
teaching dataset — De Cock 2011 Ames Assessor's Office data). Scanned column values and
`data_description.txt` for hidden unicode/injected-instruction text — none found. Only
`train.csv` is used from here on (`test.csv` has no `SalePrice` column — it's Kaggle's
own held-out set, which we can't score against; our own dev/held split for the Sealed Bet
comes from `train.csv` alone, via `/ds-seal`).

**Shape:** 1460 rows × 81 columns (80 features + `Id` + target `SalePrice`).

**Data dictionary:** the dataset ships its own official dictionary,
`data_description.txt` (79 features, one entry each, provided by the dataset's original
author) — not duplicated here; it's the source of truth for every column's meaning.

**dtypes:** 43 object (categorical), 35 int64, 3 float64 (`LotFrontage`, `MasVnrArea`,
`GarageYrBlt` — all float only because of missing values, not true continuous scale
beyond `LotFrontage`/`MasVnrArea`).

**Missingness (19 of 81 columns affected):**

| Column | Missing | Why (per `data_description.txt`) |
|---|---|---|
| `PoolQC` | 1453 (99.5%) | No pool — `NA` is a valid category ("no pool"), not missing data |
| `MiscFeature` | 1406 (96.3%) | No misc feature present |
| `Alley` | 1369 (93.8%) | No alley access |
| `Fence` | 1179 (80.8%) | No fence |
| `MasVnrType`/`MasVnrArea` | 872 / 8 | No masonry veneer (large NA count) vs. 8 genuine unknowns |
| `FireplaceQu` | 690 (47.3%) | No fireplace |
| `LotFrontage` | 259 (17.7%) | Genuinely unrecorded street frontage |
| `Garage*` (6 cols) | 81 each | No garage |
| `Bsmt*` (5 cols) | 37–38 each | No basement |
| `Electrical` | 1 | Single genuine unknown |

**Integrity findings:** for the large-count columns above, `NA` in the raw CSV means
"feature doesn't apply to this house" per `data_description.txt` — not a missing
measurement. Treating it as an ordinary numeric/categorical NaN to impute (mean, mode)
would be wrong; `/ds-prep` encodes these as an explicit "None"/0 category rather than
imputing a central tendency. No duplicate rows, no duplicate `Id`. Sanity-checked
`YearBuilt` (1872–2010), `GarageYrBlt` (1900–2010, none exceed `YrSold`), `YrSold`
(2006–2010) — all plausible, no future-dated or impossible values in `train.csv`.
(Note for the record: this dataset is widely known to have one implausible
`GarageYrBlt` = 2207 row, but it's in Kaggle's `test.csv`, which isn't used for our own
dev/held split — so it doesn't affect this run.)

**Open questions for a real stakeholder** (not resolvable from the data alone): whether
"sale price" here includes any seller concessions/financing incentives baked into the
listed price, and whether the 2006–2010 window (which spans the US housing crash)
should be modeled as one regime or split — flagged here, addressed as a documented
limitation in `09-report.md` rather than silently assumed away.
