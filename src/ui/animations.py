from __future__ import annotations

import math
from dataclasses import dataclass

SCORE_EASE_SPEED = 7.0
PULSE_DURATION = 0.55
POPUP_DURATION = 2.5
POPUP_FADE = 0.5


@dataclass
class Popup:
    action: str
    source: str
    created_at: float


def ease_out_cubic(fraction: float) -> float:
    clamped = max(0.0, min(1.0, fraction))
    return 1 - (1 - clamped) ** 3


class Animations:
    def __init__(self) -> None:
        self._displayed_score = 0.0
        self._target_score = 0.0
        self._popups: list[Popup] = []
        self._pulses: dict[int, float] = {}
        self._last_now: float | None = None

    def set_score(self, score: int) -> None:
        self._target_score = float(score)

    def add_popup(self, action: str, source: str, now: float) -> None:
        self._popups.append(Popup(action=action, source=source, created_at=now))

    def pulse(self, key: int, now: float) -> None:
        self._pulses[key] = now

    def update(self, now: float) -> None:
        delta = 0.0 if self._last_now is None else max(0.0, now - self._last_now)
        self._last_now = now
        blend = 1 - math.exp(-delta * SCORE_EASE_SPEED)
        self._displayed_score += (self._target_score - self._displayed_score) * blend
        if abs(self._target_score - self._displayed_score) < 0.5:
            self._displayed_score = self._target_score
        self._pulses = {key: start for key, start in self._pulses.items() if now - start < PULSE_DURATION}

    def displayed_score(self) -> int:
        return round(self._displayed_score)

    def pulse_intensity(self, key: int, now: float) -> float:
        start = self._pulses.get(key)
        if start is None:
            return 0.0
        return 1.0 - ease_out_cubic((now - start) / PULSE_DURATION)

    def active_popups(self, now: float) -> list[dict]:
        total = POPUP_DURATION + POPUP_FADE
        kept: list[Popup] = []
        result: list[dict] = []
        for popup in self._popups:
            age = now - popup.created_at
            if age > total:
                continue
            kept.append(popup)
            alpha = 1.0 if age < POPUP_DURATION else 1.0 - (age - POPUP_DURATION) / POPUP_FADE
            result.append({
                "action": popup.action,
                "source": popup.source,
                "alpha": max(0.0, min(1.0, alpha)),
            })
        self._popups = kept
        return result
