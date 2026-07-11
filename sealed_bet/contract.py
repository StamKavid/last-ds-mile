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
        return self

    def save(self, path) -> None:
        self.validate()
        Path(path).write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path) -> "Contract":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(**data).validate()
