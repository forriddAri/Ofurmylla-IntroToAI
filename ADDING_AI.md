# Adding a new AI player

This project is set up so each player type has its own file.

## 1) Create a new player file

Create a new file like `my_new_ai.py`.

Example:

```python
from __future__ import annotations

from player_types import Move


class MyNewAI:
    def __init__(self, symbol: str):
        self.symbol = symbol

    def choose_move(self, state: dict, legal_moves: list[Move]) -> Move | None:
        if not legal_moves:
            return None
        return legal_moves[0]
```

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
