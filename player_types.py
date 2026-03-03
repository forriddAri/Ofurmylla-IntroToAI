from __future__ import annotations

from typing import Protocol, TypedDict

Move = tuple[int, int]


class GameSnapshot(TypedDict):
    board: list[list[str]]
    big_board: list[list[str | None]]
    turn: str
    last_move: tuple[int, int] | None
    game_over: bool


class Player(Protocol):
    symbol: str

    def choose_move(self, state: GameSnapshot, legal_moves: list[Move]) -> Move | None:
        ...
