"""ai.py — 阿瓦隆 AI 决策模块"""
from __future__ import annotations
import random
from constants import Role, Alignment
from player import AvalonPlayer


class AvalonAI:
    @staticmethod
    def select_team(leader, players, team_size, round_idx, vote_history, mission_results):
        n = len(players)
        all_idxs = list(range(n))
        if leader.is_evil:
            evil_idxs = [p.idx for p in players if p.is_evil and p.idx != leader.idx]
            good_wins = mission_results.count(True)
            need_evil = good_wins >= 2 or round_idx >= 3
            if need_evil and evil_idxs:
                team = [leader.idx]
                random.shuffle(evil_idxs)
                for ei in evil_idxs:
                    if len(team) < team_size: team.append(ei)
                remaining = [i for i in all_idxs if i not in team]
                random.shuffle(remaining)
                while len(team) < team_size: team.append(remaining.pop())
                return team[:team_size]
            else:
                team = [leader.idx]
                others = [i for i in all_idxs if i != leader.idx]
                random.shuffle(others)
                while len(team) < team_size: team.append(others.pop())
                return team[:team_size]
        else:
            trust = _compute_trust_scores(players, vote_history, mission_results)
            team = [leader.idx]
            candidates = sorted([(trust.get(i, 50), i) for i in all_idxs if i != leader.idx], reverse=True)
            for _, ci in candidates:
                if len(team) >= team_size: break
                team.append(ci)
            return team[:team_size]

    @staticmethod
    def vote_team(player, team_idxs, players, round_idx, vote_history, mission_results):
        if player.is_evil:
            evil_in_team = sum(1 for i in team_idxs if players[i].is_evil)
            if evil_in_team == 0:
                return random.random() < 0.10
            if evil_in_team >= 1:
                return random.random() < 0.85
            return random.random() < 0.5
        else:
            trust = _compute_trust_scores(players, vote_history, mission_results)
            avg_trust = sum(trust.get(i, 50) for i in team_idxs) / len(team_idxs)
            vote_fail = sum(1 for vh in vote_history[-5:] if not vh.get("approved", True))
            threshold = max(35, 65 - vote_fail * 8)
            return avg_trust >= threshold

    @staticmethod
    def play_mission(player, round_idx, mission_results):
        if player.is_good: return True
        good_wins = mission_results.count(True)
        evil_wins = mission_results.count(False)
        if good_wins >= 2: return False
        if evil_wins >= 2: return False
        if round_idx == 0: return random.random() < 0.70
        if round_idx == 1: return random.random() < 0.50
        return False

    @staticmethod
    def assassinate(assassin, players, vote_history, mission_results):
        good_players = [p for p in players if p.is_good]
        if not good_players: return players[0].idx
        merlin_score = {p.idx: 0.0 for p in good_players}
        for vh in vote_history:
            evil_in_team = sum(1 for i in vh.get("team_idxs",[]) if players[i].is_evil)
            for p in good_players:
                voted_approve = bool(vh.get("votes",{}).get(p.idx, True))
                if evil_in_team >= 1 and not voted_approve:
                    merlin_score[p.idx] += 2.0
                elif evil_in_team == 0 and voted_approve:
                    merlin_score[p.idx] += 0.5
                elif evil_in_team >= 1 and voted_approve:
                    merlin_score[p.idx] -= 0.5
        for idx in merlin_score:
            merlin_score[idx] += random.uniform(-1.0, 1.0)
        target = max(good_players, key=lambda p: merlin_score.get(p.idx, 0))
        return target.idx


def _compute_trust_scores(players, vote_history, mission_results):
    scores = {p.idx: 50.0 for p in players}
    for vh in vote_history:
        round_of_mission = vh.get("round", 1) - 1
        if round_of_mission >= len(mission_results): continue
        mission_success = mission_results[round_of_mission]
        votes = vh.get("votes", {})
        approved = vh.get("approved", True)
        for player_idx, voted_approve in votes.items():
            voted_approve = bool(voted_approve)
            if approved:
                if mission_success and voted_approve:
                    scores[player_idx] = min(100, scores[player_idx] + 8)
                elif not mission_success and voted_approve:
                    scores[player_idx] = max(0, scores[player_idx] - 12)
                elif mission_success and not voted_approve:
                    scores[player_idx] = max(0, scores[player_idx] - 5)
                elif not mission_success and not voted_approve:
                    scores[player_idx] = min(100, scores[player_idx] + 10)
    return scores
