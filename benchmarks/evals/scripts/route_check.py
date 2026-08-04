#!/usr/bin/env python3
"""Tier 2 of the eval harness: does the right skill get picked?

Two deterministic, free checks over the skill
catalog's descriptions:

  1. TRIGGER ROUTING -- for each case file's `trigger.positive[]` prompts, does the
     owning skill rank within top_k? A `--min-rank1` floor guards the rank-1 rate
     (share of positives whose skill ranks FIRST, not merely top-k).
     For each `trigger.negative[]` prompt, the declared `owner` skill must
     outrank the case's own skill -- a real pairwise routing assertion rather
     than one that passes vacuously when a prompt matches nothing.

  2. DESCRIPTION COLLISION -- pairwise cosine over descriptions. Two skills whose
     descriptions are near-identical will fight for the same prompts forever, and
     no amount of body-text quality fixes it.

This is a LEXICAL approximation of routing (stemmed TF-IDF cosine). It cannot
judge semantics -- that is Tier 3's job. It catches the two failure modes that
dominate real trigger bugs: a description missing the vocabulary users actually
say (false negative), and an over-broad description that outranks the right skill
(false positive). A Tier-2 failure usually means FIX THE DESCRIPTION, not the eval.

Ported from addyosmani/agent-skills `scripts/run-evals.js`. Stdlib only -- this
repo has no lockfile and pytest/pyyaml are its only test deps.

Usage:
    python benchmarks/evals/scripts/route_check.py
    python benchmarks/evals/scripts/route_check.py --min-rank1 80
    python benchmarks/evals/scripts/route_check.py --matrix   # full collision table
    python benchmarks/evals/scripts/route_check.py --json
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import re
import sys
from collections import Counter

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
SKILLS_DIR = REPO_ROOT / "skills"
COMMANDS_DIR = REPO_ROOT / "commands"
CASES_DIR = REPO_ROOT / "benchmarks" / "evals" / "cases"

MIN_RANK1_FLOOR = 85.0  # CI gate; tests/test_eval_harness.py reads this
COLLISION_WARN = 0.50
COLLISION_ERROR = 0.75

# Words that carry no routing signal. Deliberately short: an aggressive stoplist
# hides real vocabulary gaps, which are the finding we want.
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "before", "but", "by",
    "can", "do", "does", "for", "from", "has", "have", "how", "i", "if", "in",
    "into", "is", "it", "its", "of", "on", "or", "own", "not", "so", "than",
    "that", "the", "their", "them", "then", "there", "these", "they", "this",
    "to", "up", "use", "used", "using", "was", "were", "what", "when", "where",
    "which", "while", "who", "why", "with", "you", "your",
}

TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_+-]*")
FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---", re.DOTALL)
DESCRIPTION_RE = re.compile(r"^description:\s*(.*?)(?=^\w+:|\Z)", re.MULTILINE | re.DOTALL)


def stem(token: str) -> str:
    """Crude suffix folding so 'validation'/'validate'/'validating' cluster.

    Not a real stemmer, and not trying to be -- it only needs to stop trivially
    related surface forms from being treated as unrelated terms.
    """
    for suffix in ("ations", "ation", "ings", "ing", "ers", "er", "ed", "es", "s"):
        if len(token) > len(suffix) + 3 and token.endswith(suffix):
            return token[: -len(suffix)]
    return token


def tokenize(text: str) -> list[str]:
    return [
        stem(t)
        for t in TOKEN_RE.findall(text.lower())
        if t not in STOPWORDS and len(t) > 1
    ]


def term_freq(tokens: list[str]) -> Counter:
    return Counter(tokens)


def build_corpus(docs: dict[str, str]) -> tuple[dict[str, Counter], dict[str, float]]:
    """Return per-doc term frequencies and the corpus IDF map."""
    tfs = {name: term_freq(tokenize(text)) for name, text in docs.items()}
    n = len(tfs)
    df: Counter = Counter()
    for tf in tfs.values():
        df.update(tf.keys())
    idf = {term: math.log(1 + n / (1 + count)) for term, count in df.items()}
    return tfs, idf


def vectorize(tf: Counter, idf: dict[str, float], default: float | None = None) -> dict[str, float]:
    # Unseen terms get the max IDF a singleton would earn — an unusual word in a
    # prompt is informative, not meaningless. `default` is hoisted by callers in
    # hot paths; recomputing max() per call dominated the runtime.
    if default is None:
        default = max(idf.values()) if idf else 1.0
    return {term: freq * idf.get(term, default) for term, freq in tf.items()}


def corpus_vectors(tfs: dict[str, Counter], idf: dict[str, float]) -> dict[str, dict[str, float]]:
    """Vectorize every document once.

    The document vectors are a pure function of (tfs, idf), both fixed for a run.
    Rebuilding them per prompt was ~98% of all vectorize() calls.
    """
    default = max(idf.values()) if idf else 1.0
    return {name: vectorize(tf, idf, default) for name, tf in tfs.items()}


def norm(v: dict[str, float]) -> float:
    return math.sqrt(sum(x * x for x in v.values()))


def cosine(a: dict[str, float], b: dict[str, float],
           na: float | None = None, nb: float | None = None) -> float:
    if not a or not b:
        return 0.0
    dot = sum(a[t] * b[t] for t in a.keys() & b.keys())
    na = norm(a) if na is None else na
    nb = norm(b) if nb is None else nb
    return 0.0 if na == 0 or nb == 0 else dot / (na * nb)


def _description_of(path: pathlib.Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None
    desc_match = DESCRIPTION_RE.search(match.group(1))
    if not desc_match:
        return None
    return " ".join(desc_match.group(1).split())


def load_descriptions() -> dict[str, str]:
    """name -> routable description text, for skills AND commands.

    Commands are in the corpus on purpose. In the iteration-2 transcripts the
    executor reached `/ds` through the Skill tool (`Skill{skill: last-ds-mile:ds}`)
    and it outranked `data-science-project` — so commands compete in the same
    routing space as skills, and a check that only scored skills would have
    declared that catalog healthy. Command entries are prefixed `cmd:`.
    """
    out: dict[str, str] = {}
    for skill_dir in sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        description = _description_of(skill_md)
        if description is None:
            continue
        # The skill's own name is part of how a user might refer to it.
        out[skill_dir.name] = f"{skill_dir.name.replace('-', ' ')}. {description}"

    for command_md in sorted(COMMANDS_DIR.glob("*.md")):
        description = _description_of(command_md)
        if description is None:
            continue
        name = f"cmd:{command_md.stem}"
        out[name] = f"{command_md.stem.replace('-', ' ')}. {description}"
    return out


def rank(prompt: str, tfs: dict[str, Counter], idf: dict[str, float],
         vectors: dict[str, dict[str, float]] | None = None,
         norms: dict[str, float] | None = None) -> list[tuple[str, float]]:
    """Score one prompt against every corpus entry, best first.

    `vectors` and `norms` are per-corpus and invariant across prompts; callers in
    a loop should build them once via corpus_vectors() and pass them in.
    """
    if vectors is None:
        vectors = corpus_vectors(tfs, idf)
    if norms is None:
        norms = {name: norm(v) for name, v in vectors.items()}
    pv = vectorize(term_freq(tokenize(prompt)), idf)
    pn = norm(pv)
    scored = [(name, cosine(pv, v, pn, norms[name])) for name, v in vectors.items()]
    scored.sort(key=lambda kv: (-kv[1], kv[0]))
    return scored


def load_cases() -> list[dict]:
    if not CASES_DIR.exists():
        return []
    cases = []
    for path in sorted(CASES_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as fh:
            case = json.load(fh)
        case["_path"] = str(path.relative_to(REPO_ROOT))
        cases.append(case)
    return cases


# ─── Checks ──────────────────────────────────────────────────────────────────


def check_triggers(cases, tfs, idf, aliases):
    positives = rank1 = strict_rank1 = topk = 0
    failures: list[str] = []
    vectors = corpus_vectors(tfs, idf)
    norms = {name: norm(v) for name, v in vectors.items()}

    for case in cases:
        skill = case["skill_name"]
        if skill not in tfs:
            failures.append(f"{case['_path']}: names unknown skill '{skill}'")
            continue

        for pos in case.get("trigger", {}).get("positive", []):
            positives += 1
            k = pos.get("top_k", 3)
            scored = rank(pos["prompt"], tfs, idf, vectors, norms)
            names = [n for n, _ in scored]
            position = names.index(skill) + 1
            if position == 1:
                strict_rank1 += 1
            # A skill beaten only by the command that exists to invoke it has
            # still routed correctly -- same destination, different door.
            if names[0] == skill or names[0] in aliases.get(skill, ()):
                rank1 += 1
            if position <= k:
                topk += 1
            else:
                failures.append(
                    f"{skill}: positive prompt ranked #{position} (needs top-{k}) — "
                    f"{pos['prompt']!r} → top3 {names[:3]}"
                )

        for neg in case.get("trigger", {}).get("negative", []):
            owner = neg.get("owner")
            scored = rank(neg["prompt"], tfs, idf, vectors, norms)
            names = [n for n, _ in scored]
            if owner and owner in names:
                if names.index(owner) > names.index(skill):
                    failures.append(
                        f"{skill}: negative prompt should route to '{owner}' but "
                        f"'{skill}' outranks it — {neg['prompt']!r} → top3 {names[:3]}"
                    )
            elif names[0] == skill:
                failures.append(
                    f"{skill}: negative prompt ranked it #1 — {neg['prompt']!r}"
                )

    return {
        "positives": positives,
        "rank1": rank1,
        "strict_rank1": strict_rank1,
        "topk": topk,
        "rank1_rate": round(100 * rank1 / positives, 1) if positives else 0.0,
        "strict_rank1_rate": round(100 * strict_rank1 / positives, 1) if positives else 0.0,
        "topk_rate": round(100 * topk / positives, 1) if positives else 0.0,
        "failures": failures,
    }


SKILL_REF_IN_COMMAND = re.compile(
    r"[Ii]nvoke the `?([a-z][a-z0-9-]+)`? skill|`([a-z][a-z0-9-]+)` skill"
)


def build_alias_map() -> dict[str, set[str]]:
    """skill -> the `cmd:` entries that exist to invoke it.

    Read from each command's body ("Invoke the `ds-frame` skill now ..."), with a
    same-name fallback. A command and the skill it dispatches to are the same
    destination as far as a user is concerned, so one outranking the other is the
    wiring working, not a routing defect.
    """
    aliases: dict[str, set[str]] = {}
    for command_md in sorted(COMMANDS_DIR.glob("*.md")):
        body = command_md.read_text(encoding="utf-8")
        targets = set()
        for a, b in SKILL_REF_IN_COMMAND.findall(body):
            target = a or b
            if (SKILLS_DIR / target).is_dir():
                targets.add(target)
        if not targets and (SKILLS_DIR / command_md.stem).is_dir():
            targets.add(command_md.stem)
        for target in targets:
            aliases.setdefault(target, set()).add(f"cmd:{command_md.stem}")
    return aliases


def _is_alias_pair(a: str, b: str, aliases: dict[str, set[str]]) -> bool:
    return b in aliases.get(a, ()) or a in aliases.get(b, ())


def check_collisions(tfs, idf, aliases):
    names = sorted(tfs)
    vectors = corpus_vectors(tfs, idf)
    norms = {n: norm(vectors[n]) for n in names}
    pairs = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            pairs.append((round(cosine(vectors[a], vectors[b], norms[a], norms[b]), 3),
                          a, b, _is_alias_pair(a, b, aliases)))
    pairs.sort(key=lambda p: -p[0])
    real = [p for p in pairs if not p[3]]
    return {
        "pairs": pairs,
        "errors": [p for p in real if p[0] >= COLLISION_ERROR],
        "warnings": [p for p in real if COLLISION_WARN <= p[0] < COLLISION_ERROR],
    }


# ─── CLI ─────────────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--min-rank1", type=float, nargs="?", const=MIN_RANK1_FLOOR,
                    default=None,
                    help=f"fail if the rank-1 rate falls below this percentage "
                         f"(bare flag uses the checked-in floor, {MIN_RANK1_FLOOR})")
    ap.add_argument("--matrix", action="store_true", help="print the full collision table")
    ap.add_argument("--top", type=int, default=15, help="collision pairs to print (default 15)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    descriptions = load_descriptions()
    if not descriptions:
        print("ERROR: no skill descriptions found", file=sys.stderr)
        return 1

    tfs, idf = build_corpus(descriptions)
    aliases = build_alias_map()
    cases = load_cases()
    collisions = check_collisions(tfs, idf, aliases)
    triggers = check_triggers(cases, tfs, idf, aliases) if cases else None

    shown = collisions["pairs"] if args.matrix else collisions["pairs"][: args.top]

    if args.json:
        print(json.dumps({
            "skills": len(descriptions),
            "cases": len(cases),
            "triggers": triggers,
            "collisions": {
                "errors": collisions["errors"],
                "warnings": collisions["warnings"],
                "pairs": shown,
            },
        }, indent=2))
    else:
        print(f"Skill catalog: {len(descriptions)} descriptions, {len(cases)} case file(s)\n")

        print("── Description collisions ──────────────────────────────────────")
        for score, a, b, alias in shown:
            if alias:
                mark = "alias"
            elif score >= COLLISION_ERROR:
                mark = "ERROR"
            elif score >= COLLISION_WARN:
                mark = "warn "
            else:
                mark = "     "
            print(f"  {mark} {score:.3f}  {a}  ↔  {b}")
        print(f"\n  {len(collisions['errors'])} error(s) >= {COLLISION_ERROR}, "
              f"{len(collisions['warnings'])} warning(s) >= {COLLISION_WARN}\n")

        if triggers:
            print("── Trigger routing ─────────────────────────────────────────────")
            print(f"  rank-1 rate : {triggers['rank1_rate']}%  "
                  f"({triggers['rank1']}/{triggers['positives']} positives rank their skill, "
                  f"or its own command, first)")
            print(f"  strict      : {triggers['strict_rank1_rate']}%  "
                  f"(skill itself first, commands not credited)")
            print(f"  top-k rate  : {triggers['topk_rate']}%  "
                  f"({triggers['topk']}/{triggers['positives']} within top_k)\n")
            for failure in triggers["failures"]:
                print(f"  FAIL {failure}")
            if not triggers["failures"]:
                print("  no routing failures")
            print()
        else:
            print("── Trigger routing ─────────────────────────────────────────────")
            print(f"  no case files in {CASES_DIR.relative_to(REPO_ROOT)} — skipped\n")

    exit_code = 0
    if collisions["errors"]:
        print(f"FAILED: {len(collisions['errors'])} description pair(s) at or above "
              f"{COLLISION_ERROR} cosine. Merge them or rewrite one.", file=sys.stderr)
        exit_code = 1
    if triggers and triggers["failures"]:
        print(f"FAILED: {len(triggers['failures'])} routing assertion(s).", file=sys.stderr)
        exit_code = 1
    if args.min_rank1 is not None and triggers and triggers["rank1_rate"] < args.min_rank1:
        print(f"FAILED: rank-1 rate {triggers['rank1_rate']}% is below the "
              f"{args.min_rank1}% floor.", file=sys.stderr)
        exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
