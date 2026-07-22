# TODO — deployment mile (`/ds-package` + `/ds-deploy`)

Tracks [plan.md](plan.md). Check off as each lands; stop at each ◆ checkpoint for review.

## Phase 0 — Setup
- [ ] 0.1 Branch `feat/deploy-mile` off `main`; baseline `pytest` green

## Phase 1 — `/ds-package` (stage 11)
- [ ] 1.1 `skills/ds-package/SKILL.md` — full anatomy, parity gate, contract, Dockerfile
- [ ] 1.2 `commands/ds-package.md` — thin command
- [ ] 1.3 `ds-method` package gate row + `/ds` router entry (`11. /ds-package`)
- [ ] 1.4 Tests: add `ds-package` to `STAGE_SKILLS` + `test_package_skill_specifics`; suite green
- [ ] ◆ **Checkpoint 1** — review skill wording, parity tolerance, `.last-ds-mile/package/` layout

## Phase 2 — `/ds-deploy` (stage 12)
- [ ] 2.1 `skills/ds-deploy/SKILL.md` — monitoring + drift (`distribution-shift`) + rollback + confirm-before-push
- [ ] 2.2 `commands/ds-deploy.md` — thin command
- [ ] 2.3 `ds-method` deploy gate row + `/ds` router entry (`12. /ds-deploy`)
- [ ] 2.4 Tests: add `ds-deploy` to `STAGE_SKILLS` + `test_deploy_skill_specifics`; suite green
- [ ] ◆ **Checkpoint 2** — review deploy gates, confirm-boundary, local-first cutoff, cloud stubs

## Phase 3 — Docs + release
- [ ] 3.1 README — Commands table (+2 rows, 15→17, 12→14, Three→Five gates); counts 28→30; **Scope rewrite** (drop "ends at handoff")
- [ ] 3.2 CHANGELOG `[0.8.0]` + bump `plugin.json` & `package.json` to `0.8.0`
- [ ] 3.3 Full `pytest` green (known AutoGluon skips allowed)
- [ ] ◆ **Checkpoint 3** — present diff; decide commit-to-`main` vs. PR; nothing pushed without go

## Definition of done
- [ ] `/ds-package` and `/ds-deploy` fully wired (skill + command + gate + router + tests)
- [ ] No stale "pipeline ends at handoff" / "deployment not covered" language in README
- [ ] `0.8.0` synced across both manifests; CHANGELOG updated
- [ ] Full structure suite green; no runtime code shipped, no new dependency
