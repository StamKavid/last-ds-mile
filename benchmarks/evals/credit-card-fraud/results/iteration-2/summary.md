# Benchmark summary — pass^k by case

| eval | with_skill pass^k | without_skill pass^k |
|---|---|---|
| 1 | 1.0 | 0.75 |
| 2 | 0.4 | 1.0 |

**Overall pass^k — with_skill 0.769 vs without_skill 0.846 (gap -0.077).**

pass^k = fraction of expectations that passed in *all* trials of that arm. A large gap is the plugin's reproducible marginal value; a gap near zero on passing expectations means the base model already does it (retire, practice #10).

## Cost & latency by case

| eval | with_skill $ | without_skill $ | with_skill turns | without_skill turns |
|---|---|---|---|---|
| 1 | 2.2089 | 0.3362 | 63.3333 | 8.3333 |
| 2 | 0.2866 | 0.251 | 8.0 | 6.3333 |

**Overall mean cost — with_skill $1.2478 vs without_skill $0.2936 (4.25x, OVER the 2.0x budget).**

Cost/latency come from each trial's own harness `result` record (total_cost_usd, duration_ms, num_turns) — not re-derived. The budget check flags whether with_skill's mean cost stays within the stated ceiling relative to without_skill; a plugin that wins on pass^k but blows the budget has not actually proven its value.
