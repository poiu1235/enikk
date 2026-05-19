"""Shared game-control value objects."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Region:
    """A rectangle in screen coordinates."""

    left: int
    top: int
    width: int
    height: int

    def as_tuple(self) -> tuple[int, int, int, int]:
        return self.left, self.top, self.width, self.height
