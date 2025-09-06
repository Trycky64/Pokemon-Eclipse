# ui/input_manager.py
# -*- coding: utf-8 -*-

import pygame

class InputManager:
    """
    Gestion des entrées clavier avec répétition façon GBA :
    - Délai initial avant répétition
    - Puis répétition à intervalle fixe
    """
    def __init__(self, initial_delay_ms=220, repeat_ms=80):
        self.initial = int(initial_delay_ms)
        self.repeat = int(repeat_ms)
        self._active = {}
        self._timers = {}

    def update(self, dt_ms: float):
        for k in list(self._timers):
            self._timers[k] = max(0, self._timers[k] - dt_ms)

    def pressed(self, key) -> bool:
        keys = pygame.key.get_pressed()
        if not keys[key]:
            self._active.pop(key, None)
            self._timers.pop(key, None)
            return False
        if key not in self._active:
            self._active[key] = True
            self._timers[key] = self.initial
            return True
        if self._timers[key] == 0:
            self._timers[key] = self.repeat
            return True
        return False
