---
name: capturing-learnings
description: Defines what's worth capturing as a project-local lesson and when to proactively suggest /ds-learn — a genuine failure-and-fix pair with specifics, not a restated best practice. Use when a bug was found and fixed, a leakage or validation mistake was caught and corrected, or a metric/approach was changed after a bad result — and when the user runs /ds-learn and needs the capture format.
---

# capturing-learnings

## Overview

A lesson worth capturing is a specific failure and its specific fix — not a
reminder to "be careful." This skill defines the bar for that, and the
trigger for proactively suggesting `/ds-learn` when a real one just happened.

## When to Use

- A bug was found and fixed mid-session — a leakage source removed, a broken
  validation split corrected, a wrong metric replaced after a misleading
  result.
- The user invokes `/ds-learn` and needs the capture format (see Core Process).
- NOT for: restating a rule that's already in a skill file ("remember to
  check for leakage") — that's not a lesson, it's the rule the lesson would
  illustrate. A lesson needs a *specific instance*: what broke, concretely,
  and what fixed it, concretely.

## Core Process

1. **Recognize the moment.** Mid-session, when a genuine failure-and-fix pair
   just happened (not hypothetical, not "this could go wrong" — something
   that *did* go wrong and got corrected), say so and suggest `/ds-learn`
   rather than waiting to be asked. This is the same "notice the moment"
   pattern every domain skill in this plugin already uses for its own
   trigger. If already invoked via `/ds-learn` directly, the suggestion has
   already happened — skip straight to step 2.
2. **Check it clears the bar** before capturing: does it name a concrete
   failure (a specific feature, a specific metric value, a specific broken
   assumption) and a concrete fix (what changed, not just "fixed it")? If
   either half is vague, ask one clarifying question rather than capturing a
   vague entry — a vague lesson never resurfaces usefully because nothing
   about it is specific enough to match against later.
3. **Tag it** to whichever stage(s) and/or domain skill(s) it's actually
   relevant to — the tags are what make the lesson resurface at the right
   moment later (see `hooks/session_start.py`'s matching logic, documented
   in `AUDIT.md`). Tag broadly if genuinely relevant to more than one stage;
   don't tag narrowly just to keep the list short.
4. **Capture it** via `/ds-learn`, which appends the structured entry to
   `.last-ds-mile/learnings.jsonl` — this skill defines the judgment, the
   command does the writing.

## Techniques/Patterns — does this count as a lesson?

| Situation | Counts as a lesson? | Why |
|---|---|---|
| A leakage source was found and removed mid-session (e.g. a full-dataset aggregate feature caught and recomputed as-of-date) | Yes | Specific failure (named feature/mechanism) + specific fix (what changed) |
| "Remember to always check for leakage before modeling" | No | This is the rule already in `target-leakage-detection` — no specific instance happened this session |
| A validation split was silently wrong (shuffled K-fold on time-series data) and got swapped to `TimeSeriesSplit` after a result looked implausible | Yes | Concrete broken assumption + concrete fix — matches the shape of `lessons/the-leaderboard-that-lied.md` |
| "The model could probably be better if we tuned more" | No | Not a failure-and-fix — an open-ended observation, nothing specific broke |

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "This is basically the same as what `target-leakage-detection` already says, no need to capture it" | The skill states the general rule; a captured lesson is the specific instance that made the rule real for this project. Both are useful — the lesson makes the rule concrete next time. |
| "This project is small/one-off, no one will hit this again" | The lesson protects THIS project too — the same mistake can resurface at a later stage of the same pipeline (e.g. an assumption fixed during `/ds-prep` quietly breaking again during `/ds-model`), and `/ds-learn` entries are exactly what `SessionStart`'s matching uses to catch that repeat. |

See `ds-method` for the shared Rationalizations that apply to every stage.

## Red Flags

| Red Flag | What it usually means |
|---|---|
| A captured lesson's "what fixed it" is a single vague phrase ("fixed the bug") | This lesson won't be useful when it resurfaces later — go back and get the specific fix before considering the capture done. |
| A genuine failure-and-fix happened this session and `/ds-learn` was never suggested | The proactive-nudge step (Core Process step 1) was skipped — this is the harder failure mode to catch since nothing else in the pipeline enforces it; stay alert for it specifically. |

See `ds-method` for the shared Red Flags that apply to every stage.

## Verification

- [ ] The captured lesson names a specific failure, not a general rule.
- [ ] The captured lesson names a specific fix, not just "resolved."
- [ ] Tags reflect every stage/skill the lesson is genuinely relevant to.
- [ ] `/ds-learn` was suggested proactively when a real failure-and-fix
      happened, not only when the user asked.
