from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    w: int
    h: int

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def bottom(self) -> int:
        return self.y + self.h

    @property
    def centerx(self) -> int:
        return self.x + self.w // 2

    @property
    def centery(self) -> int:
        return self.y + self.h // 2

    @property
    def center(self) -> tuple[int, int]:
        return self.centerx, self.centery

    @property
    def topleft(self) -> tuple[int, int]:
        return self.x, self.y

    def inflate(self, dw: int, dh: int) -> "Rect":
        return Rect(self.x - dw // 2, self.y - dh // 2, self.w + dw, self.h + dh)

    def move(self, dx: int, dy: int) -> "Rect":
        return Rect(self.x + dx, self.y + dy, self.w, self.h)

    def collidepoint(self, x: int, y: int) -> bool:
        return self.x <= x <= self.right and self.y <= y <= self.bottom
