---
name: ds-data
description: Loads and profiles a new dataset before any modeling — schema, provenance, integrity checks, and a data dictionary. Use when a new dataset, file, or table is introduced to a DS project, or before EDA/modeling begins on data that hasn't been profiled yet.
---

# ds-data — Data Understanding

## Overview

Establishes what a dataset actually contains and whether it can be trusted, before any
exploration or modeling touches it.

## When to Use

- A new dataset, file, or table is introduced to the project.
- Before `/ds-explore` begins on data that hasn't been profiled yet.
- NOT for: deciding what to do with missing values or encodings (that's `/ds-prep`) —
  this stage documents what's there, `/ds-prep` acts on it.

## Core Process

1. Identify the file type and provenance before loading it fully. Note where it came
   from and who provided it — this matters later when trust decisions are made about
   serialized objects (full sanitization treatment ships in a later release of this
   plugin; for now, at minimum record provenance before treating a file as trusted).
2. Load and profile: row/column counts, dtypes, missingness per column, cardinality of
   categorical columns, duplicate rows or keys.
3. Build a data dictionary: one row per column with its type, meaning (ask the user if
   unclear), and any known issues.
4. Sanity-check values against domain expectations (e.g. ages between 0–120, dates not
   in the future). Flag violations explicitly — don't silently coerce or drop them.
5. Write to `.last-ds-mile/stages/01-data.md`: the data dictionary, integrity findings,
   and open questions for the stakeholder.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The column names are self-explanatory, I don't need a dictionary" | Self-explanatory to you today; not to a reviewer six months from now, and not proof the values actually match the name. |

See `ds-method` for the shared Rationalizations that apply to every stage.

## Red Flags

| Red Flag | What it usually means |
|---|---|
| A column's summary stats look implausible (e.g. "age" has a max of 999) | Don't drop it silently — log it in the integrity findings and ask the stakeholder before deciding how to handle it. |

See `ds-method` for the shared Red Flags that apply to every stage.

## Verification

- [ ] Data dictionary written covering every column.
- [ ] Missingness and duplicate-key checks run and recorded.
- [ ] Implausible values flagged explicitly, not silently dropped or coerced.
- [ ] `.last-ds-mile/stages/01-data.md` written.
