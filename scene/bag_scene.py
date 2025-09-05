# scene/bag_scene.py
# -*- coding: utf-8 -*-

from __future__ import annotations
import pygame
from typing import Dict, List

from core.scene_manager import Scene
from core.config import SCREEN_WIDTH, SCREEN_HEIGHT, DEFAULT_FONT_PATH
from core.assets import render_text_cached
from core.run_manager import run_manager

class BagScene(Scene):
    """
    Scène d’inventaire minimaliste (hors combat) :
      - ↑/↓ pour naviguer
      - Échap/X/Retour pour quitter
    (On ne consomme pas d’objet ici pour éviter les effets de gameplay hors combat)
    """

    def __init__(self):
        super().__init__()
        self.index = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.index = max(0, self.index - 1)
            elif event.key == pygame.K_DOWN:
                self.index = min(max(0, len(run_manager.get_items_as_inventory()) - 1), self.index + 1)
            elif event.key in (pygame.K_ESCAPE, pygame.K_x, pygame.K_BACKSPACE):
                if self.manager:
                    self.manager.pop_scene()

    def update(self, dt_ms: float):
        pass

    def draw(self, screen: pygame.Surface):
        screen.fill((245, 245, 245))
        title = render_text_cached("Sac", DEFAULT_FONT_PATH, 22, (22, 22, 28))
        screen.blit(title, (24, 16))

        items = run_manager.get_items_as_inventory()
        if not items:
            empty = render_text_cached("Votre sac est vide.", DEFAULT_FONT_PATH, 18, (22, 22, 28))
            screen.blit(empty, (24, 60))
            return

        y = 60
        for i, it in enumerate(items):
            name = it.get("name", "?")
            qty = it.get("quantity", 0)
            label = f"{name}  x{qty}"
            surf = render_text_cached(label, DEFAULT_FONT_PATH, 18, (22, 22, 28))
            screen.blit(surf, (46, y))
            if i == self.index:
                arrow = render_text_cached("▶", DEFAULT_FONT_PATH, 18, (22, 22, 28))
                screen.blit(arrow, (24, y))
            y += 24
