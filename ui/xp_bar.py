# ui/xp_bar.py
# -*- coding: utf-8 -*-

import pygame

class XPBar:
    """
    Barre d'expérience animée (style GBA).
    API :
      - set_max_xp(max_xp)
      - update(current_xp, dt_ms)
      - draw(surface)
      - reset_displayed_xp(force_value=0)
    """
    def __init__(self, pos, max_xp: int):
        self.pos = pos
        self.bar_width = 98
        self.bar_height = 4
        self.bar_bg = (30, 30, 30)
        self.bar_color = (0, 152, 216)
        self.max_xp = max(1, int(max_xp))
        self.displayed_xp = 0.0
        self._target = 0.0
        self._speed = 0.012  # proportion/ms
        self._snap_eps = 0.5

    def set_max_xp(self, max_xp: int):
        self.max_xp = max(1, int(max_xp))
        self.displayed_xp = min(self.displayed_xp, float(self.max_xp))
        self._target = min(self._target, float(self.max_xp))

    def update(self, current_xp: int, dt_ms: float):
        self._target = max(0.0, min(float(current_xp), float(self.max_xp)))
        delta = self._target - self.displayed_xp
        if abs(delta) <= self._snap_eps:
            self.displayed_xp = float(self._target)
            return
        step = max(1.0, self._speed * float(dt_ms) * float(self.max_xp))
        if delta > 0:
            self.displayed_xp = min(self.displayed_xp + step, self._target)
        else:
            self.displayed_xp = max(self.displayed_xp - step, self._target)

    def draw(self, surface: pygame.Surface):
        x, y = self.pos
        pygame.draw.rect(surface, self.bar_bg, (x, y, self.bar_width, self.bar_height))
        ratio = (self.displayed_xp / float(self.max_xp)) if self.max_xp else 0.0
        ratio = max(0.0, min(1.0, ratio))
        fill_width = int(self.bar_width * ratio)
        if fill_width > 0:
            pygame.draw.rect(surface, self.bar_color, (x, y, fill_width, self.bar_height))

    def reset_displayed_xp(self, force_value=0):
        v = max(0, int(force_value))
        self.displayed_xp = float(v)
        self._target = float(v)
