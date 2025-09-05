# battle/evolution_handler.py
# -*- coding: utf-8 -*-

"""
Gestion de l'évolution après montée de niveau (format PokéAPI-like).
On suppose que les données de Pokémon contiennent un arbre d'évolution de type :
pokemon["evolution"] = [
  { "to": 2, "trigger": "level-up", "min_level": 16 },
  { "to": 3, "trigger": "level-up", "min_level": 36 }
]
"""

from typing import Dict, Optional, List

def _find_next_level_up_evo(evo_list: List[Dict], level: int) -> Optional[int]:
    """Retourne l'ID cible si une évolution par level-up est possible au niveau actuel."""
    if not evo_list:
        return None
    eligible = []
    for e in evo_list:
        if (e.get("trigger") == "level-up") and (int(e.get("min_level", 999)) <= int(level)):
            eligible.append(int(e.get("to")))
    if not eligible:
        return None
    # Si plusieurs possibles (rare), prendre le plus petit ID
    return sorted(eligible)[0]

def check_evolution(pokemon: Dict) -> Optional[int]:
    """
    Si le Pokémon peut évoluer maintenant, retourne l'ID du Pokémon évolué.
    Sinon None.
    """
    level = int(pokemon.get("level", 1))
    evo_list = pokemon.get("evolution", [])
    return _find_next_level_up_evo(evo_list, level)
