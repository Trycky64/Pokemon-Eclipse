# ui/button.py
# -*- coding: utf-8 -*-

import pygame
from core.assets import render_text_cached
from core.config import DEFAULT_FONT_PATH

class Button:
    """
    Bouton texte simple façon GBA.
    draw(surface, rect, label, selected) -> dessine avec un curseur si sélectionné.
    """
    def __init__(self, font_size=18):
        self.font_size = int(font_size)
        self.bg = (245, 245, 245)
        self.border = (32, 32, 32)
        self.text_color = (22, 22, 28)
        self.cursor = "▶"

    def draw(self, surface: pygame.Surface, rect: pygame.Rect, label: str, selected: bool = False):
        pygame.draw.rect(surface, self.bg, rect)
        pygame.draw.rect(surface, self.border, rect, 2)

        txt = render_text_cached(label, DEFAULT_FONT_PATH, self.font_size, self.text_color)
        tx = rect.centerx - txt.get_width() // 2
        ty = rect.centery - txt.get_height() // 2
        surface.blit(txt, (tx, ty))

        if selected:
            arrow = render_text_cached(self.cursor, DEFAULT_FONT_PATH, self.font_size, self.text_color)
            surface.blit(arrow, (rect.x + 6, rect.centery - arrow.get_height() // 2))
