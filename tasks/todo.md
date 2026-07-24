# TODO — deployment mile (`/ds-package` + `/ds-deploy`)

Tracks [plan.md](plan.md). Check off as each lands; stop at each ◆ checkpoint for review.

## Phase 0 — Setup
- [x] 0.1 Branch `feat/deploy-mile` off `main`; baseline `pytest` green

## Phase 1 — `/ds-package` (stage 11)
- [x] 1.1 `skills/ds-package/SKILL.md` — full anatomy, parity gate, contract, Dockerfile
- [x] 1.2 `commands/ds-package.md` — thin command
- [x] 1.3 `ds-method` package gate row + `/ds` router entry (`11. /ds-package`)
- [x] 1.4 Tests: add `ds-package` to `STAGE_SKILLS` + `test_package_skill_specifics`; suite green
- [x] ◆ **Checkpoint 1** — auto mode: parity tolerance defaulted to exact/documented-epsilon, flagged for review

## Phase 2 — `/ds-deploy` (stage 12)
- [x] 2.1 `skills/ds-deploy/SKILL.md` — monitoring + drift (`distribution-shift`) + rollback + confirm-before-push
- [x] 2.2 `commands/ds-deploy.md` — thin command
- [x] 2.3 `ds-method` deploy gate row + `/ds` router entry (`12. /ds-deploy`)
- [x] 2.4 Tests: add `ds-deploy` to `STAGE_SKILLS` + `test_deploy_skill_specifics`; suite green
- [x] ◆ **Checkpoint 2** — auto mode: local-first + confirm-before-push encoded, flagged for review

## Phase 3 — Docs + release
- [x] 3.1 README — Commands table (+2 rows, 15→17, 12→14, Three→Five gates); counts 28→30; **Scope rewrite** (drop "ends at handoff")
- [x] 3.2 CHANGELOG `[0.8.0]` + bump `plugin.json` & `package.json` to `0.8.0`
- [x] 3.3 Full `pytest` green
- [ ] ◆ **Checkpoint 3** — present diff; decide commit-to-`main` vs. PR; nothing pushed without go

## Definition of done
- [x] `/ds-package` and `/ds-deploy` fully wired (skill + command + gate + router + tests)
- [x] No stale "pipeline ends at handoff" / "deployment not covered" language in README
- [x] `0.8.0` synced across both manifests; CHANGELOG updated
- [x] Full structure suite green; no runtime code shipped, no new dependency
