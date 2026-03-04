from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from game import GameState

Move = tuple[int, int]


class Player(Protocol):
    symbol: str
    game: GameState

    def choose_move(self) -> Move | None:
        ...
