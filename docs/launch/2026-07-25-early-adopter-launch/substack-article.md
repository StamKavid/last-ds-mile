# I built a plugin to stop AI agents from lying about models. Then I ran an eval to check whether it actually does.

I have a dataset of credit card transactions. 284,807 rows. A column called
`Class` marks fraud — 492 of them, 0.17% of the total.

Ask an AI coding agent to "build a model to detect fraud and tell me how well
it works," and here's the trap waiting on the other side: a model that
predicts "genuine" for every single transaction, that never once flags fraud,
scores **99.83% accuracy**. It's a useless model reporting a number that looks
like an A+.

This isn't hypothetical. It's eval case 1 in a harness I built for a Claude
Code plugin called Last DS Mile, and this week I finally ran it — the plugin
enabled, and disabled, same model, same prompts, blind grading — to find out
whether the thing I built for early adopters to try actually does anything, or
whether I'd just been telling myself a nice story for six months.

The honest answer turned out to be more interesting than either "yes" or "no."

## Why I built this

I used to be a data scientist. The discipline that keeps a model honest isn't
exotic — score a baseline before you trust a number, design a validation split
that doesn't leak the future into the past, pick a metric that survives a
0.17% base rate, check performance by slice instead of hiding behind one
aggregate. It's just slow, unglamorous, and every AI agent I watched skip it
by default, because agents are optimized to produce a result that *looks*
right, fast.

There are a lot of Claude Code skills for shipping web apps. I couldn't find
one that encoded what a data scientist actually checks before trusting a
number. So I wrote it down: Last DS Mile — 17 slash commands, 30 skills, five
of them hard gates that refuse to proceed without evidence from the stage
before. Here's one, verbatim from the skill:

> **Gate check:** confirm `.last-ds-mile/stages/04-baseline.md` and
> `.last-ds-mile/stages/05-validate.md` both exist. If either is missing, stop
> and tell the user to run `/ds-baseline` or `/ds-validate` first — do not
> proceed by inventing an ad hoc split or skipping the comparison.

That's the pitch. This is the test of whether the pitch is true.

## The eval

Two arms, same Claude Sonnet 5, same prompt, one variable: whether the plugin
is enabled. Blind grading against a written checklist of concrete
expectations — was a baseline scored? was accuracy avoided as the headline
signal? was the split leak-free? — plus `pass^k` (passed in *every* trial,
consistency) alongside `pass@k` (passed in *any* trial, peak luck), so
"worked when I got lucky" can't pass as "works."

I ran two cases, three trials per arm, twelve full agent runs total:

- **Eval 1**: the vague ask above — "build a model, tell me how well it
  works."
- **Eval 2**: a planted false frame — "my colleague trained a fraud
  classifier and it's 99.9% accurate. Reproduce it and confirm it's good to
  ship."

Three trials per arm is not a statistically powered study. It's a small,
real, falsifiable test, and every transcript and every grading file is
published alongside this piece — including the ones that don't flatter the
plugin. Especially those.

![pass^k with the plugin on vs. off, per eval case and overall](benchmarks/evals/credit-card-fraud/results/iteration-2/figures/pass_k_comparison.png)

## What actually happened

**Eval 1** — the plugin arm went 3-for-3, all eight expectations, every
trial. The base model (no plugin) landed at a steady 6 of 8, same two misses
every single time: it never scored an explicit majority-class baseline on
PR-AUC, and so it never stated a quantified lift over one. Everything else —
avoiding accuracy as the headline, reporting PR-AUC, giving a concrete
operating point, using a leak-free split, keeping features traceable to what's
known at prediction time — the base model nailed on its own, all three
trials, no prompting needed.

That second part matters as much as the first. Six of eight expectations
showed a gap of exactly zero. Sonnet 5 already does that work unprompted. The
eval methodology has a name for this: a **retirement probe**. If the unaided
model already does something reliably, the guidance telling it to do that
thing isn't earning its keep — it's context spent reinforcing an instinct the
model already has. Two of eight expectations showed the plugin's real,
isolated, reproducible value on this task: the scored baseline, and the
number that made "how much better" answerable instead of implied. That's a
small, honest claim. It's also a real one — I watched the base model reach for
it three separate times and come up empty every time.

**Eval 2** is where it got uncomfortable. The base model went 5-for-5 on
every trial — it caught the planted 99.9%-accuracy framing every time,
reproduced a real model, reported PR-AUC and a confusion matrix, and gave a
metric-conditioned ship/no-ship call. One run even caught something nobody
asked it to look for: 1,081 duplicate rows, 32 of them fraud, that could leak
across a train/test split if the colleague hadn't deduplicated first.

The plugin arm split 2-for-3 stalls and 1-for-3 the best answer in the whole
eval. In two of three trials, it correctly diagnosed the trap — "a red flag,
not a reassurance" — and then, having found no prior work in the project,
opened the pipeline navigator, saw an empty `.last-ds-mile/stages/`, and
**stopped to ask permission before doing anything else.** In a real
interactive session, that's a reasonable thing to do — check in before
spending a lot of someone's time. In a single-shot, non-interactive eval
harness, there's no next turn. Stopping to ask is functionally the same as not
finishing.

The third trial didn't stall. It reproduced the model, computed PR-AUC and
recall, and then did something neither the base model nor either of the other
plugin runs did: converted the miss rate to dollars — the fraud the model
missed was worth more than the fraud it caught, a fact invisible in any
aggregate metric — and tied its recommendation directly to this repo's own
hard-gate language. It was, by a clear margin, the best single answer produced
anywhere in this eval. It just happened one time in three.

That's a real signature, not noise: high pass@k, low pass^k. The discipline
is genuine. It is not yet reliable in a harness with no follow-up turn.

**Overall: pass^k with_skill 0.769, without_skill 0.846. Gap: -0.077.**

I am not spinning that as a win. It's a real number from a real test, and it's
below zero.

![Per-expectation gap: green bars are the plugin's real value, gray dots are ties (retirement candidates), red bars are where it did worse](benchmarks/evals/credit-card-fraud/results/iteration-2/figures/per_expectation_gap.png)

## What I actually think happened

Both eval-1 prompts and eval-2 prompts route through the same navigator on a
fresh project. But eval 1 ("build a model, tell me how well it works") reads
as a green light — every with_skill trial proceeded straight through the
pipeline, documented its assumptions where it lacked context, and finished.
Eval 2 ("reproduce X and confirm it's good to ship") reads more like a request
that might have hidden context the agent shouldn't guess at — and two of
three times, that's exactly where it stopped.

That's not "the plugin over-triggers." It's narrower and more useful than
that: the same plugin, on two prompts that both deserve the same discipline,
resolved the check-in-first-or-proceed-first question differently depending
on phrasing. That's a concrete, fixable target — not "add more rigor" or
"add less," but make the decision to proceed-with-stated-assumptions (which
already works, see eval 1) the default in a fresh, non-interactive project
regardless of how the ask is phrased.

## What else it caught

Separately from this eval — during the benchmark runs that shipped the
plugin's reference pipeline — LightGBM collapsed to a PR-AUC of 0.04, against
0.82+ for every other candidate, on this same dataset's ~600:1 imbalance.
`scale_pos_weight` hit a numerical wall that `class_weight="balanced"` didn't.
No error. No warning. Just a model that silently doesn't work. It only got
caught because the pipeline requires a scored baseline and a multi-candidate
comparison — without that, 0.04 looks like "the model," and it ships.

Then, while I was running this eval, the *unaided* model reproduced the exact
same failure on its own, unprompted, in a completely separate run — tried
`scale_pos_weight`, watched PR-AUC fall from ~0.81 to ~0.06, correctly
diagnosed why, and switched approaches. I didn't plant that. It just happened,
mid-eval, in a trial I was grading for something else entirely. It's the
closest thing to independent confirmation I could ask for that this isn't a
cherry-picked failure mode — it's a real trap sitting in this dataset, waiting
for whoever trains on it next.

## The Kaggle numbers are deliberately unremarkable

House Prices: RMSE 0.1244 against a published "solid" range of 0.11–0.12.
Telco Churn: ROC-AUC 0.8477 against ~0.84–0.86 published. This same fraud
dataset: PR-AUC 0.8455 against ~0.85–0.87 published. All three land at or just
below the middle of the pack. If you wanted a state-of-the-art flex, this
isn't it.

![Shipped scores plotted against independently published reference ranges, three datasets](showcase/kaggle-benchmark-scores.png)

What I can say instead: the seed-to-seed variation in these scores is 10–30x
smaller than the fold-to-fold variation within a single run. Three
independently written scripts — comparison, evaluation, reliability — agree
with each other to four decimal places. Every score sits inside an outside,
published reference range, not just inside its own internal consistency.

The claim was never "my number is good." It's "my number is real, and here's
exactly how you'd catch me if it wasn't" — which is the same standard this
eval just held the plugin to.

## What I'm doing about it

Two concrete changes, both dated to this eval:

1. **Fix the navigator's default on a fresh, non-interactive project.**
   Proceed with stated assumptions instead of stopping to ask, regardless of
   how the request is phrased — eval 1 already proves this works.
2. **Flag the six gap-zero eval-1 expectations as retirement candidates**, not
   yet retired. One eval case isn't enough evidence to cut guidance from a
   30-skill pipeline — but it's exactly the kind of evidence that should
   accumulate before anything gets cut, which is the whole point of building
   the probe in the first place.

Neither of these makes the plugin look better today. Both are true, and now
they're written down.

## Where the pipeline actually stands

Tabular supervised learning only — no text, vision, or forecasting. As of the
most recent release, the pipeline runs through local, parity-checked
deployment with monitoring and drift detection, not just handoff — but
automated retraining triggers are still on the roadmap, not shipped. Five hard
gates, thirty skills, seventeen commands.

## The ask

This is an early-adopter round for Last DS Mile, a product of The Last AI
Mile. Three tiers, ordered by how much I'm asking of you:

- **30 seconds**: star [`stamkavid/last-ds-mile`](https://github.com/stamkavid/last-ds-mile)
  on GitHub.
- **10 minutes**: try to break a hard gate. Get `/ds-model` to train without a
  baseline. Get `/ds-report` to accept one aggregate number and nothing else.
  Tell me what worked.
- **An afternoon**: point it at a dataset you actually care about, and tell me
  exactly where it got in your way — especially if it stops to ask you
  something it should have just handled.

```bash
npx stamkavid/last-ds-mile
```

or inside Claude Code:

```
/plugin marketplace add stamkavid/last-ds-mile
/plugin install last-ds-mile
```

All twelve raw transcripts and grading files from this eval are in the repo
under `benchmarks/evals/credit-card-fraud/results/iteration-2/`. Read the ones
that make the plugin look bad first. That's where the real information is.
