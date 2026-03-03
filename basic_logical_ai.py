from __future__ import annotations

from player_types import GameSnapshot, Move


class BasicLogicalAI:
    def __init__(self, symbol: str):
        self.symbol = symbol

    def choose_move(self, state: GameSnapshot, legal_moves: list[Move]) -> Move | None:
        if not legal_moves:
            return None

        board = state["board"]
        opponent = "O" if self.symbol == "X" else "X"

        for move in legal_moves:
            if self._wins_subboard(board, move, self.symbol):
                return move

        for move in legal_moves:
            if self._wins_subboard(board, move, opponent):
                return move

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

    def _wins_subboard(self, board: list[list[str]], move: Move, symbol: str) -> bool:
        r, c = move
        sb_r, sb_c = r // 3, c // 3
        r0, c0 = sb_r * 3, sb_c * 3

        local = [[board[r0 + i][c0 + j] for j in range(3)] for i in range(3)]
        local[r % 3][c % 3] = symbol

        for i in range(3):
            if all(local[i][j] == symbol for j in range(3)):
                return True
            if all(local[j][i] == symbol for j in range(3)):
                return True

        if all(local[i][i] == symbol for i in range(3)):
            return True
        if all(local[i][2 - i] == symbol for i in range(3)):
            return True

        return False
