# Executive Brief — House Price Suggestion Tool

## What we built, and why

A tool that suggests a listing price for a home, based on its size, condition,
and other details, so a pricing agent has a fast starting number and can spend
their time on judgment calls instead of manual comps — the agent always has the
final say.

## How well it works

On a typical home, the suggested price is off by about **$21,600** on a home
worth around **$163,500** — roughly a **13% typical difference**. That's close
to, but not clearly better than, what an experienced agent already achieves by
eye. This tool's real value is speed and consistency, not a dramatic accuracy
advantage over a skilled human.

## Where it's weaker

On the least expensive homes (roughly under $130,000), the tool's typical error
is closer to **19%** — at that price point, it may not beat an agent's own
judgment at all. Two very unusual historical sales (large, high-quality homes
that sold far below what their size and condition would suggest, for reasons
tied to those specific properties) also throw off the tool's suggestions for
any similar future listing — a known, narrow blind spot, not a general weakness.

## Recommendation

**Use the suggested price as a starting point, not the final number** — and
weight the agent's own judgment most heavily on the cheapest listings, where the
tool is least reliable.

## What happens next

The pricing team should decide who owns final sign-off on listing price (the
tool never should). Two things would need to stay true for this recommendation
to hold: the housing market should resemble the 2006–2010 period this tool
learned from (a real shift in the market would call for retraining), and the
tool should stay a suggestion an agent can override, never an automated price.
