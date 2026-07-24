# SPEC — `/ds-package` and `/ds-deploy` (the deployment mile)

Status: **draft, awaiting approval.** Scope: add two pipeline stages that carry
Last DS Mile past `/ds-handoff` into packaging and deployment, closing the gap
between the plugin's name and what it covers — without abandoning its
pure-markdown, honesty-gated identity.

## 1. Objective

**What we're building.** Two new pipeline stages:

- `/ds-package` (stage 11) — turn the handed-off model into a **servable,
  portable unit** and prove it serves the *same* predictions it produced offline.
- `/ds-deploy` (stage 12) — stand that unit up as a **callable endpoint** with the
  operational honesty layer (monitoring, drift, rollback) that keeps a live model
  trustworthy.

**Why.** The name promises the deployment last mile; today the pipeline stops at
`/ds-handoff`. External feedback landed on this immediately ("last-mile without
`/package` and `/deploy` isn't really a thing"). These stages earn the name — and
they do it by catching the deployment world's silent-failure modes
(training/serving skew, silent drift, no rollback) the same way the rest of the
plugin catches leakage and inflated metrics.

**Target users.** The same people the plugin already serves — practitioners doing
tabular supervised learning who want a disciplined path — now extended to the
point where a model becomes a running service.

**Decisions locked (this spec is built on them):**

| Decision | Choice |
|---|---|
| How much to ship | **Markdown guidance only** — skills instruct the agent to generate artifacts into the *user's* project; the plugin ships no runtime code and adds no dependency. |
| MLOps / logging | **Tool-agnostic discipline** — prescribe *what* to log (inputs, predictions, online-metric-vs-baseline, drift signal) as newline-delimited JSON. No required tool. |
| Docker persistence | **Dockerfile committed to the user's repo** — image rebuilds from the pinned env + serialized artifact; record the built image digest in the stage doc. No image binaries in git. |
| Deploy reach | **Local container first**, with documented cloud adapters left as stubs the user fills in. No vendor baked in, no silent prod push. |

**On AutoML (explicit, since it was asked).** Because the stages are
framework-agnostic, they wrap *any* serialized predictor behind the `predict()`
contract — sklearn, an AutoGluon predictor, a plain function. The guidance notes
that an AutoGluon predictor has its own `predict` interface and can log to MLflow
if the user already runs MLflow, but the plugin **prescribes no AutoML and bundles
none**. AutoML is "supported" by being agnostic, not by taking a dependency.

### Non-goals

- No shipped Python package, no bundled AutoML, no MLflow dependency.
- No registry push, no cloud API calls from the plugin itself.
- No automated retraining triggers (a later stage/roadmap item).
- Not a general MLOps platform — a disciplined, honest local-first path with
  documented escape hatches.

## 2. Commands

| Command | Stage | Hard Gate | Produces |
|---|---|---|---|
| `/ds-package` | 11 | Requires `/ds-handoff` artifacts (pinned env + serialized model + model card). **Internal gate: training/serving parity must pass.** | `.last-ds-mile/stages/11-package.md`, plus generated `Dockerfile`, `predict` wrapper, `contract.json` in the user's project |
| `/ds-deploy` | 12 | Requires `/ds-package`. **Gate: a monitoring hook, a drift hook, and a rollback pointer must exist before full-traffic deploy.** | `.last-ds-mile/stages/12-deploy.md`, plus generated monitoring/drift hooks and rollback record |

Both also update shared surfaces:

- `/ds` router — pipeline map extended to `0 … 12`; skip-ahead into package/deploy
  reminds the user of the new gates.
- `ds-method` — new Hard Gates and Red Flags rows for the deployment mile.

### `/ds-package` process (summary — full text lives in the skill)

1. **Gate check** — handoff artifacts present (pinned env, serialized model, model card).
2. **Inference contract** — derive input schema (columns, dtypes, ranges, known
   categories) and output schema from training data; write `contract.json`.
3. **Predict wrapper** — thin, framework-agnostic `predict(rows) -> preds` loading
   the pinned artifact; no notebook state.
4. **Boundary validation** — reject/flag rows violating the contract (serving-time
   analog of the `/ds-data` sanitization gate).
5. **Parity gate (signature check)** — run the wrapper over held/eval rows; assert
   it reproduces the offline predictions within a stated tolerance. Fail = stop.
   This is the deployment world's leakage check.
6. **Containerize** — emit a `Dockerfile` from (pinned env + artifact + wrapper) and
   a smoke test. Build locally; record the image digest.
7. **Write** `11-package.md`: contract summary, parity result, image digest, smoke-test result.

### `/ds-deploy` process (summary)

1. **Gate check** — a parity-verified package + contract exist.
2. **Local endpoint** — stand the container up locally as the default callable service.
3. **Operational gate (before full traffic), all three required:**
   - **Monitoring hook** — log inputs + predictions + online metric vs. the *same
     baseline heuristic* beaten at `/ds-baseline`, as newline JSON.
   - **Drift hook** — compare serving-input distributions to training; **reuse the
     `distribution-shift` skill**. Warn on drift.
   - **Rollback pointer** — record the previous image digest; one-command revert.
4. **Canary discipline** — recommend shadow / small-canary before 100%; never route
   full traffic on first deploy.
5. **Confirm boundary** — any push to a remote/registry/cloud target **stops and asks**.
6. **Write** `12-deploy.md`: endpoint location, hook locations, rollback pointer, canary plan.

## 3. Project structure

New files shipped by the plugin:

```
skills/ds-package/SKILL.md        # stage 11 skill (markdown, full anatomy)
skills/ds-deploy/SKILL.md         # stage 12 skill
commands/ds-package.md            # thin command → references ds-package skill
commands/ds-deploy.md             # thin command → references ds-deploy skill
```

Files modified by the plugin:

```
commands/ds.md                    # pipeline map 0→12, new gate reminders
skills/ds-method/SKILL.md         # new Hard Gates + Red Flags rows
tests/test_plugin_structure.py    # STAGE_SKILLS += ds-package, ds-deploy
README.md                         # pipeline table (0→12), scope statement rewrite, skill count 28→30
CHANGELOG.md                      # [0.8.0] entry
.claude-plugin/plugin.json        # version → 0.8.0
package.json                      # version → 0.8.0
```

Generated **into the user's project** by the skills (never shipped by the plugin):

```
.last-ds-mile/stages/11-package.md
.last-ds-mile/stages/12-deploy.md
.last-ds-mile/package/Dockerfile
.last-ds-mile/package/predict.py        # or the project's language equivalent
.last-ds-mile/package/contract.json
.last-ds-mile/deploy/monitor.jsonl      # append-only prediction/metric log
.last-ds-mile/deploy/rollback.json      # previous image digest + revert command
```

## 4. Code style

- **Markdown skill anatomy** — every new skill has the six required sections:
  `## Overview`, `## When to Use`, `## Core Process`, `## Common Rationalizations`,
  `## Red Flags`, `## Verification`. Hard-gate stages also carry the gate in the
  frontmatter `description`, matching `ds-handoff`.
- **Naming** — `ds-`-prefixed skills have a matching command (both stages qualify).
- **Voice** — warn-don't-block; cite `ds-method` for shared rationalizations/red
  flags rather than re-listing them; gates *stop and ask*, never silently work around.
- **Prescribed generated code** — whatever the skill tells the agent to write into
  the user's project must be dependency-light (stdlib + the model's already-pinned
  deps), reproducible, and free of vendor SDK assumptions. The `Dockerfile` builds
  from the pinned env; the `predict` wrapper imports only what the model needs.
- **Frontmatter description ≤ 1024 chars** (enforced by tests).

## 5. Testing strategy

Hermetic — **no `docker build`, no container run, no network in CI.** Extend
`tests/test_plugin_structure.py`:

- Add `ds-package`, `ds-deploy` to `STAGE_SKILLS` → auto-covers skill structure,
  frontmatter, required sections, and command↔skill wiring.
- `/ds` router test already asserts every `STAGE_SKILLS` entry appears — extending
  the list makes it enforce the map is updated to 0→12.
- New assertions:
  - `ds-package` skill references the **parity** gate and `contract.json`.
  - `ds-deploy` skill references the **monitoring**, **drift** (`distribution-shift`),
    and **rollback** requirements, and the confirm-before-push boundary.
  - `ds-method` names the two new Hard Gates.
- `test_version_is_identical_across_both_manifests` and the README-count checks stay
  green after the `0.8.0` bump and the 28→30 update.

Out of scope for CI (documented as manual verification in the stage docs): actually
building the image, running the endpoint, exercising a real deploy.

## 6. Boundaries

**Always:**
- Keep the plugin pure-markdown — ship no runtime code, add no dependency.
- Local-container-first; Dockerfile committed to the user's repo, image rebuilt from source.
- Enforce gates by warning and stopping to ask (warn-don't-block posture).
- Cite `ds-method`; reuse `distribution-shift` for drift rather than reinventing it.
- Record the built image digest (not the image binary) in the stage doc.

**Ask first (stop and confirm):**
- Any outward push — container registry, cloud deploy target, remote endpoint.
- Adding any dependency or reintroducing AutoML/MLflow into the core.
- Routing more than canary/shadow traffic to a freshly deployed model.

**Never:**
- Silently push to production or any remote.
- Make network calls from the plugin itself (preserve the `AUDIT.md` "nothing over
  the network, ever" guarantee).
- Commit image binaries or large artifacts to git.
- Bake in a single cloud vendor as the only path.
- Enter credentials or registry tokens on the user's behalf.

---

*On approval, implementation order: (1) `ds-package` skill + command, (2)
`ds-deploy` skill + command, (3) `ds-method` gate rows, (4) `/ds` router map, (5)
tests, (6) README scope/table/count, (7) `0.8.0` bump + CHANGELOG. Each on the
working branch, tests green before commit.*
