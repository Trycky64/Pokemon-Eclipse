# scene/battle_scene.py
# -*- coding: utf-8 -*-

from __future__ import annotations
import os
import pygame
from typing import List, Dict, Optional, Callable, Tuple
import random

from core.scene_manager import Scene
from core.config import SCREEN_WIDTH, SCREEN_HEIGHT, DEFAULT_FONT_PATH
from core.assets import load_image, get_font, render_text_cached
from core.run_manager import run_manager
from battle.ai import BattleAI
from battle.move_handler import execute_move
from battle.use_item import use_item
from battle.evolution_handler import check_evolution

from ui.health_bar import HealthBar
from ui.xp_bar import XPBar
from ui.input_manager import InputManager
from ui.animated_text import AnimatedText


# --------------------------------------------------------------------------------------
# Actions non bloquantes (file d'actions façon GBA)
# --------------------------------------------------------------------------------------

class Action:
    """Interface minimale d'une action séquentielle."""
    def start(self, scene: "BattleScene"): ...
    def update(self, scene: "BattleScene", dt_ms: float): ...
    def finished(self) -> bool: return True


class TextAction(Action):
    """Affiche un texte avec écriture progressive, attend validation (Enter/Space/Z)."""
    def __init__(self, text: str):
        self.text = text
        self._started = False
        self._done = False
        self._anim: Optional[AnimatedText] = None

    def start(self, scene: "BattleScene"):
        font = get_font(DEFAULT_FONT_PATH, 18)
        # Position calée dans la textbox
        self._anim = AnimatedText(self.text, font, (36, SCREEN_HEIGHT - 78), speed=60)
        self._started = True

    def update(self, scene: "BattleScene", dt_ms: float):
        if not self._started: self.start(scene)
        # Appui joueur = passe au message suivant
        if scene._confirm_pressed:
            self._done = True

    def finished(self) -> bool:
        return self._done


class DelayAction(Action):
    """Attend un temps donné en ms (utile entre animations/effets)."""
    def __init__(self, delay_ms: int):
        self.remaining = max(0, int(delay_ms))

    def start(self, scene: "BattleScene"): ...
    def update(self, scene: "BattleScene", dt_ms: float):
        self.remaining = max(0, self.remaining - int(dt_ms))
    def finished(self) -> bool:
        return self.remaining == 0


class CallableAction(Action):
    """Exécute une fonction immédiate (logique) et termine."""
    def __init__(self, fn: Callable[["BattleScene"], None]):
        self.fn = fn
        self._done = False

    def start(self, scene: "BattleScene"):
        self.fn(scene)
        self._done = True

    def update(self, scene: "BattleScene", dt_ms: float): ...
    def finished(self) -> bool: return self._done


# --------------------------------------------------------------------------------------
# Scène de combat
# --------------------------------------------------------------------------------------

class BattleScene(Scene):
    """
    Scène de combat 1v1 façon GBA.
    - File d’actions non bloquante : messages, dégâts, effets, capture, XP, niveau/évo.
    - UI fluide : HP/XP animées, saisie clavier avec répétition douce.
    """

    def __init__(self, enemy_pokemon: Dict, rng: Optional[random.Random] = None):
        super().__init__()
        self.rng = rng or random.Random()

        # Équipe joueur / ennemi
        self.player: Dict = run_manager.get_active_pokemon() or {}
        self.enemy: Dict = dict(enemy_pokemon or {})
        self.enemy.setdefault("name", "???")
        self.enemy.setdefault("stats", {})
        self.enemy.setdefault("hp", int(self.enemy.get("stats", {}).get("hp", 20)))
        self.enemy.setdefault("status", "none")
        self.enemy.setdefault("level", self.enemy.get("level", 5))

        # IA
        self.ai = BattleAI(skill_level=1, rng=self.rng)

        # UI / assets
        self._bg = load_image("assets/ui/battle/background.png", alpha=True) if _safe_exists("assets/ui/battle/background.png") else None
        self._hud = load_image("assets/ui/battle/hud.png", alpha=True) if _safe_exists("assets/ui/battle/hud.png") else None
        self._textbox = load_image("assets/ui/battle/textbox.png", alpha=True) if _safe_exists("assets/ui/battle/textbox.png") else None

        # Polices (cache via core.assets)
        self.font_small = get_font(DEFAULT_FONT_PATH, 16)
        self.font_label = get_font(DEFAULT_FONT_PATH, 18)
        self.font_menu = get_font(DEFAULT_FONT_PATH, 20)

        # Barres HP allié/ennemi
        self.ally_hp_bar = HealthBar(pos=(302, 232), size=(128, 6),
                                     max_hp=int(self.player.get("stats", {}).get("hp", self.player.get("hp", 1))))
        self.ally_hp_bar.set_show_text(True)
        self.enemy_hp_bar = HealthBar(pos=(62, 46), size=(128, 6),
                                      max_hp=int(self.enemy.get("stats", {}).get("hp", self.enemy.get("hp", 1))))

        # XP (allié uniquement)
        self.ally_xp_bar = XPBar(pos=(302, 252), max_xp=1)  # borne fixée en on_enter

        # Menus
        self.input = InputManager()
        self.menu_index = 0          # Combat / Sac / Pokémon / Fuite
        self.submenu_index = 0       # curseur sur attaques / objets
        self._menu_mode = "root"     # "root" | "moves" | "bag" | "pokemon" | "message"
        self._confirm_pressed = False

        # File d’actions
        self._queue: List[Action] = []
        self._current: Optional[Action] = None

        # Sélection de move/item
        self._selected_move: Optional[int] = None
        self._selected_item: Optional[Dict] = None

        # États divers
        self._battle_over = False

    # ----------------------------------------------------------------------------------
    # Cycle de vie
    # ----------------------------------------------------------------------------------

    def on_enter(self):
        # Normalise le Pokémon joueur si besoin
        self.player.setdefault("name", "??")
        self.player.setdefault("level", self.player.get("level", 5))
        self.player.setdefault("stats", self.player.get("stats", {}))
        self.player.setdefault("hp", int(self.player.get("hp", self.player.get("stats", {}).get("hp", 20))))
        self.player.setdefault("status", self.player.get("status", "none"))

        # Configure les barres
        self.ally_hp_bar.set_max_hp(int(self.player["stats"].get("hp", self.player["hp"])))
        self.enemy_hp_bar.set_max_hp(int(self.enemy["stats"].get("hp", self.enemy["hp"])))

        # XP intra-niveau
        xp_in_level, xp_needed = self._calc_xp_in_level(self.player)
        self.ally_xp_bar.set_max_xp(xp_needed)
        self.ally_xp_bar.reset_displayed_xp(xp_in_level)

        # Message d’ouverture
        self.push(TextAction(f"Un {self.enemy['name']} sauvage apparaît !"))

    def on_exit(self):
        pass

    # ----------------------------------------------------------------------------------
    # File d’actions
    # ----------------------------------------------------------------------------------

    def push(self, action: Action):
        self._queue.append(action)

    def _advance_queue(self, dt_ms: float):
        if self._current is None and self._queue:
            self._current = self._queue.pop(0)
            self._current.start(self)
        if self._current:
            self._current.update(self, dt_ms)
            if self._current.finished():
                self._current = None

    # ----------------------------------------------------------------------------------
    # Entrées utilisateur
    # ----------------------------------------------------------------------------------

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
                self._confirm_pressed = True

    # ----------------------------------------------------------------------------------
    # Update & Draw
    # ----------------------------------------------------------------------------------

    def update(self, dt_ms: float):
        self._confirm_pressed = False
        self.input.update(dt_ms)

        # Une action en cours ?
        if self._current or self._queue:
            self._advance_queue(dt_ms)
            return

        # Fin de combat → pop scène
        if self._battle_over:
            if self.manager:
                self.manager.pop_scene()
            return

        # Menus
        if self._menu_mode == "root":
            self._update_menu_root()
        elif self._menu_mode == "moves":
            self._update_menu_moves()
        elif self._menu_mode == "bag":
            self._update_menu_bag()
        elif self._menu_mode == "pokemon":
            self._update_menu_pokemon()
        else:
            self._menu_mode = "root"

        # Met à jour visuellement les barres (dt)
        self.ally_hp_bar.update(int(self.player["hp"]), dt_ms)
        self.enemy_hp_bar.update(int(self.enemy["hp"]), dt_ms)

        xp_in_level, xp_needed = self._calc_xp_in_level(self.player)
        self.ally_xp_bar.set_max_xp(xp_needed)
        self.ally_xp_bar.update(xp_in_level, dt_ms)

    def draw(self, screen):
        # Fond
        if self._bg:
            screen.blit(self._bg, (0, 0))
        else:
            screen.fill((228, 240, 255))

        # HUD + barres
        self._draw_hud(screen)

        # Textbox (fond)
        self._draw_textbox(screen)

        # Affichage menu / texte animé
        self._draw_menu_or_text(screen)

    # ----------------------------------------------------------------------------------
    # Menus
    # ----------------------------------------------------------------------------------

    def _update_menu_root(self):
        # Navigation 2x2 : [Combat, Sac, Pokémon, Fuite]
        if self.input.pressed(pygame.K_LEFT):  self.menu_index = (self.menu_index + 3) % 4
        if self.input.pressed(pygame.K_RIGHT): self.menu_index = (self.menu_index + 1) % 4
        if self.input.pressed(pygame.K_UP):    self.menu_index = (self.menu_index + 2) % 4
        if self.input.pressed(pygame.K_DOWN):  self.menu_index = (self.menu_index + 2) % 4

        if self._confirm_pressed:
            if self.menu_index == 0:      # Combat
                self._menu_mode = "moves"
                self.submenu_index = 0
            elif self.menu_index == 1:    # Sac
                self._menu_mode = "bag"
                self.submenu_index = 0
            elif self.menu_index == 2:    # Pokémon
                self._menu_mode = "pokemon"
            elif self.menu_index == 3:    # Fuite
                self._try_run_away()

    def _update_menu_moves(self):
        moves = self.player.get("moves", [])
        if not moves:
            self.push(TextAction("Aucune attaque disponible."))
            self._menu_mode = "root"
            return

        # curseur vertical 2x2 max
        if self.input.pressed(pygame.K_LEFT):  self.submenu_index = (self.submenu_index + len(moves) - 1) % len(moves)
        if self.input.pressed(pygame.K_RIGHT): self.submenu_index = (self.submenu_index + 1) % len(moves)
        if self.input.pressed(pygame.K_UP):    self.submenu_index = (self.submenu_index - 2) % len(moves) if len(moves) > 2 else self.submenu_index
        if self.input.pressed(pygame.K_DOWN):  self.submenu_index = (self.submenu_index + 2) % len(moves) if len(moves) > 2 else self.submenu_index

        if self._confirm_pressed:
            self._selected_move = self.submenu_index
            self._player_use_move()

        # Retour (X/Echap/Backspace)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_x] or keys[pygame.K_ESCAPE] or keys[pygame.K_BACKSPACE]:
            self._menu_mode = "root"

    def _update_menu_bag(self):
        items = run_manager.get_items_as_inventory()
        if not items:
            self.push(TextAction("Votre sac est vide."))
            self._menu_mode = "root"
            return

        if self.input.pressed(pygame.K_UP):    self.submenu_index = (self.submenu_index - 1) % len(items)
        if self.input.pressed(pygame.K_DOWN):  self.submenu_index = (self.submenu_index + 1) % len(items)

        if self._confirm_pressed:
            self._selected_item = items[self.submenu_index]
            self._player_use_item(self._selected_item)

        # Retour
        keys = pygame.key.get_pressed()
        if keys[pygame.K_x] or keys[pygame.K_ESCAPE] or keys[pygame.K_BACKSPACE]:
            self._menu_mode = "root"

    def _update_menu_pokemon(self):
        # Pour l’instant : retour direct (scène mono-Pokémon)
        self.push(TextAction("Fonctionnalité à venir : gestion d'équipe."))
        self._menu_mode = "root"

    # ----------------------------------------------------------------------------------
    # Logique d’actions combat
    # ----------------------------------------------------------------------------------

    def _player_use_move(self):
        moves = self.player.get("moves", [])
        if self._selected_move is None or self._selected_move >= len(moves):
            self.push(TextAction("Action impossible."))
            self._menu_mode = "root"
            return

        move = moves[self._selected_move]

        def _do(scene: "BattleScene"):
            res = execute_move(scene.player, scene.enemy, move, rng=scene.rng)
            for msg in res["messages"]:
                scene.push(TextAction(msg))

            # MAJ barres
            scene.enemy_hp_bar.set_max_hp(int(scene.enemy["stats"].get("hp", scene.enemy["hp"])))
            scene.enemy_hp_bar.update(int(scene.enemy["hp"]), 0)

            # KO ennemi ?
            if scene.enemy["hp"] <= 0:
                scene._on_enemy_fainted()
            else:
                # Tour de l'ennemi
                scene.push(DelayAction(200))
                scene.push(CallableAction(lambda s: s._enemy_turn()))

        self.push(CallableAction(_do))
        self._menu_mode = "message"

    def _enemy_turn(self):
        # Choix IA
        act = self.ai.choose_action(self.enemy, self.player)
        if act.get("type") == "move":
            idx = act.get("index", 0)
            moves = self.enemy.get("moves", [])
            if not moves:
                self.push(TextAction(f"{self.enemy['name']} hésite…"))
                self._menu_mode = "root"
                return
            mv = moves[idx % len(moves)]
            res = execute_move(self.enemy, self.player, mv, rng=self.rng)
            for msg in res["messages"]:
                self.push(TextAction(msg))

            # MAJ barres HP allié
            self.ally_hp_bar.set_max_hp(int(self.player["stats"].get("hp", self.player["hp"])))
            self.ally_hp_bar.update(int(self.player["hp"]), 0)

            # KO allié ?
            if self.player["hp"] <= 0:
                self._on_player_fainted()
            else:
                self.push(DelayAction(150))
                self.push(TextAction("Que doit faire votre Pokémon ?"))
                self._menu_mode = "root"

        elif act.get("type") == "item":
            item_name = act.get("item")
            ctx = {"item": {"name": item_name, "quantity": 1}, "user": self.enemy, "target": self.enemy}
            res = use_item(ctx)
            for msg in res["messages"]:
                self.push(TextAction(msg))
            # MAJ HP ennemie si soin
            self.enemy_hp_bar.set_max_hp(int(self.enemy["stats"].get("hp", self.enemy["hp"])))
            self.enemy_hp_bar.update(int(self.enemy["hp"]), 0)
            self.push(DelayAction(150))
            self.push(TextAction("Que doit faire votre Pokémon ?"))
            self._menu_mode = "root"
        else:
            self.push(TextAction(f"{self.enemy['name']} attend."))
            self._menu_mode = "root"

    def _player_use_item(self, item_entry: Dict):
        name = item_entry.get("name")
        qty = item_entry.get("quantity", 0)
        if not name or qty <= 0:
            self.push(TextAction("Objet indisponible."))
            self._menu_mode = "root"
            return

        def _do(scene: "BattleScene"):
            ctx = {"item": {"name": name, "quantity": 1}, "user": scene.player, "target": scene.enemy}
            res = use_item(ctx)
            for msg in res["messages"]:
                scene.push(TextAction(msg))

            # Si c'était une ball et succès → fin du combat + ajout à l'équipe si place
            if res.get("capture", None) is not None:
                if res["success"]:
                    if run_manager.add_pokemon_to_team(scene.enemy):
                        scene.push(TextAction(f"{scene.enemy['name']} rejoint votre équipe !"))
                    scene._battle_over = True
                else:
                    # Tour de l'ennemi
                    scene.push(DelayAction(200))
                    scene.push(CallableAction(lambda s: s._enemy_turn()))
            # Décrément inventaire
            run_manager.remove_item(name, 1)

        self.push(CallableAction(_do))
        self._menu_mode = "message"

    def _try_run_away(self):
        # Fuite simple (probabilité fixe, on pourra lier à la Vitesse)
        if self.rng.random() < 0.6:
            self.push(TextAction("Vous prenez la fuite !"))
            self._battle_over = True
        else:
            self.push(TextAction("Impossible de fuir !"))
            self.push(DelayAction(200))
            self.push(CallableAction(lambda s: s._enemy_turn()))

    def _on_enemy_fainted(self):
        self.push(TextAction(f"{self.enemy['name']} est K.O. !"))
        # Gain d'XP simple (tu peux raffiner avec base_experience, niveau, etc.)
        gain = max(8, int(4 + self.enemy.get("level", 5) * 3))
        self.push(CallableAction(lambda s: s._give_xp(self.player, gain)))
        # Fin du combat pour cette scène mono-ennemi
        self.push(TextAction("Le combat est terminé."))
        self._battle_over = True

    def _on_player_fainted(self):
        self.push(TextAction(f"{self.player['name']} est K.O. !"))
        self.push(TextAction("Plus de Pokémon en état de se battre…"))
        self._battle_over = True

    # ----------------------------------------------------------------------------------
    # XP / Niveau / Évolution
    # ----------------------------------------------------------------------------------

    def _give_xp(self, pokemon: Dict, amount: int):
        pokemon.setdefault("xp_total", 0)
        pokemon["xp_total"] = int(pokemon["xp_total"]) + int(amount)

        self.push(TextAction(f"{pokemon['name']} gagne {amount} XP !"))
        # Recalcule niveau réel + progression
        new_level = self._level_from_xp(pokemon["xp_total"])
        if new_level > pokemon["level"]:
            # Level up multi-niveaux possible
            while pokemon["level"] < new_level:
                pokemon["level"] += 1
                self._recalc_stats_for_level(pokemon)
                self.push(TextAction(f"{pokemon['name']} monte au niveau {pokemon['level']} !"))
                # Évolution potentielle
                evo_to = check_evolution(pokemon)
                if evo_to:
                    self._apply_evolution(pokemon, evo_to)

        # Met à jour la barre d'XP (intra-niveau)
        xp_in_level, xp_needed = self._calc_xp_in_level(pokemon)
        self.ally_xp_bar.set_max_xp(xp_needed)
        self.ally_xp_bar.update(xp_in_level, 0)

    def _apply_evolution(self, pokemon: Dict, evo_id: int):
        from data.pokemon_loader import get_pokemon_by_id
        evo_data = get_pokemon_by_id(evo_id)
        if not evo_data:
            self.push(TextAction("… mais rien ne se passe."))
            return

        old_name = pokemon["name"]
        pokemon["name"] = evo_data.get("name", pokemon["name"])
        pokemon["id"] = evo_id
        pokemon["stats"] = evo_data.get("stats", pokemon.get("stats", {}))
        pokemon["types"] = evo_data.get("types", pokemon.get("types", []))
        # HP plein à l’évolution (choix de design)
        pokemon["hp"] = int(pokemon["stats"].get("hp", pokemon["hp"]))
        self.ally_hp_bar.set_max_hp(int(pokemon["stats"].get("hp", pokemon["hp"])))

        self.push(TextAction(f"Quoi ? {old_name} évolue en {pokemon['name']} !"))

    # ----------------------------------------------------------------------------------
    # Outils XP / niveaux (cohérent avec bugfix XPBar)
    # ----------------------------------------------------------------------------------

    def _xp_for_level(self, level: int) -> int:
        """Courbe d'XP simplifiée (rapide). Tu peux brancher ta vraie courbe ici."""
        l = max(1, int(level))
        return int(0.8 * (l ** 3))

    def _level_from_xp(self, xp_total: int) -> int:
        level = 1
        while xp_total >= self._xp_for_level(level + 1) and level < 100:
            level += 1
        return level

    def _calc_xp_in_level(self, pokemon: Dict) -> Tuple[int, int]:
        """
        Renvoie (xp_dans_le_niveau, xp_requise_pour_niveau_suivant)
        Clamp strict pour éviter la barre à 100% à tort.
        """
        level = int(pokemon.get("level", 1))
        total = int(pokemon.get("xp_total", 0))
        cur_min = self._xp_for_level(level)
        nxt_min = self._xp_for_level(level + 1)
        need = max(1, nxt_min - cur_min)
        in_lvl = max(0, min(total - cur_min, need))
        return in_lvl, need

    def _recalc_stats_for_level(self, pokemon: Dict):
        """
        Recalcule basiquement les stats au level-up (simple et stable).
        Si tu as une vraie formule, remplace-la ici.
        """
        base = dict(pokemon.get("stats", {}))
        # Boost doux : +2 PV et +1 autres par level (par rapport au niveau précédent)
        base["hp"] = int(base.get("hp", 20) + 2)
        base["attack"] = int(base.get("attack", 10) + 1)
        base["defense"] = int(base.get("defense", 10) + 1)
        base["sp_attack"] = int(base.get("sp_attack", 10) + 1)
        base["sp_defense"] = int(base.get("sp_defense", 10) + 1)
        base["speed"] = int(base.get("speed", 10) + 1)
        pokemon["stats"] = base
        # Restaure un peu de PV au up (sans dépasser)
        pokemon["hp"] = min(int(base["hp"]), int(pokemon.get("hp", base["hp"])) + 4)
        self.ally_hp_bar.set_max_hp(int(base["hp"]))

    # ----------------------------------------------------------------------------------
    # Dessin HUD / Menus / Textbox
    # ----------------------------------------------------------------------------------

    def _draw_hud(self, screen: pygame.Surface):
        if self._hud:
            screen.blit(self._hud, (0, 0))

        # Ennemi (nom / lvl / PV)
        enemy_name = render_text_cached(self.enemy["name"], DEFAULT_FONT_PATH, 18, (22, 22, 28))
        enemy_lvl = render_text_cached(f"N.{self.enemy.get('level', 5)}", DEFAULT_FONT_PATH, 18, (22, 22, 28))
        screen.blit(enemy_name, (62, 26))
        screen.blit(enemy_lvl, (184, 26))
        self.enemy_hp_bar.draw(screen)

        # Joueur (nom / lvl / PV / XP)
        ally_name = render_text_cached(self.player["name"], DEFAULT_FONT_PATH, 18, (22, 22, 28))
        ally_lvl = render_text_cached(f"N.{self.player.get('level', 5)}", DEFAULT_FONT_PATH, 18, (22, 22, 28))
        screen.blit(ally_name, (302, 212))
        screen.blit(ally_lvl, (424, 212))
        self.ally_hp_bar.draw(screen)
        self.ally_xp_bar.draw(screen)

    def _draw_textbox(self, screen: pygame.Surface):
        if self._textbox:
            screen.blit(self._textbox, (0, SCREEN_HEIGHT - 96))
        else:
            # Fallback si pas d'asset
            pygame.draw.rect(screen, (245, 245, 245), (0, SCREEN_HEIGHT - 96, SCREEN_WIDTH, 96))
            pygame.draw.rect(screen, (32, 32, 32), (0, SCREEN_HEIGHT - 96, SCREEN_WIDTH, 96), 2)

    def _draw_menu_or_text(self, screen: pygame.Surface):
        # Si un TextAction est en cours, c'est AnimatedText qui dessine
        if isinstance(self._current, TextAction) and self._current._anim:
            self._current._anim.draw(screen, color=(22, 22, 28))
            return

        # Sinon, afficher le menu correspondant
        if self._menu_mode == "root":
            self._draw_root_menu(screen)
        elif self._menu_mode == "moves":
            self._draw_moves_menu(screen)
        elif self._menu_mode == "bag":
            self._draw_bag_menu(screen)
        elif self._menu_mode == "pokemon":
            self._draw_simple_text(screen, "Gestion d'équipe bientôt !")

    def _draw_root_menu(self, screen: pygame.Surface):
        # Quadrillage 2x2
        labels = ["Combat", "Sac", "Pokémon", "Fuite"]
        positions = [(316, SCREEN_HEIGHT - 80), (420, SCREEN_HEIGHT - 80),
                     (316, SCREEN_HEIGHT - 52), (420, SCREEN_HEIGHT - 52)]

        for i, (label, pos) in enumerate(zip(labels, positions)):
            color = (22, 22, 28)
            surf = render_text_cached(label, DEFAULT_FONT_PATH, 20, color)
            screen.blit(surf, pos)
            if i == self.menu_index:
                # Curseur ▶
                arrow = render_text_cached("▶", DEFAULT_FONT_PATH, 20, color)
                screen.blit(arrow, (pos[0] - 18, pos[1]))

    def _draw_moves_menu(self, screen: pygame.Surface):
        moves = self.player.get("moves", [])
        if not moves:
            self._draw_simple_text(screen, "Aucune attaque.")
            return

        # Affiche jusqu’à 4 attaques en grille 2x2
        grid_pos = [(24, SCREEN_HEIGHT - 84), (220, SCREEN_HEIGHT - 84),
                    (24, SCREEN_HEIGHT - 56), (220, SCREEN_HEIGHT - 56)]
        for i, mv in enumerate(moves[:4]):
            name = mv.get("name", "???")
            pp = f"{mv.get('pp', 0)}/{mv.get('max_pp', mv.get('pp', 0))}"
            label = f"{name}  (PP {pp})"
            pos = grid_pos[i]
            color = (22, 22, 28)
            surf = render_text_cached(label, DEFAULT_FONT_PATH, 18, color)
            screen.blit(surf, pos)
            if i == self.submenu_index:
                arrow = render_text_cached("▶", DEFAULT_FONT_PATH, 18, color)
                screen.blit(arrow, (pos[0] - 18, pos[1]))

        # Type de l’attaque sélectionnée (feedback)
        sel = moves[self.submenu_index]
        type_label = render_text_cached(f"Type: {sel.get('type','?')}", DEFAULT_FONT_PATH, 18, (22, 22, 28))
        screen.blit(type_label, (316, SCREEN_HEIGHT - 84))

    def _draw_bag_menu(self, screen: pygame.Surface):
        items = run_manager.get_items_as_inventory()
        if not items:
            self._draw_simple_text(screen, "Votre sac est vide.")
            return

        base_y = SCREEN_HEIGHT - 84
        for i, it in enumerate(items[:5]):
            name = it.get("name", "?")
            qty = it.get("quantity", 0)
            label = f"{name}  x{qty}"
            y = base_y + i * 18
            color = (22, 22, 28)
            surf = render_text_cached(label, DEFAULT_FONT_PATH, 18, color)
            screen.blit(surf, (24, y))
            if i == self.submenu_index:
                arrow = render_text_cached("▶", DEFAULT_FONT_PATH, 18, color)
                screen.blit(arrow, (6, y))

    def _draw_simple_text(self, screen: pygame.Surface, text: str):
        surf = render_text_cached(text, DEFAULT_FONT_PATH, 18, (22, 22, 28))
        screen.blit(surf, (24, SCREEN_HEIGHT - 78))


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------

def _safe_exists(path: str) -> bool:
    try:
        return os.path.exists(path)
    except Exception:
        return False
