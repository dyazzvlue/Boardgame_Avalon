"""
gui_main.py — 阿瓦隆 pygame GUI 入口
用法: python gui_main.py
"""
from __future__ import annotations
import sys, os, threading
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except: pass
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path: sys.path.insert(0, _HERE)

import pygame
from typing import Optional
from constants import MISSION_SIZES, ROLE_PRESETS
from player import AvalonPlayer
from game import AvalonGame
import gui.bridge as bridge
from gui.bridge import LocalBridge
from gui.renderer import GameRenderer, W, H, BG, PANEL_BG, BORDER, TEXT, TEXT_DIM, GOLD, GREEN, RED, BTN_NORMAL, BTN_HOVER, BTN_TEXT, _font

def _text(surf, txt, pos, color=TEXT, size=16, bold=False, center=False):
    f = _font(size, bold)
    s = f.render(str(txt), True, color)
    r = s.get_rect()
    if center: r.center = pos
    else: r.topleft = pos
    surf.blit(s, r)

def _btn_draw(surf, rect, label, hovered=False, color=None):
    c = color or (BTN_HOVER if hovered else BTN_NORMAL)
    pygame.draw.rect(surf, c, rect, border_radius=6)
    pygame.draw.rect(surf, BORDER, rect, 1, border_radius=6)
    _text(surf, label, rect.center, BTN_TEXT, 15, center=True)


class SetupScene:
    MIN_P, MAX_P = 5, 10

    def __init__(self, screen):
        self.screen = screen
        self.n_players = 5
        self.names = [f"玩家{i+1}" for i in range(10)]
        self.humans = [True] + [False]*9
        self.editing_idx = None
        self.error_msg = ""

    def handle_event(self, event):
        mouse = pygame.mouse.get_pos()
        if event.type == pygame.KEYDOWN:
            if self.editing_idx is not None:
                idx = self.editing_idx
                if event.key in (pygame.K_RETURN, pygame.K_TAB):
                    self.editing_idx = None
                elif event.key == pygame.K_BACKSPACE:
                    self.names[idx] = self.names[idx][:-1]
                else:
                    if len(self.names[idx]) < 10: self.names[idx] += event.unicode
            else:
                if event.key == pygame.K_RETURN: return self._build_config()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if pygame.Rect(360,155,36,36).collidepoint(mouse):
                self.n_players = max(self.MIN_P, self.n_players-1)
            elif pygame.Rect(440,155,36,36).collidepoint(mouse):
                self.n_players = min(self.MAX_P, self.n_players+1)
            for i in range(self.n_players):
                y = 220+i*50
                if pygame.Rect(120,y+5,200,32).collidepoint(mouse):
                    self.editing_idx = i; continue
                if pygame.Rect(350,y+5,80,32).collidepoint(mouse):
                    self.humans[i] = not self.humans[i]
            if pygame.Rect(W//2-80, H-90, 160, 44).collidepoint(mouse):
                cfg = self._build_config()
                if cfg: return cfg
        return None

    def _build_config(self):
        n = self.n_players
        if not any(self.humans[:n]): self.error_msg = "至少需要一名真人玩家！"; return None
        players = []
        for i in range(n):
            name = self.names[i].strip() or f"玩家{i+1}"
            players.append({"name": name, "is_human": self.humans[i], "idx": i})
        return {"players": players}

    def draw(self):
        surf = self.screen
        surf.fill(BG)
        _text(surf, "⚔ 阿瓦隆 Avalon", (W//2,60), GOLD, 32, bold=True, center=True)
        _text(surf, "好人保护卡美洛，邪恶方暗中破坏任务", (W//2,110), TEXT_DIM, 16, center=True)
        _text(surf, "玩家人数：", (200,162), TEXT, 16)
        pygame.draw.rect(surf, BTN_NORMAL, (360,155,36,36), border_radius=5)
        pygame.draw.rect(surf, BTN_NORMAL, (440,155,36,36), border_radius=5)
        _text(surf, "−", (378,173), TEXT, 20, center=True)
        _text(surf, "+", (458,173), TEXT, 20, center=True)
        _text(surf, str(self.n_players), (410,173), GOLD, 22, center=True)
        preset = ROLE_PRESETS.get(self.n_players, {})
        gc, ec = preset.get("good",0), preset.get("evil",0)
        _text(surf, f"（好人{gc}人 / 坏人{ec}人）", (520,162), TEXT_DIM, 14)
        _text(surf, "# 玩家", (80,195), GOLD, 14, bold=True)
        _text(surf, "名字", (190,195), GOLD, 14, bold=True)
        _text(surf, "类型", (355,195), GOLD, 14, bold=True)
        mouse = pygame.mouse.get_pos()
        for i in range(self.n_players):
            y = 220+i*50
            _text(surf, f"#{i+1}", (80,y+10), TEXT_DIM, 14)
            nr = pygame.Rect(120,y+5,200,32)
            editing_here = (self.editing_idx==i)
            pygame.draw.rect(surf, (30,45,75) if editing_here else PANEL_BG, nr, border_radius=5)
            pygame.draw.rect(surf, GOLD if editing_here else BORDER, nr, 1, border_radius=5)
            _text(surf, self.names[i]+("|" if editing_here else ""), (nr.x+8,y+10), TEXT, 15)
            tr = pygame.Rect(350,y+5,80,32)
            c = (40,130,60) if self.humans[i] else (80,40,100)
            pygame.draw.rect(surf, c, tr, border_radius=5)
            _text(surf, "真人" if self.humans[i] else "AI", tr.center, BTN_TEXT, 14, center=True)
        start_rect = pygame.Rect(W//2-80, H-90, 160, 44)
        h = start_rect.collidepoint(mouse)
        _btn_draw(surf, start_rect, "▶  开始游戏", h, (45,160,75) if not h else (60,200,90))
        if self.error_msg: _text(surf, self.error_msg, (W//2, H-120), RED, 14, center=True)
        pygame.display.flip()


class GameScene:
    def __init__(self, screen, config):
        self.screen = screen
        my_idx = 0
        players = []
        for i, p in enumerate(config["players"]):
            ap = AvalonPlayer(name=p["name"], idx=i, is_human=p["is_human"])
            players.append(ap)
            if p["is_human"] and my_idx == 0: my_idx = i
        game = AvalonGame(bridge=None)
        b = LocalBridge(game)
        game.bridge = b
        game.setup(players)
        self.renderer = GameRenderer(screen, my_idx)
        t = threading.Thread(target=self._run_game, args=(game,), daemon=True)
        t.start()

    def _run_game(self, game):
        try: game.run()
        except SystemExit: pass
        except Exception as e:
            bridge.game_state["phase"] = f"ERROR: {e}"

    def handle_event(self, event):
        result = self.renderer.handle_event(event)
        if result == "reset": bridge.reset(); return "setup"
        if result == "quit": return "quit"
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if bridge.game_result: bridge.reset(); return "setup"
        return ""

    def draw(self):
        self.renderer.tick()
        self.renderer.draw()
        pygame.display.flip()


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("阿瓦隆 Avalon")
    clock = pygame.time.Clock()
    scene = SetupScene(screen)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if isinstance(scene, SetupScene):
                cfg = scene.handle_event(event)
                if cfg: scene = GameScene(screen, cfg)
            elif isinstance(scene, GameScene):
                action = scene.handle_event(event)
                if action == "setup": scene = SetupScene(screen)
                elif action == "quit": pygame.quit(); sys.exit()
        if isinstance(scene, SetupScene): scene.draw()
        elif isinstance(scene, GameScene): scene.draw()
        clock.tick(30)

if __name__ == "__main__":
    main()
