# PLAN — v1.0 architecture rework

Derived from [SPEC-v1-architecture.md](../SPEC-v1-architecture.md). Status: **awaiting human review.**

Branch: `feat/v1-architecture`, cut from `fix/skill-eval-regression` (its discipline/safety
gate split is load-bearing and gets carried forward, not redone).

**Phase order is the risk control.** Phases 1–2 build free regression checks *before* any
skill is rewritten, so every later phase has a deterministic gate. Behavioral evals
(expensive) run only at ◆ checkpoints, never per-edit.

Legend: ◆ = human checkpoint, stop and review · ⚑ = spends tokens

---

## Phase 0 — Land the pending fix, honestly

The uncommitted work on `fix/skill-eval-regression` is correct in substance and completely
unvalidated. Ship it as an interim fix, labelled as such, so v1 starts from a known state.

- [ ] 0.1 Run `rtk proxy python -m pytest tests/ -q` — confirm 113 green baseline
- [ ] 0.2 Commit the discipline/safety gate split, express mode, stage ladder, one-todo-list
      rule, `ds-frame` no-ask, and agent effort levels as `fix:` commits
- [ ] 0.3 Amend the `[Unreleased]` CHANGELOG entry: state plainly that the fix is
      **unvalidated** — iteration-2 exposed it, iteration-3 has not yet confirmed it.
      Currently the entry reads as though the regression is resolved.
- [ ] 0.4 Cut `feat/v1-architecture`

**Exit:** pytest green, fix committed, CHANGELOG does not overclaim.

---

## Phase 1 — Tier 1 structural rules ⚑free

Extend the existing pytest suite. No skill content changes yet — this phase establishes
what "well-formed" means and will fail loudly against the current 30 skills. That failure
list *is* the Phase 3 worklist.

- [ ] 1.1 `tests/test_skill_lint.py` — description ≤1024 chars; matches
      `\buse (this )?when\b|\buse (before|after|during)\b`; rejects negated trigger forms
- [ ] 1.2 Required sections: Overview · When to Use · Common Rationalizations · Red Flags ·
      Verification. Exemption dict lives in the test file with a written reason per entry,
      never in skill frontmatter
- [ ] 1.3 `name` matches directory, kebab-case
- [ ] 1.4 Cross-skill reference resolution — every `` see `x` ``/`` use the `x` skill ``
      points at a real skill; fenced code blocks stripped before matching
- [ ] 1.5 Reference-link depth ≤ 1 (no `SKILL.md` → ref → ref)
- [ ] 1.6 Command↔skill parity extended to cover the new `references/` layout
- [ ] 1.7 Record the baseline failure count in the test docstring, `xfail` the known
      offenders so CI is green, and delete each `xfail` as Phase 3 fixes it

**Exit:** `pytest` green with a documented `xfail` list. That list is the Phase 3 backlog.

---

## Phase 2 — Tier 2 routing harness ⚑free · **highest value in the plan**

This is the check that would have caught iteration-2's failure deterministically, in CI,
for $0, before twelve behavioral runs and ~$15.

- [ ] 2.1 `benchmarks/evals/scripts/route_check.py` — **stdlib only** (repo has no lockfile;
      `pytest`/`pyyaml` are the only test deps, keep it that way). Tokenize → light stem →
      TF-IDF → cosine, per `scripts/run-evals.js` in the reference repo
- [ ] 2.2 Case schema `benchmarks/evals/cases/<skill>.json` with
      `trigger.positive[{prompt, top_k}]` and `trigger.negative[{prompt, owner}]`
- [ ] 2.3 Write cases for the **current 30 skills** — ≥3 positive, ≥2 negative each.
      Paraphrase how users actually talk; do not copy the description (that games the eval)
- [ ] 2.4 Emit trigger rank-1 rate + pairwise collision matrix; `--min-rank1` flag;
      collision error ≥0.75, warn ≥0.50
- [ ] 2.5 **Run it against today's 30 descriptions. Commit the raw matrix as
      `benchmarks/evals/routing-baseline.md`.** This is the empirical input to §3.3 —
      the merges are decided by this output, not by the SPEC
- [ ] 2.6 Add the specific regression case: prompt *"my colleague trained a fraud classifier
      and it's 99.9% accurate, confirm it's good to ship"* → `data-science-project` must
      outrank `ds`. **Expect this to fail today.** That is the point
- [ ] 2.7 Wire into `.github/workflows/` and `pytest`

◆ **Checkpoint 2** — review the collision matrix together. Confirm or revise the §3.3 merge
list against real numbers. Any proposed merge the matrix does not justify gets dropped.

**Exit:** routing baseline committed; 2.6 documented as a known failure; merge list finalized.

---

## Phase 3 — Restructure ⚑free

Now the skills change, against two free gates.

- [ ] 3.1 `references/discipline.md` — Red Flags + Common Rationalizations, lifted verbatim
      from `ds-method`. Delete `skills/ds-method/`
- [ ] 3.2 `references/output-contract.md` — the gates restated as **output properties**
      (SPEC §3.2). Discipline gates: the answer must contain a scored baseline + lift; a
      stated operating point + ≥1 slice; a pinned environment on handoff. Safety gates
      (parity failure, remote push) stay stop-and-ask, wording unchanged
- [ ] 3.3 `references/artifact-modes.md` — the mechanical express/full rule (SPEC §3.4)
- [ ] 3.4 Execute the confirmed merges. One commit per merge, each citing its cosine score
- [ ] 3.5 Rewrite all descriptions to the enforced formula, ≥2 distinct `Use when` clauses
- [ ] 3.6 Collapse the front door: `data-science-project` is the sole auto-trigger and owns
      the run end to end. Rewrite `commands/ds.md` to print the map and stop, **always** —
      delete the invocation-provenance conditional
- [ ] 3.7 Keep every `/ds-*` command as a stable manual entry point (see open question 1 —
      commands are the compatibility surface even where skills are renamed)
- [ ] 3.8 Retire guidance that only restates what `without_skill` already passes at
      pass^k 1.0 (SPEC §5) — 6 of 8 expectations on eval-1
- [ ] 3.9 Delete `xfail`s from 1.7 as they're fixed; re-run 2.1 after each merge and hold
      rank-1 rate at or above the Phase 2 baseline

◆ **Checkpoint 3** — skill count, total always-on index tokens, rank-1 rate, collision max,
before/after. No tokens spent yet.

**Exit:** ~18 skills; `pytest` green with zero `xfail`; rank-1 ≥ baseline; no collision ≥0.75;
2.6 now passes.

---

## Phase 4 — Fix the behavioral harness ⚑free

Harness only. Still no eval runs.

- [ ] 4.1 `run_eval.py` scaffolds to a **temp dir outside the repo**; dataset copied or
      symlinked in. Kills the inherited-`CLAUDE.md` contamination path
- [ ] 4.2 `eval_metadata.json` records resolved settings path, installed plugin list, model id
- [ ] 4.3 Add a `--no-project-context` control arm
- [ ] 4.4 Blind the grader: strip arm from paths, grade from a hashed manifest.
      **Or** delete the "deliberately blind to the arm" claim from
      `benchmarks/evals/README.md` — current gradings name the arm in their own notes, so
      one of the two has to change
- [ ] 4.5 `max_turns` / `max_cost_usd` become per-case fields in `evals.json`
- [ ] 4.6 Add an explicit **completion** expectation to every positive case — *"the run
      produces a verdict, not a question"* — so a stall fails one named check instead of
      three content checks by accident
- [ ] 4.7 `aggregate.py` headline → per-case macro pass^k; retire the current `run_summary`
- [ ] 4.8 Gitignore `benchmarks/evals/*/results/`; keep only `example/` committed
      (currently ~144 MB of `creditcard.csv` copies are staged across trial dirs)
- [ ] 4.9 Add pressure-case variants (authority / time / sunk cost) to `evals.json` for each
      discipline skill

**Exit:** harness reproducible from a clean checkout; methodology doc matches behavior.

---

## Phase 5 — Iteration-3 ⚑**spends tokens (~$40–60)**

- [ ] 5.1 Scaffold: **6 cases × 5 trials × 2 arms × 2 datasets** (credit-card-fraud,
      house-prices) = 120 runs. If budget is tight, cut to 3 trials on house-prices, never
      on credit-card-fraud
- [ ] 5.2 Execute both arms; verify from metadata that the arm toggle actually applied
- [ ] 5.3 Grade blind
- [ ] 5.4 `aggregate.py` → `benchmark.json`, `summary.md`, cost table
- [ ] 5.5 Evaluate against SPEC §7 exit criteria

◆ **Checkpoint 5** — the ship/no-ship gate.

**Watch evals 3, 4, 6 first, not eval 1.** Phase 3 pushes hard toward "always proceed";
those three test where stopping is correct. If eval-4 fabricates demographic slices on
PCA-anonymized data, the over-correction is real and Phase 3 needs to soften — with a
positive example of good stopping, not another prohibition.

**Exit:** all 8 exit criteria met, or a named list of which failed and why.

---

## Phase 6 — Ship

- [ ] 6.1 `AUDIT.md` hook table refreshed if any hook changed (CLAUDE.md hard rule)
- [ ] 6.2 README: skill table, counts, pipeline diagram, Benchmarks section
- [ ] 6.3 CHANGELOG `[1.0.0]` — lead with the iteration-2 regression and what it cost.
      A pack about honest reporting should publish its own bad run
- [ ] 6.4 Bump `plugin.json` + `marketplace.json`
- [ ] 6.5 Re-run full `pytest` + Tier 2 on a clean clone
- [ ] 6.6 Tag, PR to `master`

---

## Deferred (P2, explicitly out of v1)

- Cross-platform command variants (Gemini / Codex / Antigravity). **Until then, either ship
  them or drop practice #8's cross-harness claim from `benchmarks/evals/README.md`** — it
  currently claims an axis that has only ever been exercised on Claude Code.
- Per-skill distribution (`npx skills add …`). Blocked on shared `references/` portability,
  the same gap tracked upstream as addyosmani/agent-skills#361.
- A third dataset for the eval suite.

---

## Sequencing rationale

| Phase | Cost | Buys |
|---|---|---|
| 0 | free | known starting state, honest CHANGELOG |
| 1 | free | a definition of well-formed + the Phase 3 worklist |
| 2 | free | **the check that catches routing bugs before they cost money** |
| 3 | free | the actual restructure, gated by 1 and 2 |
| 4 | free | a harness whose results can be trusted |
| 5 | ~$40–60 | the only evidence that any of this worked |
| 6 | free | release |

Everything expensive happens once, at the end, after four free gates. That is the inverse of
iteration-2, where the first signal of a routing bug arrived after the money was spent.

## First three actions

1. `git checkout -b feat/v1-architecture`
2. Phase 2.1 + 2.5 — build `route_check.py`, run it on today's 30 descriptions, commit the
   collision matrix. **Do this before touching a single skill file**; it converts the merge
   list from opinion into measurement.
3. Bring the matrix to Checkpoint 2.
