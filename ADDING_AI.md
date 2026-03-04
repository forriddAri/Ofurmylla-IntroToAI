# Adding a new AI player

This project is set up so each player type has its own file.

## 1) Create a new player file

Create a new file like `my_new_ai.py`.

Example:

```python
from __future__ import annotations

from game import GameState
from player_types import Move


class MyNewAI:
    def __init__(self, symbol: str, game: GameState):
        self.symbol = symbol
        self.game = game

    def choose_move(self) -> Move | None:
        legal_moves = self.game.legal_moves()
        if not legal_moves:
            return None
        return legal_moves[0]
```

`choose_move()` is executed off the main UI thread by the game loop infrastructure, so new AI implementations do not need to handle threading themselves.

`GameState` also provides helpers that are useful for smarter AIs:

- `winning_subboard_moves(symbol)`
- `winning_bigboard_moves(symbol)`
- `simulate_move(move, symbol=None)`
- `clone()`

## 2) Register it in `player_registry.py`

- Import your class.
- Add a builder function.
- Add one entry in `PLAYER_REGISTRY`.

Example entry:

```python
"my_new_ai": {
    "label": "My New AI",
    "factory": _build_my_new_ai,
    "is_human": False,
},
```

That is all — the dropdown menu and winner labels update automatically.
