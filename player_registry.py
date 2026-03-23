from __future__ import annotations

from typing import Callable

from players.ai import AI as AI
from players.basic_logical_ai import BasicLogicalAI
from game import GameState
from players.human_player import HumanPlayer
from players.random_ai import RandomAI

PlayerFactory = Callable[[str, GameState], object]

def _build_human(symbol: str, game: GameState):
    return HumanPlayer(symbol, game)

def _build_random_ai(symbol: str, game: GameState):
    return RandomAI(symbol, game)

def _build_basic_logical_ai(symbol: str, game: GameState):
    return BasicLogicalAI(symbol, game)

def _build_ai(symbol: str, game: GameState):
    return AI(symbol, game)

PLAYER_REGISTRY: dict[str, dict[str, object]] = {
    "human": {
        "label": "Human",
        "factory": _build_human,
        "is_human": True,
    },
    "random_ai": {
        "label": "Random",
        "factory": _build_random_ai,
        "is_human": False,
    },
    "basic_logical_ai": {
        "label": "Basic Logical",
        "factory": _build_basic_logical_ai,
        "is_human": False,
    },
    "ai": {
        "label": "AI",
        "factory": _build_ai,
        "is_human": False,
    },
}


def get_player_options() -> list[tuple[str, str]]:
    return [(key, str(config["label"])) for key, config in PLAYER_REGISTRY.items()]


def build_player(symbol: str, player_type: str, game: GameState):
    config = PLAYER_REGISTRY.get(player_type, PLAYER_REGISTRY["human"])
    factory = config["factory"]
    return factory(symbol, game)


def is_human_type(player_type: str) -> bool:
    config = PLAYER_REGISTRY.get(player_type, PLAYER_REGISTRY["human"])
    return bool(config["is_human"])


def get_display_name(player_type: str, sign: str) -> str:
    if is_human_type(player_type):
        return "Player 1" if sign == "X" else "Player 2"
    config = PLAYER_REGISTRY.get(player_type, PLAYER_REGISTRY["human"])
    return str(config["label"])
