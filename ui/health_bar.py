# ui/health_bar.py
# -*- coding: utf-8 -*-

import pygame


class HealthBar:
    """
    Barre de points de vie avec animation fluide et code couleur façon GBA.
    API :
      - set_max_hp(max_hp)
      - set_show_text(enabled, font_path=None, font_size=None, offset=None) [optionnel]
      - update(current_hp, dt_ms)
      - draw(surface)
    """

    def __init__(self, pos, size, max_hp, colors=None):
        self.x, self.y = pos
        self.width, self.height = size
        self.max_hp = max(1, int(max_hp))

        self.current_hp = float(self.max_hp)
        self.displayed_hp = float(self.max_hp)

        # Animation
        self._speed = 0.02  # proportion par ms
        self._snap = 0.5

        self.colors = colors or {
            "high": (88, 200, 96),     # > 50%
            "mid":  (248, 192, 0),     # 25%..50%
            "low":  (232, 64, 48),     # <= 25%
            "bg":   (32, 32, 32),
        }

        # Texte optionnel (utile pour allié)
        self.show_text = False
        self._font_path = "assets/fonts/power clear bold.ttf"
        self._font_size = 23
        self._text_offset = (11, 10)  # dx, dy depuis (x, y+height)

    def set_max_hp(self, max_hp: int):
        self.max_hp = max(1, int(max_hp))
        self.displayed_hp = max(0.0, min(self.displayed_hp, float(self.max_hp)))
        self.current_hp = max(0.0, min(self.current_hp, float(self.max_hp)))

    def set_show_text(self, enabled: bool, font_path=None, font_size=None, offset=None):
        self.show_text = bool(enabled)
        if font_path:
            self._font_path = font_path
        if font_size:
            self._font_size = font_size
        if offset:
            self._text_offset = offset

    def update(self, current_hp: int, dt_ms: float):
        self.current_hp = max(0.0, min(float(current_hp), float(self.max_hp)))
        delta = self.current_hp - self.displayed_hp
        if abs(delta) <= self._snap:
            self.displayed_hp = float(self.current_hp)
            return

        step = max(1.0, self._speed * float(dt_ms) * float(self.max_hp))
        if delta > 0:
            self.displayed_hp = min(self.displayed_hp + step, self.current_hp)
        else:
            self.displayed_hp = max(self.displayed_hp - step, self.current_hp)

    def draw(self, surface: pygame.Surface):
        # arrière-plan
        pygame.draw.rect(surface, self.colors["bg"], (self.x, self.y, self.width, self.height))

        # couleur selon ratio
        ratio = (self.displayed_hp / float(self.max_hp)) if self.max_hp else 0.0
        if   ratio <= 0.25: color = self.colors["low"]
        elif ratio <= 0.5:  color = self.colors["mid"]
        else:               color = self.colors["high"]

        # remplissage
        ratio = 0.0 if ratio < 0.0 else (1.0 if ratio > 1.0 else ratio)
        fill_w = int(self.width * ratio)
        if fill_w > 0:
            pygame.draw.rect(surface, color, (self.x, self.y, fill_w, self.height))

        # texte optionnel (ex: "61/61") — **sans coordonnées magiques**
        if self.show_text:
            font = pygame.font.Font(self._font_path, self._font_size)
            cur = int(round(self.displayed_hp))
            txt = f"{cur}/{int(self.max_hp)}"
            text_surface = font.render(txt, True, (80, 80, 84))
            dx, dy = self._text_offset
            surface.blit(text_surface, (self.x + dx, self.y + self.height + dy))
