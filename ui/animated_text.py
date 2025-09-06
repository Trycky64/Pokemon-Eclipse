# ui/animated_text.py
# -*- coding: utf-8 -*-

import pygame
from typing import Optional, List

class AnimatedText:
    """
    Texte révélé lettre par lettre.
    - speed: caractères par seconde
    - max_width: si fourni, word-wrap automatique
    """
    def __init__(self, text: str, font: pygame.font.Font, pos, speed: int = 50,
                 max_width: Optional[int] = None, line_gap: int = 2):
        self.full_text = str(text or "")
        self.font = font
        self.pos = (int(pos[0]), int(pos[1]))
        self.speed = max(1, int(speed))
        self.max_width = max_width
        self.line_gap = int(line_gap)
        self.start_time = pygame.time.get_ticks()
        self.done = False

    def set_text(self, text: str):
        self.full_text = str(text or "")
        self.start_time = pygame.time.get_ticks()
        self.done = False

    def skip(self):
        """Affiche instantanément tout le texte."""
        self.speed = 10_000

    def draw(self, surface: pygame.Surface, color=(0, 0, 0)):
        elapsed = (pygame.time.get_ticks() - self.start_time) / 1000.0
        nb_chars = min(int(elapsed * self.speed), len(self.full_text))
        if nb_chars >= len(self.full_text):
            self.done = True
        visible = self.full_text[:nb_chars]

        # Découpe en lignes (support simple du \n)
        lines = visible.split("\n")

        x, y = self.pos
        for i, line in enumerate(lines):
            surf = self.font.render(line, True, color)
            surface.blit(surf, (x, y + i * (surf.get_height() + self.line_gap)))
