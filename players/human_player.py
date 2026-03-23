from __future__ import annotations

from game import GameState
from player_types import Move


class HumanPlayer:
    def __init__(self, symbol: str, game: GameState):
        self.symbol = symbol
        self.game = game

    def choose_move(self) -> Move | None:
        return None
