---
title: The Leaderboard That Lied
skills: [validation-strategy]
stages: [ds-validate]
---

# The Leaderboard That Lied

A demand-forecasting competition's internal leaderboard had one team
consistently in first place by a wide margin, using a gradient-boosted model
with heavy feature engineering. When the competition's holdout period
actually arrived — genuinely future data the model had never seen in any form
— that team's model dropped from first to worst, while a simpler model that
had ranked mid-table on the leaderboard held its position almost exactly.

The leaderboard's validation split had been a random K-fold over the entire
historical dataset, which is fine for i.i.d. data but wrong for time-ordered
data: it let the model "see" data from time periods after the ones it was
being scored on, in both directions. The winning-looking model had, without
anyone intending it, been rewarded for interpolating between known future and
past points rather than genuinely forecasting forward — exactly what a real
production forecast can never do.

The fix was a straight swap: `TimeSeriesSplit` (train strictly on the past,
evaluate strictly on the future, expanding window) instead of shuffled
`KFold`. Every model's internal score dropped once the swap was made — the
simpler model's least of all, which is exactly why it had held up.

**Lesson**: a validation split that shuffles time-ordered data doesn't just
add noise, it can silently invert which model actually wins. If the data has
a time dimension, the split must respect it — no exceptions for "it's just
for a leaderboard."
