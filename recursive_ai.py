from __future__ import annotations

import atexit
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from math import inf
from threading import Lock
import time

from game import GameState
from player_types import Move

RECURSIVE_AI_SEARCH_DEPTH = 8
RECURSIVE_AI_PARALLEL_BACKEND = "process"
RECURSIVE_AI_PARALLEL_WORKERS = 0
RECURSIVE_AI_PROCESS_MIN_MOVES = 4
RECURSIVE_AI_USE_THREADS = False
RECURSIVE_AI_THREAD_WORKERS = 0
RECURSIVE_AI_USE_TRANSPOSITION_TABLE = True
RECURSIVE_AI_MAX_CACHE_ENTRIES = 200_000
RECURSIVE_AI_USE_OPENING_BOOK = True
RECURSIVE_AI_USE_ITERATIVE_DEEPENING = True
RECURSIVE_AI_MOVE_TIME_LIMIT_SECONDS = 5.0
RECURSIVE_AI_STOP_ON_BIG_SQUARE_WIN = True
RECURSIVE_AI_BIG_SQUARE_TERMINAL_SCORE = 12_000

TT_EXACT = "exact"
TT_LOWER = "lower"
TT_UPPER = "upper"


@dataclass(frozen=True)
class _TTEntry:
    depth: int
    value: float
    flag: str
    best_move: Move | None


@dataclass(frozen=True)
class _MoveUndo:
    r: int
    c: int
    sb_r: int
    sb_c: int
    turn: str
    game_over: bool
    status: str
    last_move: tuple[int, int] | None
    big_board_value: str | None


class _SearchTimeout(Exception):
    pass


_SHARED_PROCESS_POOL: ProcessPoolExecutor | None = None
_SHARED_PROCESS_POOL_LOCK = Lock()


def _get_shared_process_pool() -> ProcessPoolExecutor:
    global _SHARED_PROCESS_POOL

    with _SHARED_PROCESS_POOL_LOCK:
        if _SHARED_PROCESS_POOL is None:
            max_workers = None if RECURSIVE_AI_PARALLEL_WORKERS <= 0 else RECURSIVE_AI_PARALLEL_WORKERS
            _SHARED_PROCESS_POOL = ProcessPoolExecutor(max_workers=max_workers)
        return _SHARED_PROCESS_POOL


def _reset_shared_process_pool() -> None:
    global _SHARED_PROCESS_POOL

    with _SHARED_PROCESS_POOL_LOCK:
        if _SHARED_PROCESS_POOL is not None:
            _SHARED_PROCESS_POOL.shutdown(cancel_futures=True)
            _SHARED_PROCESS_POOL = None


atexit.register(_reset_shared_process_pool)


def _evaluate_root_move_in_process(args: tuple[str, GameState, Move, int, float | None]) -> tuple[Move, float | None]:
    symbol, root_state, move, search_depth, time_budget_seconds = args
    worker_ai = RecursiveAI(symbol, root_state)
    worker_ai.max_depth = search_depth

    if time_budget_seconds is not None:
        if time_budget_seconds <= 0:
            return move, None
        worker_ai._search_deadline = time.perf_counter() + time_budget_seconds

    simulated = root_state.simulate_move(move)
    if simulated is None:
        return move, None

    try:
        score = worker_ai._minimax(simulated, search_depth - 1, -inf, inf)
    except _SearchTimeout:
        return move, None

    return move, score


class RecursiveAI:
    def __init__(self, symbol: str, game: GameState):
        self.symbol = symbol
        self.game = game
        self.max_depth = max(1, RECURSIVE_AI_SEARCH_DEPTH)
        self.opponent = "O" if symbol == "X" else "X"
        self._transposition_table: dict[tuple[str, str, str, int, bool, str], _TTEntry] = {}
        self._tt_lock = Lock()
        self._search_deadline: float | None = None

    def choose_move(self) -> Move | None:
        legal_moves = self.game.legal_moves()
        if not legal_moves:
            return None

        if self.game.turn != self.symbol:
            return None

        opening_move = self._opening_book_move(legal_moves)
        if opening_move is not None:
            return opening_move

        forced_win = self.game.winning_bigboard_moves(self.symbol, legal_moves)
        if forced_win:
            return forced_win[0]

        must_block = self.game.winning_bigboard_moves(self.opponent, legal_moves)
        if must_block:
            return must_block[0]

        ordered_moves = self._ordered_moves(self.game, legal_moves, tactical=True)
        search_depth = self._effective_search_depth(self.game)

        cached_move = self._lookup_cached_root_move(self.game, ordered_moves, search_depth)
        if cached_move is not None:
            return cached_move

        if RECURSIVE_AI_USE_ITERATIVE_DEEPENING:
            return self._choose_move_iterative(ordered_moves, search_depth)

        best_move, best_score = self._choose_move_at_depth(ordered_moves, search_depth)
        self._store_exact_root(self.game, best_move, best_score, search_depth)
        return best_move

    def _choose_move_iterative(self, ordered_moves: list[Move], max_depth: int) -> Move:
        best_move = ordered_moves[0]
        best_score = -inf
        completed_depth = 0

        if RECURSIVE_AI_MOVE_TIME_LIMIT_SECONDS > 0:
            self._search_deadline = time.perf_counter() + RECURSIVE_AI_MOVE_TIME_LIMIT_SECONDS
        else:
            self._search_deadline = None

        try:
            for current_depth in range(1, max_depth + 1):
                if self._search_deadline is not None and time.perf_counter() >= self._search_deadline:
                    break

                cached_move = self._lookup_cached_root_move(self.game, ordered_moves, current_depth)
                if cached_move is not None:
                    best_move = cached_move
                    completed_depth = current_depth
                    continue

                try:
                    candidate_move, candidate_score = self._choose_move_at_depth(ordered_moves, current_depth)
                except _SearchTimeout:
                    break

                best_move = candidate_move
                best_score = candidate_score
                completed_depth = current_depth
                self._store_exact_root(self.game, best_move, best_score, current_depth)
        finally:
            self._search_deadline = None

        if completed_depth == 0:
            return ordered_moves[0]

        return best_move

    def _choose_move_at_depth(self, ordered_moves: list[Move], search_depth: int) -> tuple[Move, float]:
        if (
            RECURSIVE_AI_PARALLEL_BACKEND == "process"
            and len(ordered_moves) > 1
            and len(ordered_moves) >= RECURSIVE_AI_PROCESS_MIN_MOVES
        ):
            return self._choose_move_process_parallel(ordered_moves, search_depth)

        if (
            (RECURSIVE_AI_PARALLEL_BACKEND == "thread" or RECURSIVE_AI_USE_THREADS)
            and len(ordered_moves) > 1
        ):
            return self._choose_move_threaded(ordered_moves, search_depth)

        best_move = ordered_moves[0]
        best_score = -inf
        alpha = -inf
        beta = inf

        for move in ordered_moves:
            simulated = self.game.simulate_move(move)
            if simulated is None:
                continue

            score = self._minimax(simulated, search_depth - 1, alpha, beta)
            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, best_score)

        return best_move, best_score

    def _choose_move_process_parallel(self, ordered_moves: list[Move], search_depth: int) -> tuple[Move, float]:
        score_by_move: dict[Move, float] = {}

        time_budget_seconds: float | None = None
        if self._search_deadline is not None:
            time_budget_seconds = self._search_deadline - time.perf_counter()
            if time_budget_seconds <= 0:
                raise _SearchTimeout

        tasks = [
            (self.symbol, self.game, move, search_depth, time_budget_seconds)
            for move in ordered_moves
        ]

        try:
            process_pool = _get_shared_process_pool()
            for move, score in process_pool.map(_evaluate_root_move_in_process, tasks):
                if score is not None:
                    score_by_move[move] = score
            if not score_by_move and self._search_deadline is not None:
                raise _SearchTimeout
        except _SearchTimeout:
            raise
        except Exception:
            _reset_shared_process_pool()
            return self._choose_move_threaded(ordered_moves, search_depth)

        best_move = ordered_moves[0]
        best_score = -inf
        for move in ordered_moves:
            score = score_by_move.get(move)
            if score is None:
                continue
            if score > best_score:
                best_score = score
                best_move = move

        return best_move, best_score

    def _choose_move_threaded(self, ordered_moves: list[Move], search_depth: int) -> tuple[Move, float]:
        score_by_move: dict[Move, float] = {}

        max_workers = None if RECURSIVE_AI_THREAD_WORKERS <= 0 else RECURSIVE_AI_THREAD_WORKERS
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_by_move = {
                move: executor.submit(self._evaluate_root_move, move, search_depth)
                for move in ordered_moves
            }

            for move, future in future_by_move.items():
                score = future.result()
                if score is not None:
                    score_by_move[move] = score

        best_move = ordered_moves[0]
        best_score = -inf
        for move in ordered_moves:
            score = score_by_move.get(move)
            if score is None:
                continue
            if score > best_score:
                best_score = score
                best_move = move

        return best_move, best_score

    def _evaluate_root_move(self, move: Move, search_depth: int) -> float | None:
        simulated = self.game.simulate_move(move)
        if simulated is None:
            return None
        return self._minimax(simulated, search_depth - 1, -inf, inf)

    def _effective_search_depth(self, state: GameState) -> int:
        remaining_moves = sum(1 for row in state.board for cell in row if cell == "")
        return max(1, min(self.max_depth, remaining_moves))

    def _opening_book_move(self, legal_moves: list[Move]) -> Move | None:
        if not RECURSIVE_AI_USE_OPENING_BOOK:
            return None

        if self.game.last_move is not None:
            return None

        if any(cell for row in self.game.board for cell in row):
            return None

        center_move = (4, 4)
        if center_move in legal_moves:
            return center_move

        return None

    def _apply_move_inplace(self, state: GameState, move: Move) -> _MoveUndo | None:
        r, c = move
        if not state.is_move_legal(r, c):
            return None

        sb_r, sb_c = r // 3, c // 3
        undo = _MoveUndo(
            r=r,
            c=c,
            sb_r=sb_r,
            sb_c=sb_c,
            turn=state.turn,
            game_over=state.game_over,
            status=state.status,
            last_move=state.last_move,
            big_board_value=state.big_board[sb_r][sb_c],
        )

        if not state.apply_move(r, c):
            return None

        return undo

    def _undo_move_inplace(self, state: GameState, undo: _MoveUndo) -> None:
        state.board[undo.r][undo.c] = ""
        state.turn = undo.turn
        state.game_over = undo.game_over
        state.status = undo.status
        state.last_move = undo.last_move
        state.big_board[undo.sb_r][undo.sb_c] = undo.big_board_value

    def _minimax(self, state: GameState, depth: int, alpha: float, beta: float) -> float:
        self._check_timeout()

        terminal_score = self._terminal_score(state, depth)
        if terminal_score is not None:
            return terminal_score

        if depth == 0:
            return self._evaluate_state(state)

        initial_alpha = alpha
        initial_beta = beta
        state_key = self._state_key(state)

        cached = self._lookup_transposition(state_key, depth, alpha, beta)
        if cached is not None:
            if cached[0]:
                return cached[1]
            alpha = cached[1]
            beta = cached[2]

        cached_entry = self._get_transposition_entry(state_key)
        cached_best_move = cached_entry.best_move if cached_entry is not None else None

        legal_moves = state.legal_moves()
        if not legal_moves:
            return self._evaluate_state(state)

        ordered_moves = self._ordered_moves(state, legal_moves, tactical=False)
        if cached_best_move is not None and cached_best_move in ordered_moves:
            ordered_moves.remove(cached_best_move)
            ordered_moves.insert(0, cached_best_move)

        maximizing = state.turn == self.symbol

        if maximizing:
            value = -inf
            best_move: Move | None = None
            for move in ordered_moves:
                undo = self._apply_move_inplace(state, move)
                if undo is None:
                    continue

                try:
                    score = self._minimax(state, depth - 1, alpha, beta)
                finally:
                    self._undo_move_inplace(state, undo)
                if score > value:
                    value = score
                    best_move = move
                alpha = max(alpha, value)
                if alpha >= beta:
                    break

            if value == -inf:
                value = self._evaluate_state(state)
            self._store_transposition(state_key, depth, value, initial_alpha, initial_beta, best_move)
            return value

        value = inf
        best_move = None
        for move in ordered_moves:
            undo = self._apply_move_inplace(state, move)
            if undo is None:
                continue

            try:
                score = self._minimax(state, depth - 1, alpha, beta)
            finally:
                self._undo_move_inplace(state, undo)
            if score < value:
                value = score
                best_move = move
            beta = min(beta, value)
            if alpha >= beta:
                break

        if value == inf:
            value = self._evaluate_state(state)
        self._store_transposition(state_key, depth, value, initial_alpha, initial_beta, best_move)
        return value

    def _check_timeout(self) -> None:
        if self._search_deadline is None:
            return

        if time.perf_counter() >= self._search_deadline:
            raise _SearchTimeout

    def _state_key(self, state: GameState) -> tuple[str, str, str, int, bool, str]:
        board_key = "".join(cell if cell else "." for row in state.board for cell in row)
        big_board_key = "".join(cell if cell else "." for row in state.big_board for cell in row)
        if state.last_move is None:
            last_move_key = -1
        else:
            last_move_key = state.last_move[0] * 9 + state.last_move[1]
        return (
            board_key,
            big_board_key,
            state.turn,
            last_move_key,
            state.game_over,
            state.status,
        )

    def _get_transposition_entry(self, state_key: tuple[str, str, str, int, bool, str]) -> _TTEntry | None:
        if not RECURSIVE_AI_USE_TRANSPOSITION_TABLE:
            return None

        with self._tt_lock:
            return self._transposition_table.get(state_key)

    def _lookup_transposition(
        self,
        state_key: tuple[str, str, str, int, bool, str],
        depth: int,
        alpha: float,
        beta: float,
    ) -> tuple[bool, float, float] | None:
        entry = self._get_transposition_entry(state_key)
        if entry is None or entry.depth < depth:
            return None

        if entry.flag == TT_EXACT:
            return True, entry.value, entry.value

        next_alpha = alpha
        next_beta = beta

        if entry.flag == TT_LOWER:
            next_alpha = max(next_alpha, entry.value)
        elif entry.flag == TT_UPPER:
            next_beta = min(next_beta, entry.value)

        if next_alpha >= next_beta:
            return True, entry.value, entry.value

        return False, next_alpha, next_beta

    def _store_transposition(
        self,
        state_key: tuple[str, str, str, int, bool, str],
        depth: int,
        value: float,
        initial_alpha: float,
        initial_beta: float,
        best_move: Move | None,
    ) -> None:
        if not RECURSIVE_AI_USE_TRANSPOSITION_TABLE:
            return

        flag = TT_EXACT
        if value <= initial_alpha:
            flag = TT_UPPER
        elif value >= initial_beta:
            flag = TT_LOWER

        entry = _TTEntry(depth=depth, value=value, flag=flag, best_move=best_move)

        with self._tt_lock:
            existing = self._transposition_table.get(state_key)
            if existing is not None and existing.depth > depth:
                return

            if len(self._transposition_table) >= RECURSIVE_AI_MAX_CACHE_ENTRIES:
                self._transposition_table.clear()

            self._transposition_table[state_key] = entry

    def _lookup_cached_root_move(self, state: GameState, legal_moves: list[Move], search_depth: int) -> Move | None:
        if not RECURSIVE_AI_USE_TRANSPOSITION_TABLE:
            return None

        state_key = self._state_key(state)
        entry = self._get_transposition_entry(state_key)
        if entry is None:
            return None

        if entry.depth < search_depth or entry.flag != TT_EXACT:
            return None

        if entry.best_move is None or entry.best_move not in legal_moves:
            return None

        return entry.best_move

    def _store_exact_root(self, state: GameState, best_move: Move, best_score: float, search_depth: int) -> None:
        self._store_transposition(
            self._state_key(state),
            search_depth,
            best_score,
            -inf,
            inf,
            best_move,
        )

    def _terminal_score(self, state: GameState, depth: int) -> float | None:
        if state.game_over:
            if state.status == f"{self.symbol} wins":
                return 100_000 + depth
            if state.status == f"{self.opponent} wins":
                return -100_000 - depth
            return 0

        if RECURSIVE_AI_STOP_ON_BIG_SQUARE_WIN and state.last_move is not None:
            sb_r, sb_c = state.last_move[0] // 3, state.last_move[1] // 3
            winner = state.big_board[sb_r][sb_c]
            if winner == self.symbol:
                return RECURSIVE_AI_BIG_SQUARE_TERMINAL_SCORE + depth
            if winner == self.opponent:
                return -RECURSIVE_AI_BIG_SQUARE_TERMINAL_SCORE - depth

        return None

    def _ordered_moves(self, state: GameState, moves: list[Move], tactical: bool) -> list[Move]:
        winning_big: set[Move] = set()
        blocking_big: set[Move] = set()
        winning_sub: set[Move] = set()
        blocking_sub: set[Move] = set()

        if tactical:
            current = state.turn
            other = "O" if current == "X" else "X"
            winning_big = set(state.winning_bigboard_moves(current, moves))
            blocking_big = set(state.winning_bigboard_moves(other, moves))
            winning_sub = set(state.winning_subboard_moves(current, moves))
            blocking_sub = set(state.winning_subboard_moves(other, moves))

        def move_score(move: Move) -> int:
            score = 0
            if move in winning_big:
                score += 10_000
            if move in blocking_big:
                score += 8_000
            if move in winning_sub:
                score += 1_200
            if move in blocking_sub:
                score += 1_000

            local_r, local_c = move[0] % 3, move[1] % 3
            if (local_r, local_c) == (1, 1):
                score += 35
            elif (local_r, local_c) in {(0, 0), (0, 2), (2, 0), (2, 2)}:
                score += 20

            sb_r, sb_c = move[0] // 3, move[1] // 3
            if (sb_r, sb_c) == (1, 1):
                score += 8

            return score

        return sorted(moves, key=move_score, reverse=True)

    def _evaluate_state(self, state: GameState) -> float:
        score = 0.0

        for sb_r in range(3):
            for sb_c in range(3):
                owner = state.big_board[sb_r][sb_c]
                if owner == self.symbol:
                    score += 320
                elif owner == self.opponent:
                    score -= 320
                else:
                    score += self._evaluate_subboard(state, sb_r, sb_c)

        score += self._evaluate_bigboard_lines(state)

        if state.turn == self.symbol:
            score += 6
        else:
            score -= 6

        return score

    def _evaluate_bigboard_lines(self, state: GameState) -> float:
        score = 0.0
        b = state.big_board
        lines = [
            [b[r][0], b[r][1], b[r][2]] for r in range(3)
        ] + [
            [b[0][c], b[1][c], b[2][c]] for c in range(3)
        ] + [
            [b[0][0], b[1][1], b[2][2]],
            [b[0][2], b[1][1], b[2][0]],
        ]

        for line in lines:
            score += self._line_score(line, is_big=True)

        return score

    def _evaluate_subboard(self, state: GameState, sb_r: int, sb_c: int) -> float:
        r0, c0 = sb_r * 3, sb_c * 3
        local = [[state.board[r0 + i][c0 + j] for j in range(3)] for i in range(3)]

        lines = [
            [local[r][0], local[r][1], local[r][2]] for r in range(3)
        ] + [
            [local[0][c], local[1][c], local[2][c]] for c in range(3)
        ] + [
            [local[0][0], local[1][1], local[2][2]],
            [local[0][2], local[1][1], local[2][0]],
        ]

        score = 0.0
        for line in lines:
            score += self._line_score(line, is_big=False)

        center = local[1][1]
        if center == self.symbol:
            score += 3
        elif center == self.opponent:
            score -= 3

        return score

    def _line_score(self, line: list[str | None], is_big: bool) -> float:
        my_count = sum(1 for cell in line if cell == self.symbol)
        opp_count = sum(1 for cell in line if cell == self.opponent)

        if my_count > 0 and opp_count > 0:
            return 0

        if my_count > 0:
            if is_big:
                if my_count == 1:
                    return 35
                if my_count == 2:
                    return 240
                return 3_000

            if my_count == 1:
                return 3
            if my_count == 2:
                return 19
            return 110

        if opp_count > 0:
            if is_big:
                if opp_count == 1:
                    return -38
                if opp_count == 2:
                    return -260
                return -3_200

            if opp_count == 1:
                return -4
            if opp_count == 2:
                return -22
            return -120

        return 0