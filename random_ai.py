from __future__ import annotations

import random

from player_types import GameSnapshot, Move


class RandomAI:
    def __init__(self, symbol: str, seed: int | None = None):
        self.symbol = symbol
        self._rng = random.Random(seed)

    def choose_move(self, state: GameSnapshot, legal_moves: list[Move]) -> Move | None:
        if not legal_moves:
            return None
        return self._rng.choice(legal_moves)
