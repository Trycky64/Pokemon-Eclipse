# core/scene_manager.py
# -*- coding: utf-8 -*-
"""
Gestionnaire de scènes (pile de scènes façon GBA).
Fournit une base `Scene` et un `SceneManager` pour empiler/dépiler/changer.
"""
from __future__ import annotations
from typing import List, Optional

class Scene:
    """
    Classe de base des scènes. À surcharger.
    """
    def __init__(self):
        self.manager: Optional[SceneManager] = None

    # Cycle de vie
    def on_enter(self): pass
    def on_exit(self): pass

    # Boucle jeu
    def handle_event(self, event): pass
    def update(self, dt_ms: float): pass
    def draw(self, screen): pass

class SceneManager:
    """
    Gère une pile de scènes actives.
    """
    def __init__(self):
        self.scene_stack: List[Scene] = []

    # Accès
    @property
    def current(self) -> Optional[Scene]:
        return self.scene_stack[-1] if self.scene_stack else None

    # Transitions
    def push_scene(self, scene: Scene) -> None:
        if self.current:
            # La scène sous-jacente reste en pause/masquée
            pass
        scene.manager = self
        self.scene_stack.append(scene)
        scene.on_enter()

    def pop_scene(self) -> None:
        if not self.scene_stack:
            return
        top = self.scene_stack.pop()
        try:
            top.on_exit()
        finally:
            top.manager = None

    def change_scene(self, new_scene: Scene) -> None:
        """
        Remplace la scène courante par `new_scene`.
        """
        if self.current:
            self.current.on_exit()
            self.current.manager = None
            self.scene_stack.pop()
        new_scene.manager = self
        self.scene_stack.append(new_scene)
        new_scene.on_enter()

    # Délégation boucle de jeu
    def handle_event(self, event) -> None:
        if self.current:
            self.current.handle_event(event)

    def update(self, dt_ms: float) -> None:
        if self.current:
            self.current.update(dt_ms)

    def draw(self, screen) -> None:
        if self.current:
            self.current.draw(screen)
