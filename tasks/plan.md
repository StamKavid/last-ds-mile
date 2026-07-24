# PLAN — `/ds-package` + `/ds-deploy` (the deployment mile)

Derived from [SPEC.md](../SPEC.md). Status: **awaiting human review.**
Decisions locked: markdown-guidance-only · tool-agnostic JSON logging ·
Dockerfile-in-repo · local-first with cloud stubs.

## Objective (one line)

Add two gated pipeline stages that carry the pipeline past `/ds-handoff` into
packaging and deployment, so the plugin earns its name — without shipping runtime
code or taking a dependency.

## Dependency graph

```
                 ┌─────────────────────────────────────────┐
 Phase 0         │ P0  Branch + baseline green              │
 (setup)         └───────────────────┬─────────────────────┘
                                     │
                 ┌───────────────────▼─────────────────────┐
 Phase 1         │ P1  /ds-package  (VERTICAL SLICE)        │
 (package)       │ skill + command + ds-method gate row +   │
                 │ /ds router entry + tests + verify        │
                 └───────────────────┬─────────────────────┘
                                     │  ◆ CHECKPOINT 1 (human review)
                 ┌───────────────────▼─────────────────────┐
 Phase 2         │ P2  /ds-deploy  (VERTICAL SLICE)         │
 (deploy)        │ depends on package (gate + artifacts).   │
                 │ skill + command + ds-method gate row +   │
                 │ /ds router entry + drift-skill reuse +   │
                 │ tests + verify                           │
                 └───────────────────┬─────────────────────┘
                                     │  ◆ CHECKPOINT 2 (human review)
                 ┌───────────────────▼─────────────────────┐
 Phase 3         │ P3  Docs + release                       │
 (release)       │ README (scope rewrite, commands table,   │
                 │ counts) + CHANGELOG + 0.8.0 bump +       │
                 │ full suite green                         │
                 └───────────────────┬─────────────────────┘
                                     │  ◆ CHECKPOINT 3 (human review → commit/push)
```

**Why this order.** `/ds-deploy` gates on `/ds-package` (needs a parity-verified
image + contract), so package is genuinely upstream. Docs come last so the scope
rewrite and counts describe what actually exists. Shared files (`commands/ds.md`,
`skills/ds-method/SKILL.md`, `tests/test_plugin_structure.py`) are edited in both
P1 and P2 but touch **different rows**, so sequential edits don't collide.

## Vertical slicing rationale

Each stage is one complete path — skill **and** its command **and** its gate row
**and** its router entry **and** its tests — not "all skills, then all commands,
then all tests." After Phase 1 the plugin has a working, tested `/ds-package` end
to end; after Phase 2, a working `/ds-deploy`. Nothing is half-wired between phases.

---

## Phase 0 — Setup

### Task 0.1 — Working branch + green baseline
- Create `feat/deploy-mile` off `main`.
- **Acceptance:** on the new branch; `uv run pytest tests/test_plugin_structure.py -q`
  passes before any change.
- **Verify:** `git branch --show-current` → `feat/deploy-mile`; pytest exit 0.

*Note: the entry-point skill and 0.7.0 bump are already on `main`; this branches off that.*

---

## Phase 1 — `/ds-package` (stage 11)

### Task 1.1 — `ds-package` skill
- Write `skills/ds-package/SKILL.md` with full anatomy (Overview, When to Use, Core
  Process, Common Rationalizations, Red Flags, Verification). Frontmatter
  `description` states the Hard Gate (requires handoff) and the **parity gate**,
  mirroring `ds-handoff`'s style, ≤ 1024 chars.
- Core Process encodes: gate check → `contract.json` (input/output schema) → thin
  framework-agnostic `predict()` wrapper → boundary validation → **parity gate**
  (packaged preds reproduce offline preds within stated tolerance; fail = stop) →
  `Dockerfile` from pinned env + artifact + smoke test → write `11-package.md`.
- Cite `ds-method`; do not re-list shared rows.
- **Acceptance:** file exists; all six sections present; references `contract.json`,
  the parity gate, and `.last-ds-mile/stages/`.
- **Verify:** covered by Task 1.4 tests.

### Task 1.2 — `ds-package` command
- Write `commands/ds-package.md` in the thin format (`description` frontmatter +
  "Invoke the `ds-package` skill … $ARGUMENTS").
- **Acceptance:** frontmatter has `description`; body references `ds-package`.
- **Verify:** `test_stage_command_exists[ds-package]` passes once Task 1.4 lands.

### Task 1.3 — `ds-method` gate + `/ds` router entry (package rows)
- Add a Hard Gate row to `skills/ds-method/SKILL.md`: `/ds-package` requires the
  `/ds-handoff` artifacts and passes the parity check. Add a Red Flag row
  (offline/online prediction mismatch = training/serving skew).
- Update `commands/ds.md`: extend the map to include `11. /ds-package`, and add a
  skip-ahead gate reminder.
- **Acceptance:** `ds-method` names the package gate; `ds.md` contains `/ds-package`.
- **Verify:** `test_ds_router_command_lists_all_stages` (after Task 1.4 adds
  `ds-package` to `STAGE_SKILLS`).

### Task 1.4 — Tests for package
- Add `ds-package` to `STAGE_SKILLS` in `tests/test_plugin_structure.py`.
- Add `test_package_skill_specifics`: asserts the skill references parity + `contract.json`.
- **Acceptance:** new + existing structure tests pass.
- **Verify:** `uv run pytest tests/test_plugin_structure.py -q` → exit 0.

### ◆ Checkpoint 1 — human review
Review `ds-package` skill wording, the **parity-gate tolerance** (exact vs.
within-epsilon), and the generated-file layout under `.last-ds-mile/package/`.
Do not proceed to Phase 2 until approved.

---

## Phase 2 — `/ds-deploy` (stage 12)

### Task 2.1 — `ds-deploy` skill
- Write `skills/ds-deploy/SKILL.md`, full anatomy. Frontmatter states the Hard Gate:
  monitoring + drift + rollback must exist before full-traffic deploy; requires
  `/ds-package`.
- Core Process: gate check (parity-verified package) → local container endpoint →
  **operational gate** (monitoring hook logging inputs/preds/metric-vs-baseline as
  JSONL; drift hook **reusing `distribution-shift`**; rollback pointer) → canary
  discipline → **confirm-before-push** boundary → write `12-deploy.md`.
- Cite `ds-method` and `distribution-shift` by name.
- **Acceptance:** six sections; references monitoring, drift (`distribution-shift`),
  rollback, and the confirm-before-push boundary.
- **Verify:** Task 2.4 tests.

### Task 2.2 — `ds-deploy` command
- Write `commands/ds-deploy.md`, thin format.
- **Acceptance:** `description` frontmatter; body references `ds-deploy`.
- **Verify:** `test_stage_command_exists[ds-deploy]`.

### Task 2.3 — `ds-method` gate + `/ds` router entry (deploy rows)
- Add Hard Gate row: `/ds-deploy` requires monitoring + drift + rollback before
  full-traffic. Add Red Flag rows (no rollback pointer; no online baseline comparison;
  full traffic on first deploy).
- Update `commands/ds.md`: add `12. /ds-deploy`; skip-ahead reminder.
- **Acceptance:** `ds-method` names the deploy gate; `ds.md` contains `/ds-deploy`.
- **Verify:** `test_ds_router_command_lists_all_stages`.

### Task 2.4 — Tests for deploy
- Add `ds-deploy` to `STAGE_SKILLS`.
- Add `test_deploy_skill_specifics`: asserts references to monitoring, `distribution-shift`,
  rollback, and confirm-before-push.
- **Acceptance:** full structure suite passes.
- **Verify:** `uv run pytest tests/test_plugin_structure.py -q` → exit 0.

### ◆ Checkpoint 2 — human review
Review the deploy gates, the confirm-before-push boundary wording, the
local-first cutoff, and the cloud-stub framing. Approve before Phase 3.

---

## Phase 3 — Docs + release

### Task 3.1 — README
- `## Commands` (line ~21): counts `15 → 17` commands, `12 → 14` pipeline stages;
  add two table rows (`/ds-package ⚠`, `/ds-deploy ⚠`); update the hard-gate note
  `Three → Five` (line ~43).
- `## All N Skills` (line ~85) and Project Structure comment (line ~216): `28 → 30`,
  update the category breakdown.
- `## Scope` (line ~328): rewrite the "pipeline ends at handoff" bullet — deployment,
  serving, monitoring, and drift are now covered **local-first**; retraining triggers
  remain the only roadmap item.
- **Acceptance:** no stale "ends at handoff"/"not covered" deploy language; counts
  consistent; `npx` line untouched.
- **Verify:** `grep` for "ends at handoff" returns nothing; Task 3.3 count tests pass.

### Task 3.2 — CHANGELOG + version bump
- Move a `## [0.8.0]` entry out of `[Unreleased]` describing both stages.
- Bump `.claude-plugin/plugin.json` and `package.json` to `0.8.0` (kept in sync).
- **Acceptance:** both manifests read `0.8.0`; CHANGELOG has `[0.8.0]`.
- **Verify:** `test_version_is_identical_across_both_manifests` passes.

### Task 3.3 — Full suite + final review
- Run the whole structure suite (and `tests/test_hooks.py` if present) green.
- **Acceptance:** `uv run pytest -q` passes (allowing the known AutoGluon skips).
- **Verify:** pytest exit 0.

### ◆ Checkpoint 3 — human review → integrate
Present the diff. Decide commit-to-`main` vs. PR (per your recent workflow you've
been pushing to `main` directly — confirm at this gate). Nothing pushed without
explicit go.

---

## Risks & mitigations

| Risk | Mitigation |
|---|---|
| Scope rewrite over-promises (deploy still local-first, not a full platform) | Scope bullet says "local-first"; cloud is documented stubs; retraining stays roadmap. |
| Parity gate tolerance is a judgment call | Surfaced at Checkpoint 1 for a human decision before it hardens. |
| Shared-file edit collisions (ds.md, ds-method, tests) across P1/P2 | Different rows, sequential; full suite re-run at each phase catches regressions. |
| `/ds-deploy` implies infra CI can't run | Tests stay hermetic — structure/wording only; real build/run documented as manual verification. |
| README counts drift (28→30, 15→17) | Count assertions in tests + explicit acceptance criteria per surface. |

## Rollback

All work on `feat/deploy-mile`; abandon by deleting the branch. No changes to
`main` until Checkpoint 3. No runtime code shipped, so nothing to un-deploy.
