---
name: ds-deploy
description: Stands a packaged model up as a callable endpoint with the operational honesty layer — input/prediction logging against the live baseline, drift detection, and a rollback pointer. Hard gate — requires the /ds-package artifacts and refuses full-traffic deploy unless monitoring, drift, and rollback all exist. Local-container-first; any push to a remote or cloud target stops and asks. Use when a parity-verified package is ready to serve.
---

# ds-deploy — Make It Callable, Safely

## Overview

A model that ships without monitoring degrades in silence. This stage stands the
`/ds-package` container up as a callable endpoint and requires the operational layer
that keeps it honest in production: logging predictions against the same baseline it
beat offline, watching for input drift, and a one-command way back. It is
local-container-first by design — the plugin never pushes to a remote or a cloud target
on its own. It ships no code; it guides you to generate the endpoint wiring, monitoring
and drift hooks, and rollback record into `.last-ds-mile/deploy/`.

## When to Use

- After `/ds-package` has produced a parity-verified image and an inference contract,
  and the model is ready to serve real requests.
- NOT before parity passes — an unverified package is not deployable.
- NOT for retraining automation — retraining triggers are out of scope (roadmap).

## Core Process

1. **Gate check.** Confirm `/ds-package` produced a parity-verified image and a
   `contract.json`. If parity was never proven, stop and run `/ds-package`.
2. **Local endpoint.** Stand the container up locally as the default callable service
   (a thin HTTP or CLI entry over the packaged `predict`). Cloud targets are documented
   adapter *stubs* the user fills in — never a baked-in vendor path.
3. **Operational gate — all three required before full-traffic deploy:**
   - **Monitoring hook** → `.last-ds-mile/deploy/monitor.jsonl`: append inputs,
     predictions, and — once labels arrive — the online metric *against the same
     baseline heuristic* the model beat at `/ds-baseline`. Newline-delimited JSON, no
     tool dependency. (If the team already runs MLflow, it can log there instead; the
     discipline is what matters, not the tool.)
   - **Drift hook**: compare serving-input distributions against the training
     distributions and warn on drift. Reuse the `distribution-shift` skill for the
     method rather than reinventing it.
   - **Rollback pointer** → `.last-ds-mile/deploy/rollback.json`: the previous image
     digest and a one-command revert.
4. **Canary discipline.** Recommend shadow or a small canary before routing full
   traffic — never send 100% to a freshly deployed model on the first cutover.
5. **Confirm before any outward push.** Standing up locally is fine to proceed. Pushing
   to a container registry, a remote host, or a cloud serving target is outward-facing —
   **stop and ask the user to confirm** (and let them perform any credentialed step).
   The plugin makes no network calls of its own.
6. **Write** `.last-ds-mile/stages/12-deploy.md`: the endpoint location, the monitoring
   and drift hook locations, the rollback pointer, and the canary plan.

## Common Rationalizations

See `ds-method` for the shared Rationalizations that apply to every stage.

| Rationalization | Reality |
|---|---|
| "Ship it to 100% now, we'll add monitoring after" | Without monitoring you can't see degradation, and "after" rarely comes. The gate requires it *before* full traffic for exactly this reason. |
| "We don't need a rollback plan, the model's good" | Rollback isn't about whether this model is good — it's about being able to undo the deploy in one step when the unexpected happens. |
| "Just push it to the registry, it's basically the same" | A registry/cloud push is an outward, often irreversible action. Confirm with the user; never push silently. |

## Red Flags

See `ds-method` for the shared Red Flags that apply to every stage.

| Red Flag | What it usually means |
|---|---|
| No online comparison against the baseline heuristic | You can't tell whether the deployed model is still beating the dumb baseline — degradation stays invisible. |
| No rollback pointer recorded | A bad deploy has no clean way back; the next incident becomes an emergency instead of a one-command revert. |
| Full traffic routed on the first deploy | Skipped the canary — any serving bug hits every user at once instead of a slice. |

## Verification

- [ ] Gate check passed: a parity-verified `/ds-package` image and `contract.json` exist.
- [ ] Endpoint stands up locally and answers a smoke request.
- [ ] Monitoring hook logs inputs, predictions, and the online-vs-baseline metric.
- [ ] Drift hook compares serving inputs to training (via `distribution-shift`).
- [ ] Rollback pointer recorded (previous image digest + revert command).
- [ ] Any push to a remote/registry/cloud target was confirmed with the user, not done silently.
- [ ] `.last-ds-mile/stages/12-deploy.md` written.
