# battle/enemy_selector.py
# -*- coding: utf-8 -*-

"""
Sélection d'un ennemi équilibré en fonction du niveau de l'équipe du joueur.
Pas d'accès disque ici : on suppose que la liste des candidats est déjà fournie
ou que la scène appelle une autre couche pour charger.
"""

from typing import List, Dict
import random

def pick_enemy(candidates: List[Dict], target_level: int, rng: random.Random = None) -> Dict:
    """
    candidates: liste de Pokémon dict avec au moins {"name", "level", "stats": {"hp":..}}
    target_level: niveau moyen désiré
    Stratégie : minimiser |level - target_level|, tie-break aléatoire.
    """
    if rng is None:
        rng = random.Random()

    if not candidates:
        return {}

    best = []
    best_diff = 999
    for p in candidates:
        lvl = int(p.get("level", 1))
        diff = abs(lvl - int(target_level or 1))
        if diff < best_diff:
            best = [p]
            best_diff = diff
        elif diff == best_diff:
            best.append(p)

    return rng.choice(best)
