"""online/state.py — 游戏状态序列化"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from game import AvalonGame

def serialize_state(game: "AvalonGame") -> dict:
    return game.get_state()
