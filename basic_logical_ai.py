from __future__ import annotations

from game import GameState
from player_types import Move


class BasicLogicalAI:
    def __init__(self, symbol: str, game: GameState):
        self.symbol = symbol
        self.game = game

    def choose_move(self) -> Move | None:
        legal_moves = self.game.legal_moves()
        if not legal_moves:
            return None

        opponent = "O" if self.symbol == "X" else "X"

        winning_big_moves = self.game.winning_bigboard_moves(self.symbol, legal_moves)
        if winning_big_moves:
            return winning_big_moves[0]

        blocking_big_moves = self.game.winning_bigboard_moves(opponent, legal_moves)
        if blocking_big_moves:
            return blocking_big_moves[0]

        winning_sub_moves = self.game.winning_subboard_moves(self.symbol, legal_moves)
        if winning_sub_moves:
            return winning_sub_moves[0]

        blocking_sub_moves = self.game.winning_subboard_moves(opponent, legal_moves)
        if blocking_sub_moves:
            return blocking_sub_moves[0]

        centers = [move for move in legal_moves if move[0] % 3 == 1 and move[1] % 3 == 1]
        if centers:
            return centers[0]

        corners = [
            move
            for move in legal_moves
            if (move[0] % 3, move[1] % 3) in {(0, 0), (0, 2), (2, 0), (2, 2)}
        ]
        if corners:
            return corners[0]

        return legal_moves[0]
