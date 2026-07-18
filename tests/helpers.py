import importlib.util
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent

# AutoGluon is an optional extra (`uv sync --extra benchmarks`), not a core
# dependency -- sealed_bet imports it lazily inside auto.py::_fit_predictor so
# that the core seal/score/contract path never pays for a ~2GB install. The
# handful of tests that exercise that path skip cleanly when it is absent, which
# is what keeps the default `uv sync --group dev` contributor setup fast.
def _autogluon_importable() -> bool:
    """Attempt the real import rather than checking find_spec().

    `autogluon` is a namespace package, so find_spec("autogluon") succeeds even
    when the actual `from autogluon.tabular import TabularPredictor` raises --
    which is exactly what happens when a transitive dependency is missing. A
    spec check would leave these tests un-skipped and failing on an install
    that genuinely cannot run them.
    """
    try:
        importlib.import_module("autogluon.tabular")
    except Exception:
        return False
    return True


HAS_AUTOGLUON = _autogluon_importable()

requires_autogluon = pytest.mark.skipif(
    not HAS_AUTOGLUON,
    reason="needs the optional 'benchmarks' extra (uv sync --extra benchmarks)",
)

FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", re.DOTALL)


def parse_frontmatter(path: Path):
    """Parse a markdown file's YAML frontmatter block and return (frontmatter_dict, body_str)."""
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    assert match, f"{path} has no YAML frontmatter block (expected leading '---' ... '---')"
    frontmatter = yaml.safe_load(match.group(1)) or {}
    body = match.group(2)
    return frontmatter, body
