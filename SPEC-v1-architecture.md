# SPEC — v1.0 architecture rework

Status: **draft, awaiting approval.**
Supersedes nothing — `SPEC.md` (the deployment mile) shipped in 0.8.0/0.9.0 and stays as history.

Scope: restructure the plugin so the discipline it encodes survives contact with a
single-shot request, costs a defensible multiple of the unaided model, and can be
regression-tested for free in CI. Driven by
[`benchmarks/evals/credit-card-fraud/results/iteration-2/`](benchmarks/evals/credit-card-fraud/results/iteration-2/),
where `with_skill` lost to the unaided base model (pass^k 0.769 vs 0.846) at 4.25× the cost.

---

## 1. Objective

**What we're building.** Three separations that the current architecture fuses:

| Concern | Current home | New home |
|---|---|---|
| **Discipline** — what "good" means | stateful skill that requires a prior stage's artifact | stateless skill, applies anywhere, no prior-artifact requirement |
| **Sequence** — what order, where to stop | encoded inside skill Hard Gates → deadlock | command file with explicit orchestration and stop conditions |
| **Shared rules** — Red Flags, Rationalizations | `ds-method` *skill* → competes for triggers, loads via skill mechanism | `references/discipline.md` → loaded on demand, never routed to |

**What we're not building.** No runtime, no Python package, no new pipeline stages, no
scope expansion. The product stays Markdown. This is subtraction and re-wiring.

**Definition of done.** The exit criteria in §7 are met on a clean iteration-3 run.

---

## 2. Prior art — what `addyosmani/agent-skills` does differently

Reverse-engineered from the repo at `HEAD` (24 skills, 4 agents, 7 shared references,
8 commands × 5 platforms, 3-tier eval harness).

### 2.1 Fewer, bigger skills

| | agent-skills | last-ds-mile |
|---|---|---|
| Skills | 24 | 30 |
| Median `SKILL.md` | ~11 KB | ~5 KB |
| Range | 7.6 – 20.5 KB | 2.6 – 8.6 KB |
| Always-on description index | ~2.4 K tokens | ~2.0 K tokens |

The counterintuitive finding: **the more successful pack has bigger skill files and fewer
of them.** Their unit of a skill is *a discipline you apply* (`test-driven-development`,
`security-and-hardening`). Ours is *a step you perform* (`ds-prep`, `ds-validate`,
`ds-explore`). Steps are ordered, so they acquire prerequisites, so they deadlock. Disciplines
are not ordered, so they compose.

`skills/code-review-and-quality/SKILL.md` is 20 KB and carries five review axes inline.
We would have shipped that as five skills. Five skills means five descriptions competing
in the same trigger space — which is exactly why the eval-2 run picked `/ds` over
`data-science-project`.

### 2.2 Sequence lives in commands, not skills

`.claude/commands/build.md` is where multi-step carry-through lives, and it is explicit:

- `/build` → one task, then stop. `/build auto` → the whole plan.
- **One human gate, at a named point**: *"Present the full plan and wait for an unambiguous
  affirmative… This is the only human gate — after approval, run autonomously."*
- Explicit resume semantics: *"the user re-invokes `/build auto` — it resumes from the next
  pending task."*
- Explicit stop conditions, enumerated: test can't pass, spec ambiguous, irreversible action.
- Explicit precondition handling that **names a path**: *"Look only for a spec at a known
  path: `SPEC.md`, `docs/SPEC.md`, or a file under `spec/`. A README does not count."*

Compare our `commands/ds.md`, which asks the model to infer *why it was invoked*
(*"if this command was reached while carrying out an actual task… vs the user typed `/ds`
directly"*). A command cannot know its own provenance. That conditional reads well and
executes unreliably.

### 2.3 Shared rules are reference files, not a skill

`references/definition-of-done.md`, `security-checklist.md`, etc. live at repo root,
deliberately outside any skill directory, and are linked one level deep from the skills
that need them. `docs/skill-anatomy.md` documents the tradeoff explicitly (portability of
per-skill installs) rather than pretending there isn't one.

Our `ds-method` does the same job but is registered as a *skill* — so it consumes an index
slot, competes for triggers, and is loaded through a mechanism designed for routing rather
than inclusion.

### 2.4 Descriptions are formulaic, on purpose

Every description follows: `<Third-person verb-s> <object>. Use when <A>. Use when <B>. Use when <C>.`

```
description: Guides systematic root-cause debugging. Use when tests fail, builds break,
behavior doesn't match expectations, or you encounter any unexpected error. Use when you
need a systematic approach to finding and fixing the root cause rather than guessing.
```

Repeated `Use when` clauses each pack a *different* slice of user vocabulary. This is
deliberately optimized for the lexical routing check in §2.5. `scripts/lib/skill-lint.js`
enforces it mechanically: max 1024 chars, must match
`/\buse (this )?when\b|\buse (before|after|during)\b/`, negated forms rejected.

Ours are denser em-dash prose with a single trailing `Use when … or when …`. More
information per character, less vocabulary surface — which is the wrong optimization for a
retrieval mechanism.

### 2.5 A three-tier eval harness, two tiers of which are free

From `evals/README.md`:

| Tier | Checks | Runs | Cost |
|---|---|---|---|
| 1. Structural | frontmatter, naming, required sections, command parity | CI | free |
| 2. **Trigger & routing** | positive prompts rank their skill top-k; negative prompts rank their *declared owner* higher; no two descriptions near-collide | CI | **free** |
| 3. Behavioral | an agent following the skill satisfies `expectations[]` | on demand | tokens |

Tier 2 is stemmed TF-IDF cosine over descriptions. It is a lexical approximation and they
say so. It produces two hard numbers:

- **trigger rank-1 rate** — share of positive prompts whose skill ranks *first*. CI floor
  `--min-rank1 80`, checked-in baseline 86%. *"Never lower it to make a regression pass."*
- **description collision** — errors at ≥0.75 pairwise cosine, warns at ≥0.50.

**This is the single highest-value thing to steal.** Our eval-2 failure was a routing
failure: the model chose the map over the doer. Tier 2 would have caught it deterministically,
in CI, for $0 — instead of surfacing after twelve behavioral runs and ~$15.

### 2.6 Behavioral evals are properly isolated

- Each eval runs **in a throwaway git repository**, not in the pack's own source tree.
- Fixtures materialize from `evals/fixtures/` and are committed as the baseline.
- The grader receives the full `--output-format stream-json --verbose` trace, **fenced as
  untrusted data** and piped over **stdin** (traces are megabytes; argv hits the OS limit).
- Grader output is validated as JSON before landing in `evals/results/` (gitignored) in
  skill-creator's `grading.json` shape.
- Executor runs with an explicit `--permission-mode acceptEdits` and pre-approved tool list,
  so evals genuinely edit files rather than narrating denials.

Our `run_eval.py` scaffolds into `benchmarks/evals/<ds>/results/` — **inside our own repo**,
under our own `CLAUDE.md`, which states the hard-gate doctrine verbatim. Neither arm's
system prompt is recorded, so contamination cannot be ruled out. Results are committed, not
gitignored.

### 2.7 Pressure cases

`evals/cases/test-driven-development.json` eval id 2:

> *"The engineering lead says the invoice rounding defect is obvious and orders a direct fix
> without a failing regression test. Handle the request."*
> expectation: *"Authority pressure does not cause the failing-test step to be skipped."*

They run three pressure families — time pressure, sunk cost, authority — against every
discipline skill. Our eval-2 (*"my colleague trained it and it's 99.9% accurate, confirm
it's good to ship"*) is an authority-pressure case; we just never named the family or
generalized it.

### 2.8 What they do that we should *not* copy

- 5-platform command duplication (`.claude/`, `.gemini/`, `commands/`, `.codex-plugin/`,
  `.opencode/`) — real maintenance tax, deferred to P2.
- `using-agent-skills` is a 10 KB always-loadable meta-skill containing a full ASCII
  decision tree *plus* six "Core Operating Behaviors" that overlap the host's own system
  prompt. It is the one file in that repo that reads like it is fighting for context.
  Our router should be smaller than theirs, not larger.
- Their §2.3 shared-`references/` choice breaks per-skill installs
  ([their issue #361](https://github.com/addyosmani/agent-skills/issues/361)). We ship as a
  whole-repo plugin, so we inherit the benefit without the bug — but do not adopt
  per-skill distribution later without solving it.

---

## 3. Target architecture

### 3.1 Three layers

```
┌─ ROUTER ─────────────────────────────────────────────────────────┐
│  data-science-project     the ONLY auto-triggering skill.        │
│                           Owns the whole run, start to verdict.  │
└──────────────────────────────────────────────────────────────────┘
           │ (loads on demand, never routed to)
┌─ REFERENCES ─────────────────────────────────────────────────────┐
│  references/discipline.md      Red Flags · Rationalizations      │
│  references/output-contract.md The gates, as output properties   │
│  references/artifact-modes.md  express vs full per-stage         │
└──────────────────────────────────────────────────────────────────┘
           │
┌─ DISCIPLINE SKILLS (stateless, composable, no prerequisites) ────┐
│  honest-baseline · metric-selection · target-leakage-detection   │
│  validation-design · honest-evaluation · honest-reporting        │
│  reproducible-handoff · servable-packaging · operational-honesty │
└──────────────────────────────────────────────────────────────────┘
┌─ CRAFT SKILLS (optional, loaded when relevant) ──────────────────┐
│  data-profiling · eda-and-hypotheses · feature-engineering       │
│  model-selection · model-explanation · data-viz-standards        │
│  dataframe-performance · capturing-learnings                     │
└──────────────────────────────────────────────────────────────────┘
```

**One auto-trigger.** `data-science-project` fires on a tabular-ML ask and carries it to a
verdict. `/ds` becomes map-only and is never routed *through*. Every `/ds-*` command remains
as an explicit manual entry point into its discipline skill.

### 3.2 Gates restated as output properties

The load-bearing change. Current form is a precondition on the **input**:

> `/ds-model` requires a baseline artifact from `/ds-baseline` … to exist before modeling.

In a single-shot invocation no prior stage exists, the gate is unsatisfiable, and the run
stops. New form constrains the **output**:

> **The final answer must contain** a scored dumb baseline and the model's lift over it.
> **The final answer must contain** the headline metric at a stated operating point, and
> broken out by at least one slice. **A handoff must contain** a pinned environment.

An output contract cannot deadlock, because nothing upstream has to exist for it to be
satisfiable — it only has to be *produced*. `references/output-contract.md` is the single
home for these; skills cite it, none restate it.

**Safety gates keep stop-and-ask, unchanged**: a failing training/serving parity check, and
any push to a remote / registry / cloud target. These are irreversible or externally visible,
so continuing unilaterally isn't the agent's call. This preserves the CLAUDE.md hard rule.

### 3.3 Skill consolidation

Target **18 skills**, down from 30. Merges are grouped by the collision they resolve:

| Merge into | Absorbs | Why |
|---|---|---|
| `validation-design` | `ds-validate`, `validation-strategy`, `distribution-shift` | `ds-validate` and `validation-strategy` are near-duplicate descriptions ("setting up train/test splits, cross-validation") |
| `metric-selection` | `imbalanced-data` | both claim "metric choice for imbalanced classification" |
| `honest-evaluation` | `ds-evaluate`, `error-analysis`, `ds-iterate` | all claim "after evaluation / slice performance"; iterate is a decision, not a stage |
| `honest-reporting` | `ds-report`, `ds-brief`, `causal-vs-predictive` | one audience-facing narrative skill with a causal-overreach guard |
| `reproducible-handoff` | `ds-handoff`, `notebook-hygiene` | same concern: can someone else rerun this |
| `model-selection` | `ds-model`, `model-ensembling` | ensembling is a lever inside model selection |
| `target-leakage-detection` | `ds-frame`'s information inventory | the inventory *is* framing-time leakage detection |
| `references/discipline.md` | `ds-method` | shared rules are an include, not a route |
| `references/output-contract.md` | `uncertainty-quantification` | "report variance with every metric" is a contract clause, not a skill |

**These merges are proposals, not decisions.** Phase 1 builds the Tier-2 collision check
and runs it against the current 30 descriptions; the collision matrix decides. Any pair
above 0.75 cosine merges or gets rewritten. Any merge the matrix does *not* justify gets
dropped from this list.

> ### ⛔ Checkpoint 2 outcome — this section is superseded
>
> The matrix ran ([`benchmarks/evals/routing-baseline.md`](benchmarks/evals/routing-baseline.md))
> and **falsified the merge case**. Exactly one skill pair exceeds 0.50 cosine
> (`ds-validate ↔ validation-strategy`, 0.546); **zero** reach the 0.75 error line. The
> thirty descriptions barely overlap.
>
> The measured defect is elsewhere: **rank-1 routing is 47.8%** against a reference floor
> of 80%. Descriptions are written in author vocabulary while users speak user vocabulary,
> so skills are unreachable rather than confused with each other. `metric-selection` ranks
> **#44 of 47** for *"is accuracy the right thing to report"*; `imbalanced-data` ranks
> **#41** for *"only 0.2% of my rows are positive"* — the pack's two core claims on its own
> flagship dataset. Merging would not have moved either.
>
> **Decision (approved):** Phase 3 rewrites all descriptions and performs exactly one
> merge — `validation-strategy` into `ds-validate`. Every other merge in the table above is
> dropped. No skill is renamed, so no `/ds-*` command, README row, or external link breaks.
> Target: 30 → 29 skills, rank-1 47.8% → ≥80%.
>
> Further consolidation stays available, but must be argued from evidence in a later
> iteration rather than from the architectural intuition that produced this table.

### 3.4 Artifact mode becomes mechanical

Current: the model must *infer* whether a request is "single-shot" (express) or a "genuine
multi-session project" (full per-stage). That is another unreliable conditional.

New rule, decidable without judgment:

> Full per-stage `.last-ds-mile/stages/NN-*.md` **iff** `.last-ds-mile/stages/` already
> contains at least one file, **or** the user invoked a specific `/ds-<stage>` command.
> Otherwise a single `.last-ds-mile/run.md`.

### 3.5 Description rewrite

All 18 descriptions move to the enforced formula:

```
<Third-person verb-s> <object>. Use when <A>. Use when <B>. Use when <C>.
```

with ≥2 `Use when` clauses carrying *distinct* user vocabulary, ≤1024 chars, no negated
trigger forms. Enforced by Tier 1, scored by Tier 2.

---

## 4. Eval architecture

### 4.1 Tier 1 — structural (extend existing pytest)

`tests/test_plugin_structure.py` already covers frontmatter shape and command↔skill wiring
(113 tests currently green). Add:

- description ≤ 1024 chars; matches the trigger regex; rejects negated trigger forms
- required sections present: Overview · When to Use · Common Rationalizations · Red Flags · Verification
- frontmatter `name` matches directory name, kebab-case
- cross-skill references resolve to a real skill (`see \`x\``, `use the \`x\` skill`, …)
- reference-file links resolve and are **one level deep** (no `SKILL.md` → ref → ref chains)
- exemptions live in the test file, not in skill frontmatter, each with a written reason

### 4.2 Tier 2 — trigger & routing (new, free, CI)

Port `scripts/run-evals.js`'s scorer to **stdlib-only Python** (the repo has no lockfile and
`pyyaml`/`pytest` are the only test deps — keep it that way).

- Corpus = the 18 descriptions. Tokenize → light stem → TF-IDF → cosine.
- Per-skill case file `benchmarks/evals/cases/<skill>.json`:
  ```json
  {
    "skill_name": "honest-baseline",
    "trigger": {
      "positive": [{ "prompt": "just train a quick model on this csv", "top_k": 3 }],
      "negative": [{ "prompt": "what columns does this file have", "owner": "data-profiling" }]
    }
  }
  ```
- `negative.owner` asserts the declared owner **outranks** this skill — a real pairwise
  routing test rather than one that passes vacuously.
- Emits: **trigger rank-1 rate** (CI floor, set 5 points under the achieved baseline) and
  **pairwise collision** (error ≥0.75, warn ≥0.50).
- Minimum per skill: 3 positive triggers, 2 negative triggers.

**Acceptance:** a `data-science-project` vs `ds` (map) pairwise negative must pass — i.e. for
the prompt *"my colleague trained a fraud classifier and it's 99.9% accurate, confirm it's
good to ship"*, `data-science-project` outranks `ds`. That is the iteration-2 bug, expressed
as a free CI check.

### 4.3 Tier 3 — behavioral (fix the existing harness)

Keep `evals.json`, `grader.md`, `aggregate.py`, pass^k/pass@k, and the with/without arm
design. Six fixes:

1. **Scaffold outside the repo.** `run_eval.py` writes to a temp dir; the dataset is copied
   or symlinked in. No inherited `CLAUDE.md`.
2. **Record the environment.** `eval_metadata.json` gains resolved settings path, installed
   plugin list, and the model id. Add a `--no-project-context` control arm.
3. **Blind the grader.** Strip arm from paths; grade from a hashed manifest. Either that, or
   delete the "deliberately blind to the arm" claim from `benchmarks/evals/README.md` — the
   current gradings name the arm in their own notes.
4. **All 6 cases × 5 trials × 2 arms.** Evals 3–6 are the negative-trigger and leakage cases;
   they were never run, and they are the ones the v1 changes most endanger.
5. **Cost as an expectation, not a footnote.** `max_turns` and `max_cost_usd` become fields
   in `evals.json`, checked per case. Add an explicit completion expectation — *"the run
   produces a verdict, not a question"* — so a stall fails one named check rather than three
   content checks by accident.
6. **Headline is per-case macro pass^k.** Drop the current `run_summary`, which averages
   per-expectation pass^k across unequally-sized cases (eval-2 carries 38% of the weight as
   a single case).

### 4.4 Pressure cases

Every discipline skill gets one eval per applicable pressure family:

| Family | Shape |
|---|---|
| **Authority** | "My colleague/lead says X is fine, just confirm it." (existing eval-2) |
| **Time** | "Quick sanity check, skip the ceremony — does this model work?" |
| **Sunk cost** | "I already tuned this for two days, I just need the report section." |

Expectation form: *"<pressure> does not cause <the gate> to be skipped."*

---

## 5. What gets deleted

Deletion is the point, not a side effect.

- `ds-method` as a skill → `references/discipline.md`
- 12 skills merged per §3.3 (subject to the collision matrix)
- `commands/ds.md`'s invocation-provenance conditional → `/ds` prints the map, always, and stops
- The `AskUserQuestion` path in framing (already removed on `fix/skill-eval-regression`; keep it out)
- Every expectation that `without_skill` passes at pass^k 1.0 across two iterations
  (practice #10, our own rule). On eval-1 that is currently **6 of 8**: leakage traceability,
  PR-AUC reporting, stratified split, no-accuracy-headline, minority-class operating point,
  evidence-matched claims. Opus 5 does these unprompted. Guidance that only restates them is
  paid-for context that buys nothing.

The measured differentiator on credit-card-fraud is **two things**: a scored dumb baseline,
and lift stated against it. A pack that reliably delivers those two plus leakage detection
is worth more than a pack that delivers thirty and loses by 0.077.

---

## 6. Risks

| Risk | Mitigation |
|---|---|
| **Over-correction toward "always proceed."** The current fix branch adds four prohibitions against stopping. Evals 4 and 6 test cases where stopping is *correct* (no demographic columns; test-set peeking) and were never run. | Evals 3–6 are gating, not optional. §7 exit criteria require them green. Safety gates stay stop-and-ask. |
| **Merging loses real distinctions.** `distribution-shift` and `validation-design` are not obviously the same skill. | The collision matrix decides, not this document. Merges below 0.75 cosine get dropped. |
| **Tier 2 is lexical, not semantic.** It cannot judge meaning. | Stated as a known limitation, same as upstream. It catches the two failure modes that dominate — missing vocabulary and over-broad descriptions. Tier 3 judges semantics. |
| **Bigger skill files reverse "keep SKILL.md small."** | The 500-line / 5 K-token guidance is per-file and stays satisfied at ~12 KB. The real budget is *how many files a single run loads*: currently 8+, target ≤3. Consolidation reduces total resident context even as per-file size rises. |
| **Rewriting 30 skills is a large diff with no behavioral test until the end.** | Phase order in the plan puts Tier 1 + Tier 2 first, so every subsequent phase has a free regression check. Tier 3 runs once per phase boundary, not per edit. |

---

## 7. Exit criteria — "shippable" as v1.0.0

All eight, on a clean iteration-3:

1. `pytest` green, including the new Tier-1 rules.
2. Tier-2 trigger rank-1 rate ≥ **80%**, no pairwise description collision ≥ 0.75.
3. The `data-science-project` vs `ds` pairwise negative (§4.2) passes.
4. All **6 eval cases × 5 trials × 2 arms**, scaffolded outside the repo, blind-graded.
5. Per-case macro pass^k gap ≥ **+0.15** in favour of `with_skill`.
6. **No case regresses.** Evals 3, 4, 6 (negative-trigger, hallucinated-slice, test-set-peek)
   at `with_skill` pass^k ≥ 0.8.
7. `with_skill` mean cost ≤ **2×** `without_skill` on **every** case, not just in aggregate.
8. `benchmarks/evals/README.md`'s methodology claims are true as written — specifically the
   blind-grader claim and the trials-per-case claim.

Criterion 8 is not bureaucratic. This plugin's entire proposition is honesty in how results
are reported. An overclaim in its own methodology doc is the one bug it cannot ship.

---

## 8. Open questions for the human

1. **Version.** Is this `1.0.0` (breaking: skills renamed and removed) or `0.10.0`? Renaming
   `ds-baseline` → `honest-baseline` breaks anyone's muscle memory and any doc linking to it.
   Alternative: keep `/ds-*` command names as stable aliases over renamed skills.
2. **Cross-platform (P2).** `benchmarks/evals/README.md` already claims practice #8
   ("test across harnesses") and cites GPT-via-Copilot feedback. Do we ship Gemini/Codex
   command variants in v1, or drop the claim until we do?
3. **Merge aggressiveness.** If the collision matrix justifies only 4 of the 9 proposed
   merges, do we ship 25 skills, or force the rest on architectural grounds?
