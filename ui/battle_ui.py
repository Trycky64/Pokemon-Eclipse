# ui/battle_ui.py
# -*- coding: utf-8 -*-

import pygame
from typing import Dict, List

from ui.health_bar import HealthBar
from ui.xp_bar import XPBar
from ui.button import Button
from core.assets import render_text_cached
from core.config import DEFAULT_FONT_PATH

class BattleUI:
    """
    Orchestration des composants UI du combat :
      - barres PV/XP
      - menu Combat/Sac/Pokémon/Fuite
      - attaques avec PP
    """

    def __init__(self, player: Dict, enemy: Dict):
        # HP bars
        self.ally_hp = HealthBar((302, 232), (128, 6),
                                 max_hp=int(player.get("stats", {}).get("hp", player.get("hp", 1))))
        self.ally_hp.set_show_text(True)
        self.enemy_hp = HealthBar((62, 46), (128, 6),
                                  max_hp=int(enemy.get("stats", {}).get("hp", enemy.get("hp", 1))))

        # XP bar
        self.ally_xp = XPBar((302, 252), max_xp=1)

        # Menus
        self.root_options = ["Combat", "Sac", "Pokémon", "Fuite"]
        self.menu_index = 0
        self.submenu_index = 0
        self.font = pygame.font.Font(DEFAULT_FONT_PATH, 20)
        self.btn = Button(font_size=20)

    def update_bars(self, player: Dict, enemy: Dict, dt_ms: float):
        self.ally_hp.set_max_hp(int(player.get("stats", {}).get("hp", player.get("hp", 1))))
        self.enemy_hp.set_max_hp(int(enemy.get("stats", {}).get("hp", enemy.get("hp", 1))))
        self.ally_hp.update(int(player.get("hp", 1)), dt_ms)
        self.enemy_hp.update(int(enemy.get("hp", 1)), dt_ms)

    def update_xp(self, current: int, needed: int, dt_ms: float):
        self.ally_xp.set_max_xp(needed)
        self.ally_xp.update(current, dt_ms)

    def draw_hud(self, screen: pygame.Surface, player: Dict, enemy: Dict):
        # Enemy info
        e_name = render_text_cached(enemy["name"], DEFAULT_FONT_PATH, 18, (22, 22, 28))
        e_lvl = render_text_cached(f"N.{enemy.get('level', 5)}", DEFAULT_FONT_PATH, 18, (22, 22, 28))
        screen.blit(e_name, (62, 26))
        screen.blit(e_lvl, (184, 26))
        self.enemy_hp.draw(screen)

        # Player info
        a_name = render_text_cached(player["name"], DEFAULT_FONT_PATH, 18, (22, 22, 28))
        a_lvl = render_text_cached(f"N.{player.get('level', 5)}", DEFAULT_FONT_PATH, 18, (22, 22, 28))
        screen.blit(a_name, (302, 212))
        screen.blit(a_lvl, (424, 212))
        self.ally_hp.draw(screen)
        self.ally_xp.draw(screen)

    def draw_root_menu(self, screen: pygame.Surface):
        positions = [
            pygame.Rect(316, screen.get_height() - 80, 100, 24),
            pygame.Rect(420, screen.get_height() - 80, 100, 24),
            pygame.Rect(316, screen.get_height() - 52, 100, 24),
            pygame.Rect(420, screen.get_height() - 52, 100, 24),
        ]
        for i, (label, rect) in enumerate(zip(self.root_options, positions)):
            self.btn.draw(screen, rect, label, selected=(i == self.menu_index))

    def draw_moves_menu(self, screen: pygame.Surface, moves: List[Dict]):
        if not moves:
            txt = render_text_cached("Aucune attaque.", DEFAULT_FONT_PATH, 18, (22, 22, 28))
            screen.blit(txt, (24, screen.get_height() - 78))
            return
        grid = [
            (24, screen.get_height() - 84),
            (220, screen.get_height() - 84),
            (24, screen.get_height() - 56),
            (220, screen.get_height() - 56),
        ]
        for i, mv in enumerate(moves[:4]):
            name = mv.get("name", "???")
            pp = f"{mv.get('pp', 0)}/{mv.get('max_pp', mv.get('pp', 0))}"
            label = f"{name} (PP {pp})"
            surf = render_text_cached(label, DEFAULT_FONT_PATH, 18, (22, 22, 28))
            x, y = grid[i]
            screen.blit(surf, (x, y))
            if i == self.submenu_index:
                arrow = render_text_cached("▶", DEFAULT_FONT_PATH, 18, (22, 22, 28))
                screen.blit(arrow, (x - 18, y))
        # Type de l’attaque sélectionnée
        sel = moves[self.submenu_index]
        type_label = render_text_cached(f"Type: {sel.get('type','?')}", DEFAULT_FONT_PATH, 18, (22, 22, 28))
        screen.blit(type_label, (316, screen.get_height() - 84))
