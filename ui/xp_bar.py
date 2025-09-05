# ui/xp_bar.py
# -*- coding: utf-8 -*-

import pygame


class XPBar:
    """
    Barre d'expérience animée pour les Pokémon (style GBA).
    API :
      - set_max_xp(max_xp) : borne du niveau courant (>=1)
      - update(current_xp, dt_ms) : anime l'affichage vers current_xp
      - draw(surface) : dessine la barre
      - reset_displayed_xp(force_value=0) : reset optionnel (compat)

    Notes :
      current_xp et max_xp sont exprimés "dans le niveau" (pas XP totale).
    """

    def __init__(self, pos, max_xp):
        self.pos = pos
        self.bar_width = 98
        self.bar_height = 4

        self.bar_bg = (30, 30, 30)
        self.bar_color = (0, 152, 216)  # bleu XP GBA-like

        self.max_xp = max(1, int(max_xp))
        self.current_xp = 0.0
        self.displayed_xp = 0.0

        # Animation lissée
        self._target = 0.0
        self._speed = 0.012  # proportion de la largeur/ms (tweaké pour ~60FPS)
        self._snap_eps = 0.5

    def set_max_xp(self, max_xp: int):
        self.max_xp = max(1, int(max_xp))
        self.displayed_xp = max(0.0, min(self.displayed_xp, float(self.max_xp)))
        self._target = max(0.0, min(self._target, float(self.max_xp)))

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
        # clamp strict
        ratio = 0.0 if ratio < 0.0 else (1.0 if ratio > 1.0 else ratio)
        fill_width = int(self.bar_width * ratio)

        if fill_width > 0:
            pygame.draw.rect(surface, self.bar_color, (x, y, fill_width, self.bar_height))

    # Compatibilité (certains endroits resettaient brutalement la valeur)
    def reset_displayed_xp(self, force_value=0):
        v = max(0, int(force_value))
        self.current_xp = v
        self.displayed_xp = float(v)
        self._target = float(v)
