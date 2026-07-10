---
title: The Notebook Nobody Could Rerun
skills: [notebook-hygiene]
stages: [ds-handoff]
---

# The Notebook Nobody Could Rerun

A churn-prediction notebook had been "done" for three weeks — the plots looked
right, the metrics were written into the final slide deck, and the model was
already in a review queue for deployment. When a teammate tried to reproduce
the results before signing off on the handoff, restarting the kernel and
running the notebook top to bottom produced a different AUC than the one in
the slides, and one cell threw a `NameError` for a variable that was never
defined anywhere in the visible code.

Reconstructing what happened: a data-cleaning step had been run once, by hand,
in a cell that was later deleted during a round of "let me clean this up"
edits — but the *output* of that cell (a dataframe held in memory) was still
being used by every cell below it. The notebook's displayed state didn't
reflect its own code anymore; it reflected an execution history that no
longer existed anywhere on disk.

The fix took two days: reconstructing the missing cleaning step from git
history and Slack screenshots, re-running the whole notebook fresh, and only
then trusting the numbers enough to hand off. The AUC in the corrected run was
0.03 lower than the one in the slides — small, but the team's confidence in
every other number they'd shipped that quarter took a bigger hit than the AUC
did.

**Lesson**: "the plots look right" is not evidence a notebook is reproducible
— only Restart & Run All is. Do it before considering exploratory work done,
not after someone downstream asks why they can't reproduce your number.
