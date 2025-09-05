# core/assets.py
# -*- coding: utf-8 -*-

import pygame
from functools import lru_cache


@lru_cache(maxsize=1024)
def load_image(path: str, alpha: bool = True) -> pygame.Surface:
    """
    Charge une image puis convert/convert_alpha immédiatement (perf).
    """
    surf = pygame.image.load(path)
    return surf.convert_alpha() if alpha else surf.convert()


@lru_cache(maxsize=64)
def get_font(path: str, size: int) -> pygame.font.Font:
    return pygame.font.Font(path, size)


_text_cache = {}


def render_text_cached(text: str, font_path: str, size: int, color, antialias=True) -> pygame.Surface:
    key = (text, font_path, size, color, antialias)
    if key not in _text_cache:
        font = get_font(font_path, size)
        _text_cache[key] = font.render(text, antialias, color)
    return _text_cache[key]
