# scene/gameover_scene.py
# -*- coding: utf-8 -*-

from __future__ import annotations
import pygame

from core.scene_manager import Scene
from core.config import SCREEN_WIDTH, SCREEN_HEIGHT, DEFAULT_FONT_PATH
from core.assets import render_text_cached
from scene.menu_scene import MenuScene

class GameOverScene(Scene):
    """
    Écran de game over : Entrée/Espace/Z pour retourner au menu.
    """
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
            if self.manager:
                self.manager.change_scene(MenuScene())

    def update(self, dt_ms: float):
        pass

    def draw(self, screen: pygame.Surface):
        screen.fill((20, 20, 28))
        t1 = render_text_cached("GAME OVER", DEFAULT_FONT_PATH, 28, (240, 240, 240))
        t2 = render_text_cached("Appuyez sur Entrée", DEFAULT_FONT_PATH, 18, (240, 240, 240))
        screen.blit(t1, (SCREEN_WIDTH // 2 - t1.get_width() // 2, SCREEN_HEIGHT // 2 - 36))
        screen.blit(t2, (SCREEN_WIDTH // 2 - t2.get_width() // 2, SCREEN_HEIGHT // 2 + 12))
