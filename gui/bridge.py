"""gui/bridge.py — 本地 GUI 桥接层"""
from __future__ import annotations
import queue, threading
from typing import Any, Optional

_lock = threading.Lock()
game_state: dict = {}
game_result: Optional[dict] = None
game_log: list = []
_MAX_LOG = 400
_req_q: queue.Queue = queue.Queue()
_rsp_q: queue.Queue = queue.Queue()
_RESET_TOKEN = object()


class LocalBridge:
    def __init__(self, game: Any) -> None:
        self.game = game

    def ask(self, player_idx: int, kind: str, data: dict) -> Any:
        _req_q.put({"player_idx": player_idx, "kind": kind, "data": data})
        val = _rsp_q.get()
        if val is _RESET_TOKEN:
            raise SystemExit
        return val

    def log(self, text: str, style: str = "normal") -> None:
        with _lock:
            game_log.append((text, style))
            if len(game_log) > _MAX_LOG:
                game_log.pop(0)

    def broadcast_state(self) -> None:
        with _lock:
            game_state.update(self.game.get_state())

    def broadcast_game_over(self, result: dict) -> None:
        global game_result
        with _lock:
            game_result = result
            game_state.update(self.game.get_state())


def get_pending_request() -> Optional[dict]:
    try: return _req_q.get_nowait()
    except queue.Empty: return None


def respond(value: Any) -> None:
    _rsp_q.put(value)


def reset():
    global game_result
    _rsp_q.put(_RESET_TOKEN)
    with _lock:
        game_log.clear()
        game_state.clear()
        game_result = None
    while not _req_q.empty():
        try: _req_q.get_nowait()
        except queue.Empty: break
