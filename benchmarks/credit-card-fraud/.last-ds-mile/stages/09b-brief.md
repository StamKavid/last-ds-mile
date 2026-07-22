# Executive Brief — Transaction Fraud Screening Tool

## What we built, and why

A tool that flags card transactions likely to be fraudulent, in real time, so
the fraud-ops team can review them before or shortly after the charge goes
through — this supports the review team's decision, it doesn't block a
transaction on its own.

## How well it works

At the flagging threshold we recommend, the tool catches **83% of fraud
cases**, covering **75% of the dollar amount actually stolen** — while wrongly
flagging only about **1 in every 5,500 genuine transactions**, a very low
false-alarm rate. The 8-point gap between cases caught and dollars caught
comes from a small number of larger-value fraud cases the tool misses more
often than small ones — a specific, narrow gap, not a broad blind spot.

## Where it's weaker

The hardest fraud to catch is small-dollar (often under $10) — these blend in
with the enormous volume of small genuine purchases and are the cases most
likely to slip through. The tool's underlying signals come from a data
provider that anonymized the original transaction details for privacy, so
unlike the other two tools in this review, we can't fully explain *why* it
flags what it flags in plain business terms — only that its judgment lines up
with independent public research on the same kind of data.

## Recommendation

**Deploy as a screening flag with human review, not automated blocking.** The
catch rate and false-alarm rate above are strong enough to support that
recommendation on their own.

## What happens next

Fraud-ops should confirm the review team can handle the flagged-transaction
volume this threshold produces. Fraud patterns shift constantly — this tool
was built on a fixed two-day sample from 2013, so it needs regular retraining
on recent data to stay effective, not a one-time deployment.
