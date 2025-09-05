# battle/item_handler.py
# -*- coding: utf-8 -*-

"""
Gestion des objets (hors ball de capture qui relève de capture_handler).
Implémente : Potion, Super Potion, Hyper Potion, Antidote, Anti-Brûle, Antiparalysie, Réveil, Antigel.
"""

from typing import Dict

HEALS = {
    "Potion": 20,
    "Super Potion": 50,
    "Hyper Potion": 200,
}

CURES = {
    "Antidote": "poison",
    "Anti-Brûle": "burn",
    "Antiparalysie": "paralysis",
    "Réveil": "sleep",
    "Antigel": "freeze",
}

def heal_pokemon(pokemon: Dict, amount: int) -> int:
    """Soigne et retourne les PV réellement rendus."""
    max_hp = int(pokemon.get("stats", {}).get("hp", pokemon.get("max_hp", 1)))
    cur_hp = int(pokemon.get("hp", max_hp))
    new_hp = min(max_hp, cur_hp + int(amount))
    delta = new_hp - cur_hp
    pokemon["hp"] = new_hp
    return delta

def cure_status(pokemon: Dict, status: str) -> bool:
    if pokemon.get("status", "none") == status:
        pokemon["status"] = "none"
        return True
    return False

def use_item_on_pokemon(item_name: str, pokemon: Dict) -> Dict:
    """
    Utilise un objet (hors ball) sur un Pokémon.
    Retour: { "success": bool, "messages": [str] }
    """
    if item_name in HEALS:
        healed = heal_pokemon(pokemon, HEALS[item_name])
        if healed > 0:
            return {"success": True, "messages": [f"{pokemon.get('name','Votre Pokémon')} récupère {healed} PV !"]}
        return {"success": False, "messages": ["Cela n'a eu aucun effet…"]}

    if item_name in CURES:
        ok = cure_status(pokemon, CURES[item_name])
        if ok:
            return {"success": True, "messages": [f"Le statut de {pokemon.get('name','Votre Pokémon')} est guéri !"]}
        return {"success": False, "messages": ["Cela n'a eu aucun effet…"]}

    return {"success": False, "messages": ["Objet inconnu ou non utilisable ici."]}
