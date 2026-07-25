# 02 — Exploratory Data Analysis

## Univariate

- **Class**: 284,315 genuine (99.83%) vs. 492 fraud (0.17%). See
  `.last-ds-mile/figures/02-class-distribution.png`.
- **Amount**: right-skewed for both classes. Fraud: median $9.25, mean
  $122.21 (max $2,125.87). Genuine: median $22.00, mean $88.29 (max
  $25,691.16).
  - **Hypothesis**: fraudulent transactions skew toward small amounts at the
    median (consistent with "card testing" — small-value probes before a
    larger fraudulent charge) but have a fatter tail relative to their own
    distribution than genuine transactions' typical range, pulling the fraud
    mean above the genuine mean despite the lower median. Worth an `Amount`-
    derived feature (e.g. log-amount) in `/ds-prep`.
- **Time / hour-of-day** (Time mod 24h): fraud rate is far from uniform
  across the 2-day window — hour 2 has a 1.71% fraud rate (10x the 0.17%
  baseline) on 3,328 transactions, vs. ~0.05–0.1% during business hours
  (e.g. hour 10: 0.05% on 16,598 transactions).
  - **Hypothesis**: fraud is proportionally more common during low-volume
    overnight hours because genuine cardholder activity drops off but
    automated/fraudulent activity doesn't track the same daily rhythm. This
    makes hour-of-day a legitimate candidate feature, not leakage — it's
    known at transaction time.

## Bivariate — feature vs. target

- Ranked by single-feature AUC, the strongest predictors are **V14 (0.949),
  V4 (0.938), V12 (0.937), V11 (0.918), V10 (0.914), V3 (0.912)** — several
  individual PCA components already separate the classes well on their own.
  See `.last-ds-mile/figures/02-v14-by-class.png` for V14, the strongest.
  - **Hypothesis**: these are the PCA components carrying most of the
    variance from whatever original features (likely transaction-pattern /
    velocity signals) the dataset publisher anonymized. This is consistent
    with published analyses of this exact dataset, not an artifact specific
    to this copy of the file.
- **Leakage check on this finding**: a single-feature AUC of 0.95 is high but
  **not** the near-1.0 near-perfect separation that would indicate the
  target leaked into a feature. Per `/ds-frame`'s information inventory,
  `V1`–`V28` are pre-computed per-transaction PCA components with no
  post-outcome fields in the dataset — there's no plausible mechanism for
  `Class` to have leaked into them. Treating this as genuine signal, not a
  leakage candidate to strip out, but flagging it here per `ds-explore`'s
  red-flag process so `/ds-prep` and `/ds-model` don't need to re-derive
  this reasoning.
- Amount and Time individually have much weaker single-feature AUC than the
  top PCA components (not in the top 10), consistent with them being
  secondary/contextual signal rather than the primary fraud signature.

## Duplicate rows revisited (from `/ds-data`'s open question)
- Fraud rate among the 1,854 duplicate-involved rows is **1.73%**, vs.
  **0.16%** among non-duplicated rows — duplicates are ~10x more likely to
  be fraud (32 of 492 fraud rows, 6.5% of all fraud, are duplicate-involved).
  - **Hypothesis**: this matches known fraud-ring behavior — repeated
    near-identical small charges (card testing / rapid repeat attempts)
    produce genuinely identical rows in a PCA-anonymized, no-card-ID
    dataset, rather than being a data-pipeline artifact. Recommendation for
    `/ds-prep` and `/ds-validate`: do not blanket-drop duplicates (it would
    disproportionately remove real fraud signal), but **do** ensure
    duplicate rows don't end up split across train and test — that would
    let the model memorize an exact row instead of generalizing, inflating
    validation metrics.

## Leakage candidates flagged for `/ds-prep` and `/ds-validate`
1. `V14`/`V4`/`V12` high single-feature AUC — assessed above as genuine
   signal, not leakage, but documented so the reasoning is auditable.
2. Duplicate rows correlating with fraud — real signal, but a **train/test
   split leakage risk** if identical rows land on both sides of the split.
3. `Time` encodes row order — validation split must not implicitly leak
   future-fraud patterns backward; addressed in `/ds-validate`.

## Figures
- `.last-ds-mile/figures/02-class-distribution.png` — class imbalance (log
  scale).
- `.last-ds-mile/figures/02-v14-by-class.png` — density of `V14` by class,
  the strongest single-feature separator.
