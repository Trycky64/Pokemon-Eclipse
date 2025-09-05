# ui/animated_text.py
# -*- coding: utf-8 -*-

import pygame


class AnimatedText:
    """
    Affichage progressif d'un texte (lettre par lettre).
    Args:
      text (str): texte complet
      font (pygame.font.Font)
      pos (x, y)
      speed (int): caractères par seconde
    """

    def __init__(self, text, font, pos, speed=50):
        self.full_text = text or ""
        self.font = font
        self.pos = tuple(pos)
        self.speed = int(speed or 50)
        self.start_time = pygame.time.get_ticks()
        self.done = False

    def reset(self, text=None):
        if text is not None:
            self.full_text = str(text)
        self.start_time = pygame.time.get_ticks()
        self.done = False

    def draw(self, surface: pygame.Surface, color=(0, 0, 0)):
        """
        Affiche le texte animé sur la surface. Met à jour self.done quand fini.
        """
        elapsed = (pygame.time.get_ticks() - self.start_time) / 1000.0
        nb_chars = min(int(elapsed * self.speed), len(self.full_text))
        visible_text = self.full_text[:nb_chars]
        if nb_chars >= len(self.full_text):
            self.done = True
        text_surface = self.font.render(visible_text, True, color)
        surface.blit(text_surface, self.pos)
