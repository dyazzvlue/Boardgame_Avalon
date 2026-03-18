"""main.py — 阿瓦隆 CLI 文字模式入口
用法: python main.py [人数]
"""
from __future__ import annotations
import sys, os, random
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path: sys.path.insert(0, _HERE)

from constants import MISSION_SIZES
from player import AvalonPlayer
from game import AvalonGame


class _CliBridge:
    def __init__(self, game): self.game = game

    def ask(self, player_idx, kind, data):
        p = self.game.players[player_idx]
        if kind == "show_role":
            print(f"\n[{p.name}] 角色：{data['your_role']} ({data['alignment']})")
            if data.get("visible"):
                for v in data["visible"]: print(f"  你能看到：{v['name']} — {v['hint']}")
            if p.is_human: input("  按 Enter 确认...")
            return True
        elif kind == "select_team":
            ts = data["team_size"]; names = data["player_names"]
            print(f"\n[{p.name}] 选择 {ts} 名队员：")
            for i, n in enumerate(names): print(f"  [{i}] {n}")
            if p.is_human:
                while True:
                    try:
                        chosen = [int(x) for x in input("编号(空格分隔): ").split() if x.isdigit()]
                        chosen = [c for c in chosen if 0 <= c < len(names)]
                        if len(chosen) == ts: return chosen
                    except: pass
            return list(range(ts))
        elif kind == "vote_team":
            names = data.get("team_names", [])
            print(f"\n[{p.name}] 投票 [{', '.join(names)}] 赞成(y)/反对(n)?")
            if p.is_human:
                while True:
                    v = input("  > ").strip().lower()
                    if v in ("y","yes"): return True
                    if v in ("n","no"): return False
            return random.choice([True, False])
        elif kind == "play_mission":
            can_fail = data.get("can_fail", False)
            print(f"\n[{p.name}] 任务牌 成功(y)" + ("/失败(n)" if can_fail else ""))
            if p.is_human:
                while True:
                    v = input("  > ").strip().lower()
                    if v in ("y","yes"): return True
                    if can_fail and v in ("n","no"): return False
            return True
        elif kind == "assassinate":
            cnames = data.get("candidate_names", []); cidxs = data.get("candidate_idxs", [])
            print(f"\n[{p.name}] 刺杀目标：")
            for ci, (idx, name) in enumerate(zip(cidxs, cnames)): print(f"  [{ci}] {name}")
            if p.is_human:
                while True:
                    try:
                        v = int(input("编号: ").strip())
                        if 0 <= v < len(cidxs): return cidxs[v]
                    except: pass
            return cidxs[0] if cidxs else 0
        return None

    def log(self, text, style="normal"): print(text)
    def broadcast_state(self): pass
    def broadcast_game_over(self, result):
        print("\n" + "═"*50)
        print(f"游戏结束！赢家：{'好人' if result['winner']=='good' else '邪恶方'}")
        print(result.get("end_reason", ""))
        print("\n角色揭示：")
        for p in result.get("players", []):
            print(f"  {p['name']:10s}  {p.get('role','?'):12s}  {p.get('alignment','?')}")


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    if n not in MISSION_SIZES:
        print(f"人数 {n} 不支持，使用5人"); n = 5
    print(f"\n══ 阿瓦隆 {n}人局 ══")
    players = [AvalonPlayer(name=f"玩家{i+1}", idx=i, is_human=False) for i in range(n)]
    players[0].is_human = True
    game = AvalonGame(bridge=None)
    b = _CliBridge(game); game.bridge = b
    game.setup(players)
    game.run()

if __name__ == "__main__":
    main()
