# core/assets.py
# -*- coding: utf-8 -*-
"""
Gestion centralisée des assets (images, polices, sons) avec cache.
Toutes les conversions coûteuses (convert/convert_alpha) sont faites au chargement,
jamais pendant la boucle principale, pour garantir une UI fluide.
"""
from __future__ import annotations
import pygame
from functools import lru_cache
import os

# --- Images --------------------------------------------------------------

@lru_cache(maxsize=1024)
def load_image(path: str, alpha: bool = True) -> pygame.Surface:
    """
    Charge une image depuis le disque puis applique convert/convert_alpha immédiatement.

    Args:
        path: Chemin vers l'image (PNG/GIF/…).
        alpha: True = convert_alpha(), False = convert().
    Returns:
        Surface Pygame prête à blitter efficacement.
    """
    surf = pygame.image.load(path)
    return surf.convert_alpha() if alpha else surf.convert()

# --- Polices -------------------------------------------------------------

@lru_cache(maxsize=64)
def get_font(path: str, size: int) -> pygame.font.Font:
    """
    Récupère une police mise en cache.
    """
    return pygame.font.Font(path, size)

_TEXT_CACHE: dict[tuple, pygame.Surface] = {}

def render_text_cached(text: str, font_path: str, size: int, color, antialias: bool = True) -> pygame.Surface:
    """
    Rend un texte en le mettant en cache selon (texte, police, taille, couleur, AA).
    """
    key = (text, font_path, size, color, antialias)
    surf = _TEXT_CACHE.get(key)
    if surf is None:
        font = get_font(font_path, size)
        surf = font.render(text, antialias, color)
        _TEXT_CACHE[key] = surf
    return surf

# --- Sons ----------------------------------------------------------------

@lru_cache(maxsize=256)
def load_sound(path: str) -> pygame.mixer.Sound:
    """
    Charge un son (WAV/OGG) avec cache.
    """
    return pygame.mixer.Sound(path)

# --- Utilitaires chemins -------------------------------------------------

def resolve_path(*parts: str) -> str:
    """
    Construit un chemin relatif robuste à partir de segments (utile en dev/exe).
    """
    base = os.getcwd()
    return os.path.join(base, *parts)
