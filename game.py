from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

GRID = 9
Move = tuple[int, int]


@dataclass
class GameState:
    board: list[list[str]] = field(default_factory=lambda: [["" for _ in range(GRID)] for _ in range(GRID)])
    turn: str = "X"
    game_over: bool = False
    status: str = ""
    last_move: tuple[int, int] | None = None
    big_board: list[list[str | None]] = field(default_factory=lambda: [[None for _ in range(3)] for _ in range(3)])

    def clone(self) -> GameState:
        return GameState(
            board=[row[:] for row in self.board],
            turn=self.turn,
            game_over=self.game_over,
            status=self.status,
            last_move=self.last_move,
            big_board=[row[:] for row in self.big_board],
        )

    def reset(self) -> None:
        self.board = [["" for _ in range(GRID)] for _ in range(GRID)]
        self.turn = "X"
        self.game_over = False
        self.status = ""
        self.last_move = None
        self.big_board = [[None for _ in range(3)] for _ in range(3)]

    def subboard_full(self, sb_r: int, sb_c: int) -> bool:
        r0, c0 = sb_r * 3, sb_c * 3
        for rr in range(r0, r0 + 3):
            for cc in range(c0, c0 + 3):
                if self.board[rr][cc] == "":
                    return False
        return True

    def allowed_subboards(self) -> list[tuple[int, int]]:
        playable = [
            (sr, sc)
            for sr in range(3)
            for sc in range(3)
            if self.big_board[sr][sc] is None and not self.subboard_full(sr, sc)
        ]

        if self.last_move is None:
            return playable

        r, c = self.last_move
        target = (r % 3, c % 3)
        if target in playable:
            return [target]

        return playable

    def check_subboard_win(self, sb_r: int, sb_c: int) -> str | None:
        r0, c0 = sb_r * 3, sb_c * 3

        for r in range(3):
            row = [self.board[r0 + r][c0 + c] for c in range(3)]
            if row[0] and row.count(row[0]) == 3:
                return row[0]

        for c in range(3):
            col = [self.board[r0 + r][c0 + c] for r in range(3)]
            if col[0] and col.count(col[0]) == 3:
                return col[0]

        d1 = [self.board[r0 + i][c0 + i] for i in range(3)]
        d2 = [self.board[r0 + i][c0 + 2 - i] for i in range(3)]

        if d1[0] and d1.count(d1[0]) == 3:
            return d1[0]
        if d2[0] and d2.count(d2[0]) == 3:
            return d2[0]

        return None

    def check_bigboard_win(self) -> str | None:
        for r in range(3):
            if self.big_board[r][0] and all(self.big_board[r][c] == self.big_board[r][0] for c in range(3)):
                return self.big_board[r][0]

        for c in range(3):
            if self.big_board[0][c] and all(self.big_board[r][c] == self.big_board[0][c] for r in range(3)):
                return self.big_board[0][c]

        if self.big_board[0][0] and all(self.big_board[i][i] == self.big_board[0][0] for i in range(3)):
            return self.big_board[0][0]

        if self.big_board[0][2] and all(self.big_board[i][2 - i] == self.big_board[0][2] for i in range(3)):
            return self.big_board[0][2]

        if not self.allowed_subboards():
            return "DRAW"

        return None

    def legal_moves(self) -> list[tuple[int, int]]:
        moves = []
        for sb_r, sb_c in self.allowed_subboards():
            if self.big_board[sb_r][sb_c] is not None:
                continue
            r0, c0 = sb_r * 3, sb_c * 3
            for rr in range(r0, r0 + 3):
                for cc in range(c0, c0 + 3):
                    if self.board[rr][cc] == "":
                        moves.append((rr, cc))
        return moves

    def is_move_legal(self, r: int, c: int) -> bool:
        if self.game_over:
            return False

        if not (0 <= r < GRID and 0 <= c < GRID):
            return False

        sb_r, sb_c = r // 3, c // 3
        if (sb_r, sb_c) not in self.allowed_subboards():
            return False

        if self.big_board[sb_r][sb_c] is not None:
            return False

        if self.board[r][c] != "":
            return False

        return True

    def would_win_subboard(self, move: Move, symbol: str) -> bool:
        r, c = move
        if not (0 <= r < GRID and 0 <= c < GRID):
            return False

        if self.board[r][c] != "":
            return False

        sb_r, sb_c = r // 3, c // 3
        if self.big_board[sb_r][sb_c] is not None:
            return False

        r0, c0 = sb_r * 3, sb_c * 3
        local = [[self.board[r0 + i][c0 + j] for j in range(3)] for i in range(3)]
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

    def winning_subboard_moves(self, symbol: str, moves: list[Move] | None = None) -> list[Move]:
        candidates = moves if moves is not None else self.legal_moves()
        return [move for move in candidates if self.would_win_subboard(move, symbol)]

    def simulate_move(self, move: Move, symbol: str | None = None) -> GameState | None:
        simulated = self.clone()
        if symbol is not None:
            simulated.turn = symbol
        if not simulated.apply_move(move[0], move[1]):
            return None
        return simulated

    def would_win_bigboard(self, move: Move, symbol: str) -> bool:
        simulated = self.simulate_move(move, symbol)
        return simulated is not None and simulated.status == f"{symbol} wins"

    def winning_bigboard_moves(self, symbol: str, moves: list[Move] | None = None) -> list[Move]:
        candidates = moves if moves is not None else self.legal_moves()
        return [move for move in candidates if self.would_win_bigboard(move, symbol)]

    def apply_move(self, r: int, c: int) -> bool:
        if not self.is_move_legal(r, c):
            return False

        sb_r, sb_c = r // 3, c // 3
        self.board[r][c] = self.turn
        self.last_move = (r, c)

        winner = self.check_subboard_win(sb_r, sb_c)
        if winner:
            self.big_board[sb_r][sb_c] = winner

        big_winner = self.check_bigboard_win()
        if big_winner == "DRAW":
            self.game_over = True
            self.status = "Draw"
        elif big_winner in ("X", "O"):
            self.game_over = True
            self.status = f"{big_winner} wins"
        else:
            self.turn = "O" if self.turn == "X" else "X"

        return True

    def snapshot(self) -> dict[str, Any]:
        return {
            "board": self.board,
            "big_board": self.big_board,
            "turn": self.turn,
            "last_move": self.last_move,
            "game_over": self.game_over,
        }