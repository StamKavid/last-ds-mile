# 02 — Exploratory Data Analysis

## Univariate

- **Class**: 284,315 genuine / 492 fraud (0.173% positive). Severe imbalance
  confirmed as the dominant characteristic of this problem.
  See `.last-ds-mile/figures/02-class-imbalance.png`.
- **Amount**: heavily right-skewed (mean $88.35, median $22.00, max $25,691.16).
  1,825 rows (0.64%) have `Amount == 0`.
- **Time**: near-uniform coverage over ~48 hours with two low-activity dips
  (overnight periods) — expected diurnal pattern, not itself a strong
  fraud signal (see bivariate).
- **V1–V28**: all roughly mean-zero, unit-ish scale by construction (PCA
  output), but per-column ranges vary widely (some span ±70+).

## Bivariate (vs. Class)

Computed Cohen's d (standardized mean difference) between fraud and genuine
for every feature. Strongest separators:

| Feature | Cohen's d | Direction |
|---|---|---|
| V14 | -2.26 | fraud much lower |
| V4  | +2.01 | fraud much higher |
| V11 | +1.88 | fraud much higher |
| V12 | -1.87 | fraud much lower |
| V10 | -1.61 | fraud much lower |

**Hypothesis**: these five PCA components jointly encode whatever raw
transaction attributes (merchant category, velocity, device/location
signals — undisclosed) most strongly distinguish fraud, since the PCA was
fit on the original bank features, not on the label. This is legitimate
signal, not leakage — confirmed by checking overlap: genuine transactions'
values fall inside the fraud range for V14 in 99.9% of genuine cases (i.e.
no feature perfectly separates the classes on its own; d > 2 is strong but
not deterministic). See `.last-ds-mile/figures/02-v14-by-class.png`.

**Leakage check**: per the Red Flag in `ds-explore`/`ds-method` ("a feature
is almost perfectly separated by target"), V14 was checked explicitly — it
is strongly associated but not perfectly separating, and it's derived from
pre-label raw features via a PCA the dataset authors applied uniformly. Not
flagged as leakage. No feature is a disguised copy of `Class` or an
after-the-fact fraud-outcome field (e.g. no chargeback/dispute-status-like
column exists in the schema at all).

- **Amount vs Class**: fraud transactions average $122.21 vs $88.29 for
  genuine — a real but weak difference (d = 0.13). Transactions with
  `Amount == 0` have a fraud rate of 1.48% vs 0.16% overall (~9x), but this
  is a small subgroup (1,825 rows, only a handful fraud) — noted as a
  hypothesis to watch in error analysis, not a strong standalone signal.
- **Time vs Class**: correlation -0.012, essentially no linear relationship.
  Hypothesis: fraud is not concentrated by time-of-day/window position in
  this 48-hour sample; `Time` is unlikely to be a useful raw feature and
  isn't a real timestamp anyway (see `01-data.md`).

## Collinearity

PCA components are orthogonal by construction (V1-V28), so no meaningful
collinearity expected among them; not separately computed since the
transform guarantees it.

## Leakage candidates flagged for `/ds-prep`

- None beyond the note above. `Time`/`Amount` are the only non-PCA'd
  features and neither shows suspiciously perfect separation.
- Duplicate rows (from `01-data.md`) remain the main leakage vector to
  handle — via `/ds-prep` deduplication and `/ds-validate` split integrity,
  not a feature-leakage issue.

## Figures exported

- `.last-ds-mile/figures/02-class-imbalance.png` — class distribution (log scale).
- `.last-ds-mile/figures/02-v14-by-class.png` — strongest bivariate separator.
