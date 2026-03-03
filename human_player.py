from __future__ import annotations

from player_types import Move


class HumanPlayer:
    def __init__(self, symbol: str):
        self.symbol = symbol

    def choose_move(self, state: dict, legal_moves: list[Move]) -> Move | None:
        return None
