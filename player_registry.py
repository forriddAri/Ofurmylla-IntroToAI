from __future__ import annotations

from typing import Callable

from ari_ai import AI as AriAI
from arnkatla_ai import AI as ArnkatlaAI
from basic_logical_ai import BasicLogicalAI
from egill_ai import AI as EgillAI
from game import GameState
from human_player import HumanPlayer
from recursive_ai import RecursiveAI
from random_ai import RandomAI
from tumi_ai import AI as TumiAI


PlayerFactory = Callable[[str, GameState], object]


def _build_human(symbol: str, game: GameState):
    return HumanPlayer(symbol, game)


def _build_random_ai(symbol: str, game: GameState):
    return RandomAI(symbol, game)


def _build_basic_logical_ai(symbol: str, game: GameState):
    return BasicLogicalAI(symbol, game)


def _build_recursive_ai(symbol: str, game: GameState):
    return RecursiveAI(symbol, game)


def _build_ari_ai(symbol: str, game: GameState):
    return AriAI(symbol, game)


def _build_arnkatla_ai(symbol: str, game: GameState):
    return ArnkatlaAI(symbol, game)


def _build_tumi_ai(symbol: str, game: GameState):
    return TumiAI(symbol, game)


def _build_egill_ai(symbol: str, game: GameState):
    return EgillAI(symbol, game)

PLAYER_REGISTRY: dict[str, dict[str, object]] = {
    "human": {
        "label": "Human",
        "factory": _build_human,
        "is_human": True,
    },
    "random_ai": {
        "label": "Random AI",
        "factory": _build_random_ai,
        "is_human": False,
    },
    "basic_logical_ai": {
        "label": "Basic Logical AI",
        "factory": _build_basic_logical_ai,
        "is_human": False,
    },
    "recursive_ai": {
        "label": "Recursive AI",
        "factory": _build_recursive_ai,
        "is_human": False,
    },
    "ari_ai": {
        "label": "Ari AI",
        "factory": _build_ari_ai,
        "is_human": False,
    },
    "arnkatla_ai": {
        "label": "Arnkatla AI",
        "factory": _build_arnkatla_ai,
        "is_human": False,
    },
    "tumi_ai": {
        "label": "Tumi AI",
        "factory": _build_tumi_ai,
        "is_human": False,
    },
    "egill_ai": {
        "label": "Egill AI",
        "factory": _build_egill_ai,
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
