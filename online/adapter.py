"""online/adapter.py — 将 AvalonGame 包装为 framework 的 AbstractGame"""
from __future__ import annotations
import sys, os
from typing import Any

try:
    from framework.core import AbstractGame, AbstractBridge
except ImportError as _e:
    raise ImportError(f"联机模式需要 gameplatform 框架。\n原始错误: {_e}")

_AVALON_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _AVALON_DIR not in sys.path:
    sys.path.insert(0, _AVALON_DIR)

from constants import MISSION_SIZES
from player import AvalonPlayer
from game import AvalonGame
from .state import serialize_state


class _OnlineBridge:
    def __init__(self, abstract_bridge: AbstractBridge, players: list) -> None:
        self._b = abstract_bridge
        self._players = players

    def ask(self, player_idx: int, kind: str, data: dict) -> Any:
        return self._b.ask(player_idx, kind, data)

    def log(self, text: str, style: str = "normal") -> None:
        self._b.log(text, style)

    def broadcast_state(self) -> None:
        self._b.broadcast_state()

    def broadcast_game_over(self, result: dict) -> None:
        self._b.broadcast_game_over(result)


class AvalonGameAdapter(AbstractGame):
    GAME_ID      = "avalon"
    GAME_NAME    = "阿瓦隆"
    MIN_PLAYERS  = 5
    MAX_PLAYERS  = 10
    COVER_IMAGE  = ""

    def __init__(self) -> None:
        self._engine = None
        self._players = []

    def setup(self, player_names: list, human_flags: list) -> None:
        players = [
            AvalonPlayer(name=name, idx=i, is_human=is_human)
            for i, (name, is_human) in enumerate(zip(player_names, human_flags))
        ]
        self._players = players
        bridge = _OnlineBridge(self.bridge, players)
        self._engine = AvalonGame(bridge=bridge)
        self._engine.setup(players)

    def run(self) -> None:
        if self._engine is None: raise RuntimeError("请先调用 setup()")
        self._engine.run()

    def get_state(self) -> dict:
        if self._engine is None: return {"phase": "waiting"}
        return serialize_state(self._engine)

    def on_player_disconnected(self, player_idx: int) -> None:
        if self._engine is None: return
        for p in self._engine.players:
            if p.idx == player_idx:
                p.is_human = False
                self.bridge.log(f"⚠ {p.name} 已断线，由 AI 接管", "warn")
                break
