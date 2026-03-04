from __future__ import annotations

import random

from game import GameState
from player_types import Move


class RandomAI:
    def __init__(self, symbol: str, game: GameState, seed: int | None = None):
        self.symbol = symbol
        self.game = game
        self._rng = random.Random(seed)

    def choose_move(self) -> Move | None:
        legal_moves = self.game.legal_moves()
        if not legal_moves:
            return None
        return self._rng.choice(legal_moves)
