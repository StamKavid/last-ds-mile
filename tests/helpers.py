import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


def parse_frontmatter(path: Path):
    """Parse a markdown file's YAML frontmatter block and return (frontmatter_dict, body_str)."""
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    assert match, f"{path} has no YAML frontmatter block (expected leading '---' ... '---')"
    frontmatter = yaml.safe_load(match.group(1)) or {}
    body = match.group(2)
    return frontmatter, body
