"""
constants.py — 阿瓦隆 (Avalon) 常量与配置
"""
from __future__ import annotations
from enum import Enum


class Role(Enum):
    MERLIN          = "梅林"
    PERCIVAL        = "派西维尔"
    LOYAL_SERVANT   = "亚瑟的忠臣"
    ASSASSIN        = "刺客"
    MORDRED         = "莫德雷德"
    MORGANA         = "莫甘娜"
    OBERON          = "奥伯倫"
    MINION          = "莫德雷德的爪牙"


class Alignment(Enum):
    GOOD = "好人"
    EVIL = "坏人"


ROLE_ALIGNMENT = {
    Role.MERLIN:        Alignment.GOOD,
    Role.PERCIVAL:      Alignment.GOOD,
    Role.LOYAL_SERVANT: Alignment.GOOD,
    Role.ASSASSIN:      Alignment.EVIL,
    Role.MORDRED:       Alignment.EVIL,
    Role.MORGANA:       Alignment.EVIL,
    Role.OBERON:        Alignment.EVIL,
    Role.MINION:        Alignment.EVIL,
}

ROLE_PRESETS = {
    5:  {"good": 3, "evil": 2, "required_good": [Role.MERLIN], "required_evil": [Role.ASSASSIN],
         "optional_good": [Role.PERCIVAL, Role.LOYAL_SERVANT],
         "optional_evil": [Role.MORDRED, Role.MORGANA, Role.MINION]},
    6:  {"good": 4, "evil": 2, "required_good": [Role.MERLIN], "required_evil": [Role.ASSASSIN],
         "optional_good": [Role.PERCIVAL, Role.LOYAL_SERVANT],
         "optional_evil": [Role.MORDRED, Role.MORGANA, Role.MINION]},
    7:  {"good": 4, "evil": 3, "required_good": [Role.MERLIN], "required_evil": [Role.ASSASSIN],
         "optional_good": [Role.PERCIVAL, Role.LOYAL_SERVANT],
         "optional_evil": [Role.MORDRED, Role.MORGANA, Role.OBERON, Role.MINION]},
    8:  {"good": 5, "evil": 3, "required_good": [Role.MERLIN], "required_evil": [Role.ASSASSIN],
         "optional_good": [Role.PERCIVAL, Role.LOYAL_SERVANT],
         "optional_evil": [Role.MORDRED, Role.MORGANA, Role.OBERON, Role.MINION]},
    9:  {"good": 6, "evil": 3, "required_good": [Role.MERLIN], "required_evil": [Role.ASSASSIN],
         "optional_good": [Role.PERCIVAL, Role.LOYAL_SERVANT],
         "optional_evil": [Role.MORDRED, Role.MORGANA, Role.OBERON, Role.MINION]},
    10: {"good": 6, "evil": 4, "required_good": [Role.MERLIN], "required_evil": [Role.ASSASSIN],
         "optional_good": [Role.PERCIVAL, Role.LOYAL_SERVANT],
         "optional_evil": [Role.MORDRED, Role.MORGANA, Role.OBERON, Role.MINION]},
}

MISSION_SIZES = {
    5:  [2, 3, 2, 3, 3],
    6:  [2, 3, 4, 3, 4],
    7:  [2, 3, 3, 4, 4],
    8:  [3, 4, 4, 5, 5],
    9:  [3, 4, 4, 5, 5],
    10: [3, 4, 4, 5, 5],
}

DOUBLE_FAIL_THRESHOLD = {7: 3, 8: 3, 9: 3, 10: 3}
DOUBLE_FAIL_ROUND_IDX = 3
VOTE_FAIL_LIMIT = 5
TOTAL_ROUNDS    = 5
WIN_MISSIONS    = 3
LOSE_MISSIONS   = 3
