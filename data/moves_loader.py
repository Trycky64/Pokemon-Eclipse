# data/moves_loader.py
# -*- coding: utf-8 -*-

"""
Charge et fournit l'accès aux données des attaques (moves.json).
Inclut des fonctions utilitaires pour récupérer des informations sur les attaques.

Schéma moves.json (extrait) :
[
  {
    "id": 1,
    "name_en": "pound",
    "name_fr": "Écras’Face",
    "type": "normal",
    "damage_class": "physical",
    "power": 40,
    "accuracy": 100,
    "pp": 35,
    "priority": 0,
    "effect": "",
    "description": "…",
    "effect_chance": null,
    "ailment": "none",
    "target": "selected-pokemon"
  },
  ...
]
"""

import json
import os
from functools import lru_cache
from typing import Dict, List, Optional

MOVES_PATH = os.path.join("data", "moves.json")


@lru_cache(maxsize=1)
def load_moves_data() -> List[Dict]:
    """Charge toutes les attaques depuis le fichier JSON (avec mise en cache)."""
    with open(MOVES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _normalize_move_record(move: Dict, language: str = "fr") -> Dict:
    """
    Retourne une copie normalisée de l'attaque, avec une clé 'name' cohérente.
    language: "fr" ou "en" (par défaut "fr" pour coller à l'UI FR).
    """
    m = dict(move)
    name_key = "name_fr" if language == "fr" else "name_en"
    # Ajout d'un champ 'name' pour compatibilité (ex: logs, UI, move_handler).
    m["name"] = m.get(name_key, m.get("name_fr") or m.get("name_en") or "")
    # Défauts robustes
    m.setdefault("type", "normal")
    m.setdefault("damage_class", "physical")
    m.setdefault("power", 0)
    m.setdefault("accuracy", 100)
    m.setdefault("pp", 0)
    m.setdefault("priority", 0)
    m.setdefault("effect", "")
    m.setdefault("description", "")
    m.setdefault("effect_chance", None)
    m.setdefault("ailment", "none")
    m.setdefault("target", "selected-pokemon")
    return m


def get_all_moves(language: str = "fr") -> List[Dict]:
    """Retourne la liste de toutes les attaques normalisées (avec 'name')."""
    return [_normalize_move_record(m, language=language) for m in load_moves_data()]


def get_move_by_name(move_name: str, language: str = "fr") -> Optional[Dict]:
    """
    Récupère une attaque par son nom FR/EN (insensible à la casse).
    Returns un dict normalisé (avec clé 'name') ou None si introuvable.
    """
    key = "name_fr" if language == "fr" else "name_en"
    target = (move_name or "").strip().lower()
    if not target:
        return None
    for move in load_moves_data():
        if (move.get(key, "") or "").lower() == target:
            return _normalize_move_record(move, language=language)
    # Fallback : si on cherche FR mais fourni EN (ou inversement)
    other = "name_en" if key == "name_fr" else "name_fr"
    for move in load_moves_data():
        if (move.get(other, "") or "").lower() == target:
            return _normalize_move_record(move, language=language)
    return None


def get_move_data(move_name: str) -> Optional[Dict]:
    """
    Alias pour récupérer une attaque en français (compatibilité).
    """
    return get_move_by_name(move_name, language="fr")


def get_move_description(move_name: str, language: str = "fr") -> Optional[str]:
    """Retourne la description localisée d'une attaque."""
    move = get_move_by_name(move_name, language=language)
    return move.get("description") if move else None


def get_move_power(move_name: str, language: str = "fr") -> Optional[int]:
    move = get_move_by_name(move_name, language=language)
    return move.get("power") if move else None


def get_move_accuracy(move_name: str, language: str = "fr") -> Optional[int]:
    move = get_move_by_name(move_name, language=language)
    return move.get("accuracy") if move else None
