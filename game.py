"""game.py — 阿瓦隆核心游戏引擎"""
from __future__ import annotations
import random
from typing import Any

from constants import (
    Role, Alignment, ROLE_PRESETS, MISSION_SIZES,
    DOUBLE_FAIL_THRESHOLD, DOUBLE_FAIL_ROUND_IDX,
    VOTE_FAIL_LIMIT, WIN_MISSIONS, LOSE_MISSIONS, TOTAL_ROUNDS,
)
from player import AvalonPlayer
from ai import AvalonAI


ROLE_DESCRIPTIONS = {
    Role.MERLIN:        "你知道所有邪恶方（莫德雷德除外）。游戏结束时若被刺客猜中，邪恶方获胜。",
    Role.PERCIVAL:      "你能看到疑似梅林的玩家（梅林和莫甘娜均显示为疑似梅林）。",
    Role.LOYAL_SERVANT: "你是好人阵营，没有特殊能力。帮助好人完成三次任务！",
    Role.ASSASSIN:      "你是邪恶方的刺客。若好人完成三次任务，你可以尝试刺杀梅林。",
    Role.MORDRED:       "梅林看不到你的邪恶身份。暗中破坏任务！",
    Role.MORGANA:       "你会假扮成梅林迷惑派西维尔。邪恶方互相认识。",
    Role.OBERON:        "你是邪恶方，但你不认识其他邪恶方，他们也不认识你。独立行动！",
    Role.MINION:        "你是莫德雷德的爪牙，与其他邪恶方互相认识。暗中破坏任务！",
}


class AvalonGame:
    def __init__(self, bridge: Any) -> None:
        self.bridge = bridge
        self.players: list[AvalonPlayer] = []
        self.round_idx: int = 0
        self.leader_idx: int = 0
        self.vote_fail_count: int = 0
        self.mission_results: list[bool] = []
        self.vote_history: list[dict] = []
        self.phase: str = "waiting"
        self.winner: str | None = None
        self.end_reason: str = ""

    def setup(self, players: list[AvalonPlayer], roles=None) -> None:
        self.players = players
        n = len(players)
        if n not in MISSION_SIZES:
            raise ValueError(f"不支持的玩家人数: {n}（需要5-10人）")
        role_list = list(roles) if roles else self._build_role_list(n)
        random.shuffle(role_list)
        for p, r in zip(self.players, role_list):
            p.assign_role(r)
        self.leader_idx = random.randint(0, n - 1)

    def _build_role_list(self, n):
        preset = ROLE_PRESETS[n]
        good_roles = list(preset["required_good"])
        evil_roles = list(preset["required_evil"])
        opt_good = list(preset["optional_good"])
        opt_evil = list(preset["optional_evil"])
        while len(good_roles) < preset["good"] and opt_good:
            good_roles.append(opt_good.pop(0))
        while len(evil_roles) < preset["evil"] and opt_evil:
            evil_roles.append(opt_evil.pop(0))
        while len(good_roles) < preset["good"]:
            good_roles.append(Role.LOYAL_SERVANT)
        while len(evil_roles) < preset["evil"]:
            evil_roles.append(Role.MINION)
        return good_roles + evil_roles

    def run(self) -> None:
        self._night_phase()
        for self.round_idx in range(TOTAL_ROUNDS):
            self._run_round()
            good_wins = self.mission_results.count(True)
            evil_wins = self.mission_results.count(False)
            if good_wins >= WIN_MISSIONS:
                self._assassination_phase()
                return
            if evil_wins >= LOSE_MISSIONS:
                self._end_evil_wins("任务失败三次，邪恶方获胜！")
                return

    def _night_phase(self):
        self.phase = "night"
        self.bridge.log("═════ 夜晚阶段：闭上眼睛 ═════", "header")
        self.bridge.broadcast_state()
        evil_idxs = [p.idx for p in self.players if p.is_evil and p.role != Role.OBERON]
        merlin_sees = [p.idx for p in self.players if p.is_evil and p.role != Role.MORDRED]
        percival_sees = ([p.idx for p in self.players if p.role == Role.MERLIN] +
                         [p.idx for p in self.players if p.role == Role.MORGANA])
        for p in self.players:
            info = self._build_night_info(p, evil_idxs, merlin_sees, percival_sees)
            if p.is_human:
                self.bridge.ask(p.idx, "show_role", info)
        self.bridge.log("═════ 睁开眼睛，游戏开始！═════", "header")
        self.bridge.broadcast_state()

    def _build_night_info(self, p, evil_idxs, merlin_sees, percival_sees):
        visible = []
        if p.role == Role.MERLIN:
            for idx in merlin_sees:
                q = self.players[idx]
                visible.append({"idx": idx, "name": q.name, "hint": "邪恶方"})
        elif p.role == Role.PERCIVAL:
            for idx in percival_sees:
                q = self.players[idx]
                visible.append({"idx": idx, "name": q.name, "hint": "疑似梅林"})
        elif p.is_evil and p.role != Role.OBERON:
            for idx in evil_idxs:
                if idx != p.idx:
                    q = self.players[idx]
                    visible.append({"idx": idx, "name": q.name, "hint": "邪恶同伴"})
        return {
            "your_idx": p.idx, "your_name": p.name,
            "your_role": p.role.value, "alignment": p.alignment.value,
            "visible": visible,
            "role_desc": ROLE_DESCRIPTIONS.get(p.role, ""),
        }

    def _run_round(self):
        round_num = self.round_idx + 1
        n = len(self.players)
        team_size = MISSION_SIZES[n][self.round_idx]
        self.vote_fail_count = 0
        self.bridge.log(f"══ 第 {round_num} 轮任务（需 {team_size} 人出任务）══", "header")

        while True:
            leader = self.players[self.leader_idx]
            self.phase = f"round{round_num}_select"
            self.bridge.log(f"► 队长：{leader.name}，请选 {team_size} 名队员", "section")
            self.bridge.broadcast_state()

            team_idxs = self._team_select_phase(leader, team_size)
            team_names = [self.players[i].name for i in team_idxs]
            self.bridge.log(f"  提名队伍：{', '.join(team_names)}", "normal")

            self.phase = f"round{round_num}_vote"
            self.bridge.broadcast_state()
            approve, votes = self._team_vote_phase(team_idxs)
            approve_count = sum(1 for v in votes.values() if v)
            reject_count  = sum(1 for v in votes.values() if not v)
            self.bridge.log(
                f"  投票结果：赞成 {approve_count} vs 反对 {reject_count} "
                f"→ {'✅ 通过' if approve else '❌ 否决'}",
                "section" if approve else "warn",
            )

            self.vote_history.append({
                "round": round_num, "leader_idx": self.leader_idx,
                "team_idxs": team_idxs, "votes": votes, "approved": approve,
            })
            self.bridge.broadcast_state()

            if approve:
                self.vote_fail_count = 0
                break
            else:
                self.vote_fail_count += 1
                if self.vote_fail_count >= VOTE_FAIL_LIMIT:
                    self._end_evil_wins("连续 5 次投票否决，邪恶方获胜！")
                    return
                self.bridge.log(
                    f"  ⚠ 连续投票失败 {self.vote_fail_count}/{VOTE_FAIL_LIMIT} 次", "warn"
                )
                self.leader_idx = (self.leader_idx + 1) % len(self.players)

        self.phase = f"round{round_num}_mission"
        self.bridge.broadcast_state()
        success, fail_count = self._mission_phase(team_idxs)
        self.mission_results.append(success)
        self.bridge.log(
            f"  任务结果：{'✅ 成功' if success else f'❌ 失败（{fail_count} 张失败牌）'}",
            "section" if success else "warn",
        )
        self.bridge.broadcast_state()
        self.leader_idx = (self.leader_idx + 1) % len(self.players)

    def _team_select_phase(self, leader, team_size):
        if leader.is_human:
            result = self.bridge.ask(leader.idx, "select_team", {
                "team_size": team_size,
                "player_names": [p.name for p in self.players],
                "leader_idx": leader.idx,
            })
            if isinstance(result, list):
                result = [int(i) for i in result[:team_size]]
                while len(result) < team_size:
                    for i in range(len(self.players)):
                        if i not in result:
                            result.append(i); break
                return result
        return AvalonAI.select_team(leader, self.players, team_size,
                                    self.round_idx, self.vote_history, self.mission_results)

    def _team_vote_phase(self, team_idxs):
        votes = {}
        for p in self.players:
            if p.is_human:
                val = self.bridge.ask(p.idx, "vote_team", {
                    "team_idxs": team_idxs,
                    "team_names": [self.players[i].name for i in team_idxs],
                })
                votes[p.idx] = bool(val)
            else:
                votes[p.idx] = AvalonAI.vote_team(p, team_idxs, self.players,
                                                   self.round_idx, self.vote_history, self.mission_results)
        approve = sum(1 for v in votes.values() if v) > len(self.players) / 2
        return approve, votes

    def _mission_phase(self, team_idxs):
        n = len(self.players)
        need_double = (n in DOUBLE_FAIL_THRESHOLD and self.round_idx == DOUBLE_FAIL_ROUND_IDX)
        cards = []
        for idx in team_idxs:
            p = self.players[idx]
            if p.is_human:
                val = self.bridge.ask(p.idx, "play_mission", {
                    "round_num": self.round_idx + 1,
                    "can_fail": p.is_evil,
                })
                cards.append(bool(val))
            else:
                cards.append(AvalonAI.play_mission(p, self.round_idx, self.mission_results))
        random.shuffle(cards)
        fail_count = cards.count(False)
        success = fail_count < 2 if need_double else fail_count == 0
        return success, fail_count

    def _assassination_phase(self):
        self.phase = "assassination"
        self.bridge.log("══ 刺杀阶段 ══", "header")
        self.bridge.log("  好人阵营完成了三次任务！刺客，你有最后一次机会……", "section")
        self.bridge.broadcast_state()
        assassin = next((p for p in self.players if p.role == Role.ASSASSIN), None)
        if assassin is None:
            self._end_good_wins("任务成功，好人获胜！（无刺客角色）"); return
        good_players = [p for p in self.players if p.is_good]
        if assassin.is_human:
            target_idx = self.bridge.ask(assassin.idx, "assassinate", {
                "assassin_name": assassin.name,
                "candidate_idxs": [p.idx for p in good_players],
                "candidate_names": [p.name for p in good_players],
            })
            target_idx = int(target_idx) if target_idx is not None else good_players[0].idx
        else:
            target_idx = AvalonAI.assassinate(assassin, self.players, self.vote_history, self.mission_results)
        target = self.players[target_idx]
        self.bridge.log(f"  {assassin.name} 刺杀了 {target.name}！", "section")
        if target.role == Role.MERLIN:
            self.bridge.log("  ✦ 梅林身份暴露！邪恶方获胜！", "warn")
            self._end_evil_wins(f"刺客刺杀了梅林（{target.name}），邪恶方获胜！")
        else:
            merlin_name = next((p.name for p in self.players if p.role == Role.MERLIN), "?")
            self.bridge.log(f"  {target.name} 不是梅林（真正的梅林是 {merlin_name}）", "section")
            self._end_good_wins("刺杀失败，好人阵营获胜！")

    def _end_good_wins(self, reason):
        self.winner = "good"; self.end_reason = reason; self.phase = "game_over"
        self.bridge.log(f"🏆 {reason}", "header")
        self.bridge.broadcast_state(); self.bridge.broadcast_game_over(self._build_result())

    def _end_evil_wins(self, reason):
        self.winner = "evil"; self.end_reason = reason; self.phase = "game_over"
        self.bridge.log(f"👿 {reason}", "warn")
        self.bridge.broadcast_state(); self.bridge.broadcast_game_over(self._build_result())

    def get_state(self) -> dict:
        n = len(self.players)
        return {
            "phase": self.phase, "round_idx": self.round_idx,
            "round_num": self.round_idx + 1, "leader_idx": self.leader_idx,
            "vote_fail_count": self.vote_fail_count,
            "mission_results": self.mission_results,
            "vote_history": self.vote_history[-6:],
            "mission_sizes": MISSION_SIZES.get(n, []),
            "winner": self.winner, "end_reason": self.end_reason,
            "players": [
                {"idx": p.idx, "name": p.name, "is_human": p.is_human,
                 "role": p.role.value if (self.phase == "game_over" and p.role) else None,
                 "alignment": p.alignment.value if (self.phase == "game_over" and p.alignment) else None}
                for p in self.players
            ],
        }

    def _build_result(self):
        return {
            "winner": self.winner, "end_reason": self.end_reason,
            "players": [{"idx": p.idx, "name": p.name,
                          "role": p.role.value if p.role else None,
                          "alignment": p.alignment.value if p.alignment else None}
                        for p in self.players],
            "mission_results": self.mission_results,
        }
