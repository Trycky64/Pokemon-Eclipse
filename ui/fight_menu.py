# ui/fight_menu.py
# -*- coding: utf-8 -*-

from __future__ import annotations
import pygame
from typing import List, Dict

from core.assets import render_text_cached
from core.config import DEFAULT_FONT_PATH

class FightMenu:
    """
    Menu des attaques (grille 2x2 façon GBA).
    API simple :
      - set_moves(moves)
      - set_index(i) / get_index()
      - draw(surface)
    Les déplacements du curseur sont gérés par la scène (InputManager).
    """

    def __init__(self):
        self.moves: List[Dict] = []
        self.index: int = 0  # curseur [0..3]

    # --------------------------- data ---------------------------

    def set_moves(self, moves: List[Dict]):
        self.moves = list(moves or [])
        self.index = 0

    def set_index(self, i: int):
        if not self.moves:
            self.index = 0
            return
        self.index = max(0, min(len(self.moves) - 1, int(i)))

    def get_index(self) -> int:
        return self.index

    # --------------------------- draw ---------------------------

    def draw(self, surface: pygame.Surface):
        h = surface.get_height()
        # Emplacements en grille
        slots = [
            (24,  h - 84),
            (220, h - 84),
            (24,  h - 56),
            (220, h - 56),
        ]
        if not self.moves:
            txt = render_text_cached("Aucune attaque.", DEFAULT_FONT_PATH, 18, (22, 22, 28))
            surface.blit(txt, (24, h - 78))
            return

        for i, mv in enumerate(self.moves[:4]):
            name = mv.get("name", "???")
            pp = f"{mv.get('pp', 0)}/{mv.get('max_pp', mv.get('pp', 0))}"
            label = f"{name}  (PP {pp})"
            x, y = slots[i]
            surf = render_text_cached(label, DEFAULT_FONT_PATH, 18, (22, 22, 28))
            surface.blit(surf, (x, y))
            if i == self.index:
                arrow = render_text_cached("▶", DEFAULT_FONT_PATH, 18, (22, 22, 28))
                surface.blit(arrow, (x - 18, y))

        # Bandeau d’info sur l’attaque sélectionnée (type)
        sel = self.moves[self.index]
        type_label = render_text_cached(f"Type: {sel.get('type','?')}", DEFAULT_FONT_PATH, 18, (22, 22, 28))
        surface.blit(type_label, (316, h - 84))
