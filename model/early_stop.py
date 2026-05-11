from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class EarlyStopConfig:
    patience: int = 0
    smoothing: float = 0.05


@dataclass
class EarlyStopTracker:
    patience: int
    smoothing: float
    _best_smoothed_score: float = field(default=float("-inf"), init=False, repr=False)
    _smoothed_score: float = field(default=0.0, init=False, repr=False)
    _best_state_dict: dict = field(default_factory=dict, init=False, repr=False)
    _wait: int = field(default=0, init=False, repr=False)
    _initialized: bool = field(default=False, init=False, repr=False)

    @property
    def best_score(self) -> float:
        return self._best_smoothed_score

    @property
    def enabled(self) -> bool:
        return self.patience > 0

    def step(self, raw_score: float, state_dict: dict) -> bool:
        if not self.enabled:
            return False
        self._update_smoothed(raw_score)
        if self._smoothed_score > self._best_smoothed_score:
            self._record_best(state_dict)
            return False
        self._wait += 1
        if self._wait >= self.patience:
            logger.info(
                "Early stopping after %d iterations without improvement "
                "(best smoothed score: %.1f)",
                self._wait,
                self._best_smoothed_score,
            )
            return True
        return False

    def best_state(self) -> dict:
        return self._best_state_dict

    def _record_best(self, state_dict: dict) -> None:
        self._best_smoothed_score = self._smoothed_score
        self._best_state_dict = copy.deepcopy(state_dict)
        self._wait = 0

    def _update_smoothed(self, raw_score: float) -> None:
        if not self._initialized:
            self._smoothed_score = raw_score
            self._initialized = True
        else:
            self._smoothed_score = (
                self.smoothing * raw_score
                + (1 - self.smoothing) * self._smoothed_score
            )
