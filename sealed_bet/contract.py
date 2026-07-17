"""The Contract: the human-signed, agent-immutable rules of the bet."""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

from sealed_bet.metrics import METRICS


@dataclass
class Contract:
    target: str
    task: str
    metric: str
    split: dict
    baseline_score: float
    held_frac: float
    seed: int
    data_hash: str
    input_mode: str
    created_at: str
    budget: int
    ceiling_score: float
    ceiling_source: str

    def validate(self) -> "Contract":
        if self.metric not in METRICS:
            raise ValueError(f"unknown metric: {self.metric}")
        if self.task not in ("regression", "classification"):
            raise ValueError(f"unknown task: {self.task}")
        if not math.isfinite(self.baseline_score):
            raise ValueError(f"baseline_score must be finite, got {self.baseline_score}")
        if not (0 < self.held_frac < 1):
            raise ValueError(f"held_frac must be in (0, 1), got {self.held_frac}")
        if self.seed < 0:
            raise ValueError(f"seed must be non-negative, got {self.seed}")
        if self.budget <= 0:
            raise ValueError(f"budget must be a positive int, got {self.budget}")
        if not math.isfinite(self.ceiling_score):
            raise ValueError(f"ceiling_score must be finite, got {self.ceiling_score}")
        if self.ceiling_source not in ("human", "proxy"):
            raise ValueError(f"ceiling_source must be 'human' or 'proxy', got {self.ceiling_source!r}")
        return self

    def save(self, path) -> None:
        self.validate()
        Path(path).write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path) -> "Contract":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        try:
            return cls(**data).validate()
        except TypeError as exc:
            # Most likely cause: a contract.json written by a pre-Phase-C
            # version of this plugin, missing budget/ceiling_score/ceiling_source.
            # Fail loudly and explain rather than silently defaulting those
            # fields -- a made-up ceiling_score would corrupt diagnose()'s
            # regime classification without any visible symptom.
            raise TypeError(
                f"{path} doesn't match this version's Contract shape ({exc}). "
                "If this was sealed by an older version of the plugin, re-run "
                "/ds-seal to write a current-format contract.json."
            ) from exc
