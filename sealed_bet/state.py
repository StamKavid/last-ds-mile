"""Seal state: enforce that the holdout is opened exactly once."""
from __future__ import annotations

import json
from pathlib import Path

_NAME = "seal_state.json"


def _path(out_dir) -> Path:
    return Path(out_dir) / _NAME


def init_state(out_dir) -> None:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    _path(out_dir).write_text(json.dumps({"opened": False}), encoding="utf-8")


def is_opened(out_dir) -> bool:
    p = _path(out_dir)
    if not p.exists():
        return False
    return bool(json.loads(p.read_text(encoding="utf-8")).get("opened", False))


def mark_opened(out_dir) -> None:
    _path(out_dir).write_text(json.dumps({"opened": True}), encoding="utf-8")
