# scene/starter_scene.py
# -*- coding: utf-8 -*-

from __future__ import annotations
import pygame
from typing import List, Dict

from core.scene_manager import Scene
from core.config import SCREEN_WIDTH, SCREEN_HEIGHT, DEFAULT_FONT_PATH
from core.assets import render_text_cached
from core.run_manager import run_manager
from data.pokemon_loader import get_pokemon_by_id, get_learnable_moves

DEFAULT_STARTERS = [1, 4, 7]  # Bulbizarre, Salamèche, Carapuce — FR

class StarterScene(Scene):
    """
    Choix du starter : trois options. Charge depuis run_manager.starters si dispo,
    sinon fallback sur 1/4/7. Niveau 5, moves via learnset.
    """

    def __init__(self):
        super().__init__()
        # Préparer la liste des starters
        self.index = 0
        self.starters: List[Dict] = []
        if run_manager.starters:
            # run_manager.starters devrait déjà contenir des dicts complets
            self.starters = [
                {
                    "id": s.get("id"),
                    "name": s.get("name", "???"),
                    "base": s,
                }
                for s in run_manager.starters[:3]
                if s.get("id")
            ]
        else:
            for sid in DEFAULT_STARTERS:
                base = get_pokemon_by_id(sid)
                if base:
                    self.starters.append({"id": sid, "name": base.get("name", "???"), "base": base})

        # Si moins de 3, on complète avec des placeholders
        while len(self.starters) < 3:
            self.starters.append({"id": 19, "name": "Rattata", "base": get_pokemon_by_id(19)})

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.index = (self.index + 2) % 3
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.index = (self.index + 1) % 3
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
                self._choose()

    def _choose(self):
        chosen = self.starters[self.index]
        base = chosen["base"] or {}
        # Crée une instance de Pokémon jouable
        level = 5
        stats = dict(base.get("stats", {"hp": 20}))
        pkm = {
            "id": chosen["id"],
            "name": base.get("name", "???"),
            "level": level,
            "types": base.get("types", []),
            "stats": stats,
            "hp": int(stats.get("hp", 20)),
            "status": "none",
            "xp_total": 0,
            "moves": get_learnable_moves(chosen["id"], level),
        }
        run_manager.start_new_run(pkm)

        # Retour menu
        from scene.menu_scene import MenuScene
        if self.manager:
            self.manager.change_scene(MenuScene())

    def update(self, dt_ms: float):
        pass

    def draw(self, screen: pygame.Surface):
        screen.fill((250, 250, 250))
        title = render_text_cached("Choisissez votre starter", DEFAULT_FONT_PATH, 22, (22, 22, 28))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 70))

        # Affiche 3 options sur une ligne
        cx = [SCREEN_WIDTH // 2 - 180, SCREEN_WIDTH // 2, SCREEN_WIDTH // 2 + 180]
        for i, s in enumerate(self.starters):
            label = f"{s['name']}"
            surf = render_text_cached(label, DEFAULT_FONT_PATH, 20, (22, 22, 28))
            x = cx[i] - surf.get_width() // 2
            y = 160
            screen.blit(surf, (x, y))
            if i == self.index:
                arrow = render_text_cached("▼", DEFAULT_FONT_PATH, 20, (22, 22, 28))
                screen.blit(arrow, (cx[i] - arrow.get_width() // 2, y - 28))
