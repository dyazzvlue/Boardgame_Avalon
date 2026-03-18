"""
gui/renderer.py — pygame 渲染器（圆桌布局）
"""
from __future__ import annotations
import math
from typing import Any, Optional

import pygame
import gui.bridge as bridge

BG          = (15,  20,  40)
PANEL_BG    = (22,  30,  55)
PANEL_DARK  = (12,  16,  32)
BORDER      = (45,  70, 120)
TEXT        = (210, 215, 230)
TEXT_DIM    = (120, 130, 155)
TEXT_BRIGHT = (255, 255, 255)
GOLD        = (215, 170,  45)
GREEN       = ( 45, 175,  80)
RED         = (200,  50,  55)
BTN_NORMAL  = ( 30,  55,  90)
BTN_HOVER   = ( 50,  90, 145)
BTN_SEL     = ( 45, 140,  65)
BTN_TEXT    = (215, 228, 245)
GOOD_COLOR  = ( 60, 120, 210)
EVIL_COLOR  = (200,  50,  50)
MISSION_WIN  = ( 50, 170,  80)
MISSION_LOSE = (200,  50,  55)
MISSION_NONE = ( 50,  55,  80)

ROLE_COLORS = {
    "梅林":        ( 80, 130, 220),
    "派西维尔":    ( 80, 180, 200),
    "亚瑟的忠臣":  ( 60, 110, 180),
    "刺客":        (200,  45,  55),
    "莫德雷德":    (160,  40,  70),
    "莫甘娜":      (190,  70, 150),
    "奥伯倫":      (150,  60, 180),
    "莫德雷德的爪牙": (130, 40, 40),
}

W, H = 1280, 800
TABLE_CX, TABLE_CY = 420, 370
TABLE_RX, TABLE_RY = 310, 240

_font_cache: dict = {}

def _font(size: int, bold: bool = False) -> pygame.font.Font:
    key = (size, bold)
    if key in _font_cache: return _font_cache[key]
    candidates = ["notosanscjksc","notosanscjk","wqyzenhei","simhei","microsoftyahei","unifont"]
    f = None
    for name in candidates:
        path = pygame.font.match_font(name, bold=bold)
        if path: f = pygame.font.Font(path, size); break
    if f is None: f = pygame.font.SysFont(None, size)
    _font_cache[key] = f
    return f

def _text(surf, txt, pos, color=TEXT, size=16, bold=False, center=False, right=False):
    f = _font(size, bold)
    s = f.render(str(txt), True, color)
    r = s.get_rect()
    if center: r.center = pos
    elif right: r.topright = pos
    else: r.topleft = pos
    surf.blit(s, r)

def _btn(surf, rect, label, hover=False, selected=False, color=None):
    c = color or (BTN_SEL if selected else BTN_HOVER if hover else BTN_NORMAL)
    pygame.draw.rect(surf, c, rect, border_radius=6)
    pygame.draw.rect(surf, BORDER, rect, 1, border_radius=6)
    _text(surf, label, rect.center, BTN_TEXT, 15, center=True)


class Button:
    def __init__(self, rect, label, value=None, color=None, toggle=False):
        self.rect = pygame.Rect(rect)
        self.label = label; self.value = value; self.color = color
        self.toggle = toggle; self.selected = False; self.hovered = False

    def draw(self, surf):
        _btn(surf, self.rect, self.label, self.hovered, self.selected, self.color)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.toggle: self.selected = not self.selected
                return True
        return False


class GameRenderer:
    def __init__(self, screen: pygame.Surface, my_idx: int = 0):
        self.screen = screen
        self.my_idx = my_idx
        self.pending_request: Optional[dict] = None
        self._btns: list[Button] = []
        self._selected_team: list[int] = []

    def tick(self):
        req = bridge.get_pending_request()
        if req is not None:
            self.pending_request = req
            self._selected_team = []
            self._build_buttons()

    def draw(self):
        surf = self.screen
        surf.fill(BG)
        with bridge._lock:
            state = dict(bridge.game_state)
            log = list(bridge.game_log)
            result = bridge.game_result
        self._draw_table(surf, state)
        self._draw_mission_track(surf, state)
        self._draw_right_panel(surf, log, state)
        self._draw_action_panel(surf, state)
        if result: self._draw_game_over(surf, result)

    def _draw_table(self, surf, state):
        pygame.draw.ellipse(surf, PANEL_DARK,
            (TABLE_CX-TABLE_RX-12, TABLE_CY-TABLE_RY-12, (TABLE_RX+12)*2, (TABLE_RY+12)*2))
        pygame.draw.ellipse(surf, BORDER,
            (TABLE_CX-TABLE_RX-12, TABLE_CY-TABLE_RY-12, (TABLE_RX+12)*2, (TABLE_RY+12)*2), 2)
        players = state.get("players", [])
        n = len(players)
        if not n: return
        leader_idx = state.get("leader_idx", -1)
        vote_history = state.get("vote_history", [])
        last_vote = vote_history[-1] if vote_history else None
        positions = self._calc_positions(n)
        for i, p in enumerate(players):
            cx, cy = positions[i]
            self._draw_player_card(surf, p, cx, cy,
                is_me=(p["idx"]==self.my_idx),
                is_leader=(p["idx"]==leader_idx),
                in_team=(p["idx"] in self._selected_team),
                last_vote=last_vote)

    def _calc_positions(self, n):
        my = self.my_idx if 0 <= self.my_idx < n else 0
        positions = []
        for i in range(n):
            offset = (i - my) % n
            angle = math.pi/2 + 2*math.pi*offset/n
            x = int(TABLE_CX + TABLE_RX * math.cos(angle))
            y = int(TABLE_CY + TABLE_RY * math.sin(angle))
            positions.append((x, y))
        return positions

    def _draw_player_card(self, surf, p, cx, cy, is_me, is_leader, in_team, last_vote):
        cw, ch = 90, 58
        rect = pygame.Rect(cx-cw//2, cy-ch//2, cw, ch)
        role = p.get("role")
        alignment = p.get("alignment")
        if alignment == "好人": border_c = GOOD_COLOR
        elif alignment == "坏人": border_c = EVIL_COLOR
        elif in_team: border_c = GOLD
        elif is_me: border_c = (100, 200, 255)
        else: border_c = BORDER
        pygame.draw.rect(surf, PANEL_BG, rect, border_radius=8)
        pygame.draw.rect(surf, border_c, rect, 2, border_radius=8)
        nc = TEXT_BRIGHT if is_me else TEXT
        _text(surf, p["name"][:6], (cx, cy-10), nc, 14, bold=is_me, center=True)
        if role:
            rc = ROLE_COLORS.get(role, TEXT_DIM)
            _text(surf, role, (cx, cy+8), rc, 11, center=True)
        if is_leader: _text(surf, "👑", (cx-cw//2+3, cy-ch//2+2), GOLD, 12)
        if not p.get("is_human", True): _text(surf, "🤖", (cx+cw//2-17, cy-ch//2+2), TEXT_DIM, 12)
        if last_vote:
            votes = last_vote.get("votes", {})
            val = votes.get(p["idx"])
            if val is not None:
                _text(surf, "✓" if val else "✗", (cx+cw//2-14, cy+8), GREEN if val else RED, 16, bold=True)
        if in_team:
            pygame.draw.circle(surf, GOLD, (cx+cw//2-7, cy-ch//2+7), 5)

    def _draw_mission_track(self, surf, state):
        results = state.get("mission_results", [])
        sizes = state.get("mission_sizes", [2,3,2,3,3])
        cur_round = state.get("round_idx", 0)
        ty = TABLE_CY + TABLE_RY + 30
        tl = TABLE_CX - 210
        cw, ch = 78, 46
        gap = 9
        _text(surf, "任务进度", (tl, ty-22), GOLD, 15, bold=True)
        for i in range(5):
            x = tl + i*(cw+gap)
            rect = pygame.Rect(x, ty, cw, ch)
            if i < len(results):
                c = MISSION_WIN if results[i] else MISSION_LOSE
                label = "✅ 成功" if results[i] else "❌ 失败"
            elif i == cur_round:
                c = (60,60,100); label = f"R{i+1}进行中"
            else:
                c = MISSION_NONE; label = f"R{i+1}"
            pygame.draw.rect(surf, c, rect, border_radius=6)
            pygame.draw.rect(surf, BORDER, rect, 1, border_radius=6)
            _text(surf, label, rect.center, TEXT_BRIGHT, 12, center=True)
            if i < len(sizes):
                _text(surf, f"{sizes[i]}人", (rect.centerx, rect.bottom+3), TEXT_DIM, 11, center=True)
        vfc = state.get("vote_fail_count", 0)
        if vfc > 0:
            _text(surf, f"投票连败:{vfc}/5", (tl+5*(cw+gap)+10, ty+14), RED, 13)

    def _draw_right_panel(self, surf, log, state):
        px, pw, ph = 860, W-880, H-60
        pygame.draw.rect(surf, PANEL_DARK, (px,15,pw,ph), border_radius=8)
        pygame.draw.rect(surf, BORDER, (px,15,pw,ph), 1, border_radius=8)
        _text(surf, "📜 日志", (px+12, 22), GOLD, 15, bold=True)
        log_styles = {"header": GOLD, "section": (140,190,255), "warn": (240,100,80),
                      "normal": TEXT, "ai": TEXT_DIM}
        line_h, max_lines = 18, (ph-50)//18
        y0 = 50
        for text, style in log[-max_lines:]:
            color = log_styles.get(style, TEXT)
            f = _font(13)
            words = text
            mw = pw - 20
            if f.size(words)[0] > mw:
                while f.size(words)[0] > mw and len(words) > 4: words = words[:-1]
                words += "…"
            surf.blit(f.render(words, True, color), (px+10, y0))
            y0 += line_h
        phase = state.get("phase", "")
        _text(surf, f"阶段: {phase}", (px+10, H-38), TEXT_DIM, 12)

    def _draw_action_panel(self, surf, state):
        req = self.pending_request
        if req is None: return
        kind = req.get("kind", "")
        data = req.get("data", {})
        player_idx = req.get("player_idx", -1)
        if player_idx != self.my_idx: return
        py = H-140; ph = 128
        pygame.draw.rect(surf, PANEL_BG, (0,py,840,ph), border_radius=8)
        pygame.draw.rect(surf, BORDER, (0,py,840,ph), 1, border_radius=8)
        if kind == "show_role":
            role = data.get("your_role","?"); alignment = data.get("alignment","?")
            desc = data.get("role_desc",""); visible = data.get("visible",[])
            rc = ROLE_COLORS.get(role, TEXT)
            ac = GOOD_COLOR if alignment=="好人" else EVIL_COLOR
            _text(surf, f"你的角色：{role} ({alignment})", (12,py+10), rc, 17, bold=True)
            _text(surf, desc[:60], (12,py+34), TEXT_DIM, 12)
            if visible:
                infos = "  |  ".join(f"{v['name']}（{v['hint']}）" for v in visible)
                _text(surf, f"你能看到：{infos}", (12,py+58), TEXT, 13)
        elif kind == "select_team":
            ts = data.get("team_size",2); sel = self._selected_team
            _text(surf, f"请选 {ts} 名队员（已选 {len(sel)}/{ts}）— 点桌上头像",
                  (12,py+10), GOLD, 15, bold=True)
            names = data.get("player_names",[])
            for i, n in enumerate(names):
                c = BTN_SEL if i in sel else BTN_NORMAL
                r = pygame.Rect(12+i*88, py+42, 78, 28)
                pygame.draw.rect(surf, c, r, border_radius=5)
                _text(surf, n[:5], r.center, BTN_TEXT, 12, center=True)
        elif kind == "vote_team":
            names = data.get("team_names",[])
            _text(surf, f"队伍：{', '.join(names)}  — 是否赞成？", (12,py+12), GOLD, 15, bold=True)
        elif kind == "play_mission":
            can_fail = data.get("can_fail",False)
            _text(surf, "任务进行中！选择任务牌：", (12,py+12), GOLD, 15, bold=True)
            if not can_fail: _text(surf, "（好人只能选成功）", (280,py+14), TEXT_DIM, 12)
        elif kind == "assassinate":
            _text(surf, f"{data.get('assassin_name','刺客')}，选择刺杀目标：", (12,py+10), RED, 16, bold=True)
        for btn in self._btns: btn.draw(surf)

    def _draw_game_over(self, surf, result):
        overlay = pygame.Surface((W,H), pygame.SRCALPHA)
        overlay.fill((0,0,0,180))
        surf.blit(overlay, (0,0))
        winner = result.get("winner",""); reason = result.get("end_reason","")
        color = GREEN if winner=="good" else RED
        _text(surf, "游戏结束！", (W//2,190), color, 36, bold=True, center=True)
        wt = "🏆 好人阵营获胜" if winner=="good" else "👿 邪恶阵营获胜"
        _text(surf, wt, (W//2,250), color, 24, bold=True, center=True)
        _text(surf, reason, (W//2,300), TEXT, 17, center=True)
        players = result.get("players",[])
        cw = min(115, (W-80)//max(len(players),1))
        for i, p in enumerate(players):
            rx = 40+i*(cw+8)
            role = p.get("role","?"); alignment = p.get("alignment","?")
            rc = GOOD_COLOR if alignment=="好人" else EVIL_COLOR
            pygame.draw.rect(surf, PANEL_BG, (rx,360,cw,76), border_radius=8)
            pygame.draw.rect(surf, rc, (rx,360,cw,76), 2, border_radius=8)
            _text(surf, p.get("name",""), (rx+cw//2,375), TEXT_BRIGHT, 13, center=True)
            _text(surf, role, (rx+cw//2,396), ROLE_COLORS.get(role,TEXT), 12, center=True)
            _text(surf, alignment, (rx+cw//2,415), rc, 12, center=True)
        _text(surf, "按 R 重新开始  |  按 ESC 退出", (W//2, H-55), TEXT_DIM, 15, center=True)

    def _build_buttons(self):
        self._btns = []
        req = self.pending_request
        if req is None: return
        kind = req.get("kind",""); data = req.get("data",{})
        player_idx = req.get("player_idx",-1)
        if player_idx != self.my_idx: return
        py = H - 140
        if kind == "show_role":
            self._btns.append(Button((340,py+85,140,32), "✅ 我知道了", True, GREEN))
        elif kind == "select_team":
            ts = data.get("team_size",2)
            self._btns.append(Button((680,py+85,140,32), "✅ 确认队伍", "confirm", GREEN))
        elif kind == "vote_team":
            self._btns.append(Button((280,py+60,110,38), "✅ 赞成", True, GREEN))
            self._btns.append(Button((420,py+60,110,38), "❌ 反对", False, RED))
        elif kind == "play_mission":
            can_fail = data.get("can_fail",False)
            self._btns.append(Button((280,py+60,126,38), "✅ 任务成功", True, GREEN))
            if can_fail:
                self._btns.append(Button((430,py+60,126,38), "❌ 任务失败", False, RED))
        elif kind == "assassinate":
            candidates = data.get("candidate_idxs",[]); cnames = data.get("candidate_names",[])
            for ci,(idx,name) in enumerate(zip(candidates,cnames)):
                r = pygame.Rect(12+ci*108, py+62, 98, 32)
                self._btns.append(Button(r, name[:6], idx, RED))

    def handle_event(self, event):
        req = self.pending_request
        if req is None: return None
        kind = req.get("kind",""); data = req.get("data",{})
        player_idx = req.get("player_idx",-1)
        if bridge.game_result:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r: return "reset"
                if event.key == pygame.K_ESCAPE: return "quit"
            return None
        if player_idx != self.my_idx: return None
        if kind == "select_team" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            ts = data.get("team_size",2)
            state = bridge.game_state
            players = state.get("players",[])
            n = len(players)
            if n:
                positions = self._calc_positions(n)
                for i, (px, py_) in enumerate(positions):
                    dist = ((event.pos[0]-px)**2 + (event.pos[1]-py_)**2)**0.5
                    if dist < 50:
                        pidx = players[i]["idx"]
                        if pidx in self._selected_team: self._selected_team.remove(pidx)
                        elif len(self._selected_team) < ts: self._selected_team.append(pidx)
                        break
        for btn in self._btns:
            if btn.handle_event(event):
                if kind == "show_role" and btn.value is True:
                    self.pending_request = None; self._btns = []
                    bridge.respond(True)
                elif kind == "select_team" and btn.value == "confirm":
                    ts = data.get("team_size",2)
                    if len(self._selected_team) == ts:
                        resp = list(self._selected_team)
                        self.pending_request = None; self._btns = []; self._selected_team = []
                        bridge.respond(resp)
                elif kind in ("vote_team","play_mission"):
                    self.pending_request = None; self._btns = []
                    bridge.respond(btn.value)
                elif kind == "assassinate":
                    self.pending_request = None; self._btns = []
                    bridge.respond(btn.value)
        return None
