from __future__ import annotations
import random
from game import GameState
from player_types import Move

class AI:
    def __init__(self, symbol: str, game: GameState, seed: int | None = None):
        self.symbol = symbol
        self.game = game
        self._rng = random.Random(seed)
        # How many moves ahead the AI looks — higher is stronger but slower
        self.MAX_DEPTH = 5

    def choose_move(self) -> Move | None:
        legal_moves = self.game.legal_moves()
        if not legal_moves:
            return None
        # Try every legal move and pick the one with the best minimax score
        best_move = None
        best_score = float('-inf')
        for move in legal_moves:
            state = self.game.simulate_move(move, self.symbol)
            if state is None:
                continue
            score = self._minimax(state, self.MAX_DEPTH, float('-inf'), float('inf'), False)
            if score > best_score:
                best_score = score
                best_move = move
        return best_move

    def _minimax(self, state: GameState, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
        # Stop when the game is over or we've looked far enough ahead
        if state.game_over or depth == 0:
            return self._evaluate(state)

        if maximizing:
            # Our turn — we want the highest possible score
            max_eval = float('-inf')
            for move in state.legal_moves():
                simulated = state.simulate_move(move, self.symbol)
                if simulated is None:
                    continue
                eval = self._minimax(simulated, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                # Opponent would never allow this branch, so stop searching it
                if beta <= alpha:
                    break
            return max_eval
        else:
            # Opponent's turn — they want the lowest possible score for us
            opponent = 'O' if self.symbol == 'X' else 'X'
            min_eval = float('inf')
            for move in state.legal_moves():
                simulated = state.simulate_move(move, opponent)
                if simulated is None:
                    continue
                eval = self._minimax(simulated, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                # We would never allow this branch, so stop searching it
                if beta <= alpha:
                    break
            return min_eval

    def _evaluate(self, state: GameState) -> float:
        opponent = 'O' if self.symbol == 'X' else 'X'
        # Terminal states get extreme scores
        if state.status == f"{self.symbol} wins":
            return 1000.0
        if state.status == f"{opponent} wins":
            return -1000.0
        if state.status == "Draw":
            return 0.0
        # For non-terminal states, count how many local boards each player owns
        score = 0.0
        for row in state.big_board:
            for cell in row:
                if cell == self.symbol:
                    score += 10.0
                elif cell == opponent:
                    score -= 10.0
        return score