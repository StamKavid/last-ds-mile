# Executive Brief — Customer Retention Targeting Tool

## What we built, and why

A tool that scores each customer by how likely they are to cancel their
service this cycle, so the retention team can decide who to call before they
leave rather than after — today, outreach is either untargeted or based on
simple rules that miss less obvious warning signs.

## How well it works

At the outreach volume we recommend, the tool catches **9 out of 10 customers**
who are about to cancel, covering **92% of the monthly revenue** that's
actually at risk. To do that, it flags about **3,800 customers per billing
cycle** for a retention call — of those, only about **45% would actually have
cancelled**, meaning most calls go to customers who weren't leaving anyway.
That trade-off (catch nearly everyone, at the cost of some unnecessary calls)
is a deliberate choice, not a flaw — it can be dialed back toward fewer, more
targeted calls if outreach capacity is tight.

## Where it's weaker

The tool is noticeably less precise for customers already flagged as
high-risk (month-to-month plans, and customers with our higher-priced internet
service) — it correctly identifies these groups as risky overall, but is less
able to tell which *specific* customer within that group will actually leave.
Some clearly loyal-looking, long-time customers cancel anyway, for reasons
nothing in our current customer data explains.

## Recommendation

**Use the score to prioritize this cycle's retention calls**, with the
understanding that roughly half of contacted customers will not have been
about to leave — a cost worth naming to whoever plans the outreach schedule.

## What happens next

The retention team lead should confirm that ~3,800 contacts per cycle fits
within actual outreach capacity, and decide whether that trade-off (near-
complete coverage vs. call volume) is right or should shift toward fewer,
more targeted calls. This is a snapshot of today's customers — it should be
retrained periodically as the customer base and offers change.
