# scene/menu_scene.py
# -*- coding: utf-8 -*-

from __future__ import annotations
import pygame
import random
from typing import Optional, Dict

from core.scene_manager import Scene
from core.config import SCREEN_WIDTH, SCREEN_HEIGHT, DEFAULT_FONT_PATH
from core.assets import render_text_cached, get_font
from core.run_manager import run_manager

from scene.starter_scene import StarterScene
from scene.battle_scene import BattleScene
from data.pokemon_loader import get_all_pokemon, get_learnable_moves

class MenuScene(Scene):
    """
    Menu principal (GBA-like) :
      - Nouvelle partie (choix starter)
      - Combat aléatoire
      - Sac (affichage inventaire)
      - Quitter
    """

    def __init__(self):
        super().__init__()
        self.options = ["Nouvelle partie", "Combat aléatoire", "Sac", "Quitter"]
        self.index = 0
        self.title_font = get_font(DEFAULT_FONT_PATH, 28)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.index = (self.index - 1) % len(self.options)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.index = (self.index + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
                self._select()

    def _select(self):
        label = self.options[self.index]
        if label == "Nouvelle partie":
            if self.manager:
                self.manager.push_scene(StarterScene())
        elif label == "Combat aléatoire":
            # Si pas de Pokémon → forcer starter d'abord
            if not run_manager.team:
                if self.manager:
                    self.manager.push_scene(StarterScene())
                return
            # Ennemi équilibré simple : niveau proche du joueur
            player = run_manager.get_active_pokemon()
            lvl = int(player.get("level", 5))
            all_pkm = [p for p in get_all_pokemon() if p.get("stats")]
            enemy_base = random.choice(all_pkm) if all_pkm else {
                "id": 19, "name": "Rattata", "stats": {"hp": 30}, "types": ["normal"]
            }
            enemy = {
                "id": enemy_base["id"],
                "name": enemy_base["name"],
                "level": max(2, min(100, lvl + random.choice([-1, 0, 1]))),
                "types": enemy_base.get("types", []),
                "stats": dict(enemy_base.get("stats", {"hp": 30})),
            }
            enemy["hp"] = int(enemy["stats"].get("hp", 30))
            enemy["moves"] = get_learnable_moves(enemy["id"], enemy["level"])
            if self.manager:
                self.manager.push_scene(BattleScene(enemy))
        elif label == "Sac":
            # On peut afficher le sac depuis la scène de bag si tu l’ajoutes au stack,
            # mais comme le zip d'origine ne contenait qu'un bag_scene incomplet,
            # on laisse ici un message minimal pour indiquer l'action.
            # Tu peux pousser la BagScene si tu veux : from scene.bag_scene import BagScene
            # self.manager.push_scene(BagScene())
            pass
        elif label == "Quitter":
            import sys
            pygame.quit()
            sys.exit()

    def update(self, dt_ms: float):
        pass

    def draw(self, screen: pygame.Surface):
        screen.fill((240, 248, 255))
        title = self.title_font.render("Pokémon Eclipse", True, (20, 20, 28))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 86))

        for i, label in enumerate(self.options):
            surf = render_text_cached(label, DEFAULT_FONT_PATH, 20, (22, 22, 28))
            x = SCREEN_WIDTH // 2 - surf.get_width() // 2
            y = 170 + i * 32
            screen.blit(surf, (x, y))
            if i == self.index:
                arrow = render_text_cached("▶", DEFAULT_FONT_PATH, 20, (22, 22, 28))
                screen.blit(arrow, (x - 24, y))
