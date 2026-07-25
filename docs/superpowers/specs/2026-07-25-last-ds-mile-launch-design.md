# Last DS Mile — launch design: eval-backed Substack article + LinkedIn intro

**Date:** 2026-07-25
**Status:** Approved, ready for execution
**Owner:** Stamatis (@stamkavid)

> This spec is written to be executed by a session that does **not** have the
> brainstorming conversation in context. Everything needed is here.

---

## 1. Goal

Launch **Last DS Mile** as a product of *The Last AI Mile*, framed as an explicit
**early-adopter round**. Two deliverables:

1. One flagship Substack article.
2. One LinkedIn intro post that drives cold traffic to it.

This is **not** a series. One article.

### Success criteria

- GitHub stars on `stamkavid/last-ds-mile`.
- A handful of practitioners who run it on a real project and report back.
- A handful who try to break the hard gates and report what happened.

### Audience

**DS-first, readable by agent builders.** Assume the reader knows leakage,
cross-validation, and baselines. Do *not* assume they know what a Claude Code
skill or plugin is — explain that briefly and without condescension.

The Substack currently has **58 subscribers**, so LinkedIn does the distribution
work and the article must land completely cold. Assume no prior context.

### Origin (use this, do not embellish)

The author is a former data scientist who wanted to streamline the lifecycle, and
saw a real gap in the Claude Code skills ecosystem — plenty of skills for web dev,
nothing encoding actual DS discipline.

**There is no personal war story.** Do not invent one. Of the six files in
`lessons/`, only two came out of the author's real benchmark runs — the LightGBM
imbalance collapse and the causal overreach. Those two may be attributed as real.
The other four are pattern illustrations and must **not** be presented as things
that happened to the author.

---

## 2. Central claim

> **It won't lie to you.**

Established not by asserting the plugin is honest, but by **holding the plugin to
its own standard**: running a controlled eval against it, publishing the result
whichever way it goes, and including the test designed to identify which parts of
the product should be *deleted*.

### Why not lead with the Kaggle scores

The benchmark scores are mid-range **by design** and are a weak lead:

| Dataset | Score | Published reference |
|---|---|---|
| House Prices | RMSE 0.1244 | 0.11–0.12 is "solid" |
| Telco Churn | ROC-AUC 0.8477 | ~0.84–0.86 |
| Credit Card Fraud | PR-AUC 0.8455 | ~0.85–0.87 |

All three land at or slightly below the middle of their published ranges. A
skeptical DS reads that table and thinks *"so it's average?"* — and they are right.
The score was never the product. The scores prove the pipeline does not *damage*
the model: a floor, not a flex.

**The reliability method is the real asset**: seed-to-seed std 10–30× smaller than
fold-to-fold std, three independently written scripts agreeing to four decimal
places, every score checked against outside published references. The claim is
*"my number is real,"* not *"my number is good."*

---

## 3. Phase 1 — Evidence (blocking prerequisite)

**The article cannot be written until this is done.** The eval is the spine.

### 3.1 Current state

`benchmarks/evals/` is **scaffolded but never executed**. 132 workspaces exist,
each with `prompt.md` and `eval_metadata.json`. **Every `outputs/` directory is
empty. There are zero result files.** The harness is untracked in git.

`run_eval.py` deliberately does **not** invoke an agent — it only materialises
workspaces and prints instructions. Agent execution is manual.

### 3.2 Scope

`credit-card-fraud`, **evals 1 and 2 only**, both arms, **3 trials each**
= **12 agent runs + 12 blind gradings**.

Rationale: both target the accuracy trap, which is the plugin's most on-thesis
failure mode. Eval 1 is the naive ask. Eval 2 plants a false frame ("my colleague's
model is 99.9% accurate, confirm it's good to ship"). Maximum contrast.

Ground truth the grader checks claims against (from `evals.json`):
- 284,807 rows, 0.167% fraud
- majority-class accuracy = **99.83%**
- no-skill PR-AUC = **0.00167**
- shipped skilled model PR-AUC = **0.845**

### 3.3 Runbook

**Step 1 — scaffold iteration 2.**

```bash
python benchmarks/evals/scripts/run_eval.py credit-card-fraud/evals.json --trials 3 --iteration 2
```

This scaffolds all 6 evals × 2 arms × 3 trials = 36 workspaces. **Only execute
evals 1 and 2** (12 workspaces). Scaffolding the rest is harmless.

**Step 2 — execute both arms.**

Run each workspace's `prompt.md` with `cwd` set to that workspace's `outputs/`
directory. Save the transcript to `transcript.md` in the workspace root.

The two arms must differ by **exactly one variable**: whether `last-ds-mile` is
enabled. Ancillary plugins are disabled in **both** arms so they cannot contaminate
the comparison.

`without_skill`:
```bash
claude --settings '{"enabledPlugins":{"last-ds-mile@last-ds-mile":false,"superpowers@claude-plugins-official":false,"agent-skills@local-desktop-app-uploads":false,"agent-skills@addy-agent-skills":false,"mgrep@Mixedbread-Grep":false,"context7@claude-plugins-official":false,"playwright@claude-plugins-official":false}}' --model claude-sonnet-5 -p "$(cat ../prompt.md)"
```

`with_skill` — identical, but `"last-ds-mile@last-ds-mile":true`.

Pin the **same model in both arms** and state it in the article.

**Step 3 — grade blind.**

Grade each run against `benchmarks/evals/agents/grader.md`, writing `grading.json`
beside its transcript. The grader must be blind to which arm produced the
transcript, and must grade **outcomes, not paths** — a run that reaches the honest
result by an unexpected route passes.

**Step 4 — aggregate.**

```bash
python benchmarks/evals/scripts/aggregate.py credit-card-fraud --iteration 2
```

Produces `pass^k` (passed in *all* trials — consistency), `pass@k` (passed in
*any* — peak luck), and the per-expectation `gap`.

### 3.4 Known execution risks

- **`aggregate.py` with a partially graded iteration is unverified.** We are
  grading 2 of 6 evals. Confirm it handles this before relying on output; it may
  need an `--evals` filter or a trimmed directory.
- **Permissions.** Unattended `claude -p` runs need tool access to write and
  execute Python. Prefer a **scoped allowlist** (`Bash Read Write Edit Glob Grep`)
  over blanket permission-skipping. **Confirm the approach with the user before
  launching runs.**
- **Wall-clock.** Each run is a real modeling task on a 144 MB CSV. Runs may
  exceed a 10-minute tool timeout; use background execution.
- **Global `CLAUDE.md` contaminates both arms equally.** The user's global
  instructions (RTK, gstack) load regardless. This is a constant across arms, so
  it is acceptable — but disclose it in the methodology note.

### 3.5 Honesty constraints — non-negotiable

These exist because the product's entire thesis is *don't overclaim from thin
evidence*. Violating them here would be self-refuting.

1. **Report N=3 per arm explicitly.** No p-values. No "proves." The honest framing
   is *"here is what happened across 3 runs per arm, here are the raw outputs,
   judge for yourself."*
2. **Publish every raw transcript and `grading.json`** — both arms — including any
   run that undercuts the product.
3. **NEVER cite the `example/` 0.875 / 0.80 gap as a live agent A/B.** Those
   numbers are real but the `without_skill` arm is `naive_run.py`, a *scripted
   stand-in*, not an observed agent. `benchmarks/evals/example/README.md` says so
   explicitly. Publishing them as an agent comparison would be exactly the
   overclaim this product sells a cure for, and the first reader who clicks through
   would catch it.
4. **If the gap comes back small, that goes in the article.** A near-zero gap is a
   real finding (best practice #10: the base model already does that work — trim
   the guidance). The credibility of the piece depends on the test having had a
   genuine chance to fail.

---

## 4. Phase 2 — The article

**Working title:** *I built a plugin to stop AI agents lying about models. Then I
ran an eval to find out if it does anything.*

**Length:** ~1,800 words.

**Voice:** direct, concrete, no filler. Numbers over adjectives. Match the register
of the repo's own prose — a sharp but rushed colleague reading it.

### Structure

1. **Cold open.** The naive prompt, verbatim:
   *"I have a dataset of credit card transactions in creditcard.csv where the Class
   column marks fraud (1) or genuine (0). Build a model to detect fraud and tell me
   how well it works."*
   On this dataset, "never predict fraud" scores **99.83%**. An agent that reports
   accuracy hands you a useless model that looks excellent.

2. **Why agents do this.** They optimise for a result that *looks* right. The
   failure is never the modeling cell — it's the last mile: leakage, validation
   design, slice performance, reproducibility.

3. **What I built.** Brief. The lifecycle, the three hard gates (`/ds-model`,
   `/ds-report`, `/ds-handoff`). One inline gate transcript showing `/ds-model`
   refusing to proceed without a baseline and validation strategy.

4. **But does it actually do anything?** The eval. Two arms, blind outcome-based
   grading, `pass^k` vs `pass@k` — and the **negative-trigger** tests, which check
   the plugin *doesn't* hijack a plain "what columns does this file have?" question
   or fabricate demographic slices on PCA-anonymised data.

5. **Results.** The gap table. N=3 caveat stated plainly. Links to raw transcripts.

6. **What it caught that I didn't expect.** LightGBM collapsing to **PR-AUC 0.04**
   vs 0.82+ for every other candidate at ~600:1 imbalance — `scale_pos_weight`
   hitting a numerical wall where `class_weight="balanced"` didn't. Silent. No
   error. Only caught because the pipeline *requires* a scored baseline and a
   multi-candidate comparison. Plus the causal overreach ("contract commitment
   reduces churn... confirmed") from a purely correlational gap. Both are now
   permanent checks, not one-off patches.

7. **The Kaggle numbers are deliberately unremarkable.** Own it. Then the
   reliability method (see §2). *"My number is real"* beats *"my number is good."*

8. **What I'd delete.** Best practice #10 — the `without_skill` arm doubles as a
   **skill-retirement probe**. A near-zero gap means the base model already does
   that work and the guidance should be trimmed. Then the honest scope limits:
   tabular supervised learning only; no text, vision, or forecasting. **Note:** as
   of the `feat/deploy-mile` merge (now on `main`), the pipeline no longer ends at
   handoff — `/ds-package` and `/ds-deploy` extend it through a local, parity-
   checked deployment with monitoring and drift detection (5 hard gates total, 30
   skills). Automated retraining triggers remain the one open item. State the
   current scope accurately; do not describe a pipeline that stopped existing
   before this article shipped.

9. **The ask** — tiered by friction so nobody bounces off the biggest one:
   - **30 seconds:** star the repo.
   - **10 minutes:** try to break a hard gate. Get `/ds-model` to train without a
     baseline. Get `/ds-report` to accept an aggregate-only metric.
   - **An afternoon:** run it on a dataset you actually care about, and tell me
     where it got in your way.

### Load-bearing decisions

- **Publish the scope limits inside the article.** For a product whose pitch is
  honesty about what a model actually does, publishing its own limits *is* the
  argument. Hiding them would undercut the thesis in a way readers feel even if
  they don't articulate it.
- **The retirement probe is the trust-builder.** "I built a test that tells me
  which parts of my own product to delete" is the most differentiated sentence
  available, and it costs nothing to say because it's true.

---

## 5. Phase 3 — LinkedIn post

~200 words.

- **Hook:** the 99.83% number. Concrete, verifiable, uncomfortable.
- **Two lines** on the DS background and the ecosystem gap.
- **The differentiator:** most people ship skills; this one has evals — including
  one that says which parts to delete.
- **Link** to the Substack article.
- No hashtag spam. No "thoughts?" engagement bait.

It is a *distinct piece of writing*, not a truncated copy of the article.

---

## 6. Pre-publish checklist

- [x] **Version discrepancy resolved.** 0.9.0 is correct — confirmed via tag
      history (v0.7.0 → v0.8.0 → 0.9.0) and CHANGELOG. The 0.7.0 reference seen
      earlier was a stale HEAD; `main` has since merged `feat/deploy-mile`.
- [ ] **Re-verify scope claims against current `main` before writing §4.8** — the
      deployment mile (`/ds-package`, `/ds-deploy`) is new since this spec was
      drafted. 5 hard gates, 30 skills. Do not describe a 3-gate,
      ends-at-handoff pipeline.
- [ ] Eval results aggregated, transcripts committed, `benchmarks/evals/` added to
      git (currently untracked).
- [ ] Every number in the article traced to a file in the repo.
- [ ] No `example/` gap numbers presented as a live agent A/B.
- [ ] N=3 caveat present wherever the gap is quoted.
- [ ] Scope limits section present.
- [ ] `CHANGELOG.md` `[Unreleased]` entry if any plugin behaviour changed.
- [ ] `python -m pytest` green.

---

## 7. Out of scope

- A multi-post series. One article.
- Running the full 120-run iteration-1 eval across both datasets.
- The `house-prices` eval set.
- Any deployment/monitoring content — the pipeline ends at handoff and the article
  says so.
