---
name: ds-package
description: Packages a handed-off model into a servable, portable unit — an inference contract, a thin framework-agnostic predict wrapper, and a reproducible Dockerfile — and proves it serves the same predictions it produced offline. Hard gate — requires the /ds-handoff artifacts and refuses to proceed unless the training/serving parity check passes. Use when a model is ready to become a running service.
---

# ds-package — Make It Servable, Prove Parity

## Overview

`/ds-handoff` proves the work *reruns*. This stage makes it *serve*: it wraps the
pinned model behind a stable inference contract, containerizes it reproducibly, and —
the point of the stage — proves the packaged model returns the **same predictions it
produced offline**. Training/serving skew is to deployment what target leakage is to
modeling: the silent failure that passes every offline check and still ships a wrong
answer. This stage exists to catch it before `/ds-deploy`.

It ships no code itself — it guides you to generate the contract, wrapper, and
`Dockerfile` into your own project under `.last-ds-mile/package/`.

## When to Use

- After `/ds-handoff` has produced a pinned environment, a serialized model artifact,
  and a model card, and the model is ready to become a callable service.
- NOT for further tuning or re-evaluation — if the model isn't finished, go back to
  `/ds-model` or `/ds-evaluate`.
- NOT for text, vision, recommenders, or forecasting stacks — outside plugin scope.

## Core Process

1. **Gate check.** Confirm the `/ds-handoff` artifacts exist: a pinned environment
   (lockfile or exact-version `requirements.txt`/`environment.yml`), a serialized model
   with its version and training-data hash/date, and a model card. If any is missing,
   stop and run `/ds-handoff` first.
2. **Write the inference contract** to `.last-ds-mile/package/contract.json`: the input
   schema (column names, dtypes, allowed ranges, known categories — derived from the
   training data) and the output schema (the prediction, plus probability/uncertainty
   if the model emits it). This is the frozen interface the service promises.
3. **Write a thin, framework-agnostic predict wrapper** to
   `.last-ds-mile/package/predict.py` (or the project's language equivalent): a
   `predict(rows) -> preds` that loads the *pinned* artifact and carries no notebook
   state or globals. It wraps whatever the model is — sklearn, an AutoGluon predictor,
   a plain function — behind the one contract.
4. **Validate at the boundary.** The wrapper rejects or flags rows that violate the
   contract (out-of-range values, unseen categories) — the serving-time analog of the
   `/ds-data` sanitization gate.
5. **Parity gate (the signature check).** Run the wrapper over the held/eval rows and
   assert it reproduces the offline predictions — exact for a deterministic model, or
   within a documented epsilon for a float path where hardware/library differences
   apply. **If parity fails, stop.** A mismatch means a feature is computed differently
   at serve time than at train time; fix the wrapper (or the feature) before continuing.
6. **Containerize reproducibly.** Generate `.last-ds-mile/package/Dockerfile` that
   builds the image from the pinned environment + the serialized artifact + the predict
   wrapper, plus a smoke test that loads the model and scores one row. Build locally and
   record the resulting image **digest** — never commit the image binary.
7. **Write** `.last-ds-mile/stages/11-package.md`: the contract summary, the parity
   result (tolerance used and outcome), the image digest, and the smoke-test result.

## Common Rationalizations

See `ds-method` for the shared Rationalizations that apply to every stage.

| Rationalization | Reality |
|---|---|
| "The offline predictions are obviously correct — skip the parity check" | Parity isn't checking the model, it's checking the *serving path*. Skew hides in feature recomputation, not the model weights. |
| "I'll just `docker run` the notebook, it's the same environment" | A notebook isn't a service — no contract, no boundary validation, no proof the loaded artifact scores identically. Package it properly. |

## Red Flags

See `ds-method` for the shared Red Flags that apply to every stage.

| Red Flag | What it usually means |
|---|---|
| Packaged predictions differ from the offline predictions on the same rows | Training/serving skew — a feature is computed differently at serve time. This is the exact condition the parity gate exists to catch. Do not proceed. |
| The `Dockerfile` installs bare package names instead of the pinned versions | The image won't reproduce; you've reintroduced "works on my machine" at the container layer. |
| The contract has no allowed ranges or category lists | Nothing at the boundary can reject bad input, so the first malformed production row becomes a silent wrong answer. |

## Verification

- [ ] Gate check passed: pinned environment, serialized artifact, and model card all present.
- [ ] `.last-ds-mile/package/contract.json` written with input and output schemas.
- [ ] Predict wrapper loads the pinned artifact and validates rows against the contract.
- [ ] Parity gate passed — packaged predictions reproduce offline predictions within the stated tolerance.
- [ ] `Dockerfile` builds from the pinned env + artifact; image digest recorded, binary not committed.
- [ ] `.last-ds-mile/stages/11-package.md` written.
