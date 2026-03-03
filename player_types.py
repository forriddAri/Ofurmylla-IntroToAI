from __future__ import annotations

from typing import Any, Protocol

Move = tuple[int, int]


class Player(Protocol):
    symbol: str

    def choose_move(self, state: dict[str, Any], legal_moves: list[Move]) -> Move | None:
        ...
