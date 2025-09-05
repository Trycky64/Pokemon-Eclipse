# data/items_loader.py
# -*- coding: utf-8 -*-

"""
Charge les objets (items.json) et fournit des utilitaires de lookup.
Contrat :
- Les objets sont stockés dans data/items.json (UTF-8).
- On privilégie l'UI française : les retours incluent toujours un champ 'name' (FR).
- On reste permissif : si certaines clés manquent, on renvoie des valeurs par défaut.

Exemples d'objets attendus dans items.json (extrait) :
[
  {
    "id": 1,
    "name_en": "Potion",
    "name_fr": "Potion",
    "category": "medicine",
    "effect": "heal",
    "amount": 20,
    "description": "Rend 20 PV."
  },
  {
    "id": 2,
    "name_en": "Antidote",
    "name_fr": "Antidote",
    "category": "medicine",
    "effect": "cure",
    "status": "poison",
    "description": "Soigne l'empoisonnement."
  },
  {
    "id": 101,
    "name_en": "Poké Ball",
    "name_fr": "Poké Ball",
    "category": "ball",
    "effect": "capture",
    "description": "Une simple Poké Ball."
  }
]
"""

import json
import os
from functools import lru_cache
from typing import Dict, List, Optional

ITEMS_PATH = os.path.join("data", "items.json")


# ------------------------------- Loading ---------------------------------

@lru_cache(maxsize=1)
def load_items_data() -> List[Dict]:
    """Charge et met en cache tous les objets depuis items.json."""
    with open(ITEMS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("items.json doit contenir une liste d'objets")
    return data


def _normalize_item_record(item: Dict, language: str = "fr") -> Dict:
    """
    Retourne une copie normalisée avec champ 'name' cohérent avec l'UI.
    - language: 'fr' par défaut, sinon 'en'
    - Garantit la présence minimale des clés de base.
    """
    m = dict(item or {})
    name_key = "name_fr" if language == "fr" else "name_en"
    m["name"] = m.get(name_key) or m.get("name_fr") or m.get("name_en") or ""
    m.setdefault("category", "misc")
    m.setdefault("effect", "")
    m.setdefault("description", "")
    # Quantité par défaut pour affichage/inventaire (peut être ignorée par l'UI)
    m.setdefault("amount", item.get("amount") if isinstance(item.get("amount"), int) else None)
    m.setdefault("status", item.get("status") if isinstance(item.get("status"), str) else None)
    return m


# ------------------------------ Queries ----------------------------------

def get_all_items(language: str = "fr") -> List[Dict]:
    """Liste complète d'objets normalisés (champ 'name' conforme UI)."""
    return [_normalize_item_record(it, language=language) for it in load_items_data()]


def get_item_by_name(name: str, language: str = "fr") -> Optional[Dict]:
    """
    Récupère un objet par son nom FR/EN (insensible à la casse).
    Retourne l'item normalisé (avec 'name') ou None.
    """
    if not name:
        return None
    key = "name_fr" if language == "fr" else "name_en"
    target = name.strip().lower()

    # Lookup direct
    for it in load_items_data():
        if (it.get(key, "") or "").lower() == target:
            return _normalize_item_record(it, language=language)

    # Fallback (si mauvais language fourni)
    other = "name_en" if key == "name_fr" else "name_fr"
    for it in load_items_data():
        if (it.get(other, "") or "").lower() == target:
            return _normalize_item_record(it, language=language)
    return None


def get_items_by_category(category: str, language: str = "fr") -> List[Dict]:
    """Retourne tous les objets d'une catégorie (ex: 'medicine', 'ball')."""
    cat = (category or "").strip().lower()
    return [
        _normalize_item_record(it, language=language)
        for it in load_items_data()
        if (it.get("category", "") or "").lower() == cat
    ]


# -------------------------- Helpers gameplay -----------------------------

# Tables utiles pour aligner avec battle/item_handler.py & capture_handler
HEAL_AMOUNTS = {
    "Potion": 20,
    "Super Potion": 50,
    "Hyper Potion": 200,
}

CURE_STATUS = {
    "Antidote": "poison",
    "Anti-Brûle": "burn",
    "Antiparalysie": "paralysis",
    "Réveil": "sleep",
    "Antigel": "freeze",
}

CAPTURE_BALLS = {"Poké Ball", "Super Ball", "Hyper Ball", "Master Ball"}


def is_heal_item(item_name: str) -> bool:
    return item_name in HEAL_AMOUNTS


def is_cure_item(item_name: str) -> bool:
    return item_name in CURE_STATUS


def is_capture_ball(item_name: str) -> bool:
    return item_name in CAPTURE_BALLS


def get_heal_amount(item_name: str) -> int:
    return HEAL_AMOUNTS.get(item_name, 0)


def get_cure_status(item_name: str) -> Optional[str]:
    return CURE_STATUS.get(item_name)
