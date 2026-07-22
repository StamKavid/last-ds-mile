---
description: Translate the /ds-report narrative into a one-page brief for non-technical stakeholders
argument-hint: "[optional: who the brief is for, e.g. 'the board' or 'the retention team lead']"
---

Invoke the `ds-brief` skill now via the Skill tool and follow its Core Process.

1. Confirm `.last-ds-mile/stages/09-report.md` exists (the skill's gate check). If
   it doesn't, tell the user to run `/ds-report` first rather than drafting a brief
   from raw evaluation results.
2. If $ARGUMENTS names an intended audience, tailor the framing (e.g. a board brief
   leans on the recommendation and the dollar figure; a frontline-team brief leans
   on "what happens next" and who owns the call) — the five required sections and
   the no-jargon rule apply regardless of audience.
3. Write `.last-ds-mile/stages/09b-brief.md` per the skill's process.
4. Show the brief to the user directly in the response, not only as a file write —
   this is the artifact most likely to be read immediately, not filed away.
