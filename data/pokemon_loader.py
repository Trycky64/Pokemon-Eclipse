# data/pokemon_loader.py
# -*- coding: utf-8 -*-

"""
Accès aux données des Pokémon (pokemon.json) + utilitaires :
- get_all_pokemon, get_pokemon_by_id, get_pokemon_by_name
- get_learnable_moves(pokemon_id, level) : 4 dernières attaques apprises (<= level)
"""

import json
import os
from functools import lru_cache
from typing import Dict, List, Optional

from data.moves_loader import get_move_by_name

POKEMON_PATH = os.path.join("data", "pokemon.json")


@lru_cache(maxsize=1)
def load_pokemon_data() -> List[Dict]:
    """Charge tout le fichier pokemon.json en mémoire."""
    with open(POKEMON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_all_pokemon() -> List[Dict]:
    """Retourne la liste complète des Pokémon (tel que dans le JSON)."""
    return list(load_pokemon_data())


def get_pokemon_by_id(pokemon_id: int) -> Dict:
    """Retourne un Pokémon à partir de son ID numérique (ou {} si introuvable)."""
    for p in load_pokemon_data():
        if int(p.get("id", -1)) == int(pokemon_id):
            return p
    return {}


def get_pokemon_by_name(name: str) -> Dict:
    """Retourne un Pokémon à partir de son nom (FR) insensible à la casse."""
    target = (name or "").strip().lower()
    for p in load_pokemon_data():
        if (p.get("name", "") or "").lower() == target:
            return p
    return {}


def get_pokemon_stats(pokemon_id: int) -> Dict:
    """Retourne le dict 'stats' d'un Pokémon."""
    p = get_pokemon_by_id(pokemon_id)
    return p.get("stats", {}) if p else {}


def _last_unique_moves_learned(learnset: List[Dict], level: int) -> List[str]:
    """
    À partir d'une liste [{"name": str, "level": int}, ...] renvoie les 4
    dernières attaques uniques apprises à un niveau <= level (ordre du plus récent au plus ancien).
    """
    last_by_name = {}
    for entry in learnset or []:
        name = entry.get("name")
        lvl = int(entry.get("level", 1))
        if not name:
            continue
        if lvl <= level:
            # On conserve la dernière occurrence (plus haut niveau)
            last_by_name[name] = max(lvl, last_by_name.get(name, 1))
    # Trier par niveau (desc) pour obtenir les plus récents d'abord
    sorted_names = sorted(last_by_name.items(), key=lambda kv: kv[1], reverse=True)
    return [name for name, _ in sorted_names[:4]]


def get_learnable_moves(pokemon_id: int, level: int) -> List[Dict]:
    """
    Construit la liste (max 4) des attaques apprises par montée de niveau (<= level).
    Renvoie des dicts complets (nom FR, type, power, accuracy, pp, etc.).
    """
    p = get_pokemon_by_id(pokemon_id)
    if not p:
        return []

    picked_names = _last_unique_moves_learned(p.get("moves", []), int(level or 1))

    moves: List[Dict] = []
    seen = set()
    for move_name in picked_names:
        if move_name in seen:
            continue
        move_data = get_move_by_name(move_name, language="fr")
        if not move_data:
            # Log non-bloquant, utile en debug
            print(f"[⚠] Attaque introuvable : {move_name} (pokemon_id={pokemon_id})")
            continue

        moves.append({
            "name": move_data.get("name_fr", move_data.get("name", move_name)),
            "type": move_data.get("type", "normal"),
            "power": move_data.get("power", 0) or 0,
            "accuracy": move_data.get("accuracy", 100) or 100,
            "pp": move_data.get("pp", 0) or 0,
            "max_pp": move_data.get("pp", 0) or 0,
            "damage_class": move_data.get("damage_class", "physical"),
            "effect": move_data.get("effect", "") or "",
            "effect_chance": move_data.get("effect_chance", None),
            "ailment": move_data.get("ailment", "none"),
            "priority": move_data.get("priority", 0) or 0,
            "target": move_data.get("target", "selected-pokemon"),
        })
        seen.add(move_name)

    return moves


# Alias occasionnellement attendu ailleurs
def get_pokemon_by_id_name(name: str) -> Dict:
    """Compatibilité : alias vers get_pokemon_by_name."""
    return get_pokemon_by_name(name)
