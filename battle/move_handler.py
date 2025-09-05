# battle/move_handler.py
# -*- coding: utf-8 -*-

"""
Exécution d'une attaque : vérif PP, précision, dégâts, critique, efficacité, effets annexes.
Retourne un dictionnaire structuré pour l'UI (messages, flags, valeurs).
"""

from typing import Dict, List
import random

from battle.engine import calculate_damage
from battle.move_utils import has_pp, consume_pp, accuracy_check, is_status_move
from battle.move_effects import apply_move_effects, derived_stats_from_stages

def execute_move(attacker: Dict, defender: Dict, move: Dict, rng: random.Random = None) -> Dict:
    """
    Exécute une attaque 'move' du lanceur 'attacker' sur 'defender'.
    Modifie in-place certaines valeurs (HP, statuts, stages).
    Retour:
      {
        "used": bool, "hit": bool, "messages": [str],
        "damage": int, "crit": bool, "eff": float,
        "defender_hp_before": int, "defender_hp_after": int
      }
    """
    if rng is None:
        rng = random.Random()

    result = {
        "used": False, "hit": False, "messages": [],
        "damage": 0, "crit": False, "eff": 1.0,
        "defender_hp_before": int(defender.get("hp", 1)),
        "defender_hp_after": int(defender.get("hp", 1)),
    }

    name = move.get("name") or "Attaque"
    # PP
    if not has_pp(move):
        result["messages"].append(f"{attacker.get('name','Votre Pokémon')} ne peut pas lancer {name} (PP) !")
        return result

    # Consomme le PP maintenant (comme les jeux GBA)
    consume_pp(move, 1)
    result["used"] = True

    # Statut/Stat-only ?
    if is_status_move(move):
        # Effets non-dégâts
        msgs = apply_move_effects(attacker, defender, move, rng)
        result["messages"].append(f"{attacker.get('name','Votre Pokémon')} utilise {name} !")
        result["messages"].extend(msgs)
        # Recalcule dérivés si besoin
        attacker["derived_stats"] = derived_stats_from_stages(attacker)
        defender["derived_stats"] = derived_stats_from_stages(defender)
        return result

    # Précision
    if not accuracy_check(attacker, defender, move, rng):
        result["messages"].append(f"{attacker.get('name','Votre Pokémon')} utilise {name}… mais l'attaque échoue !")
        return result

    # Dégâts
    calc = calculate_damage(attacker, defender, move, rng)
    dmg = max(1, int(calc["damage"]))
    result["hit"] = True
    result["damage"] = dmg
    result["crit"] = bool(calc["crit"])
    result["eff"] = float(calc["eff"])

    defender["hp"] = max(0, int(defender.get("hp", 1)) - dmg)

    # Messages
    result["messages"].append(f"{attacker.get('name','Votre Pokémon')} utilise {name} !")
    if calc["crit"]:
        result["messages"].append("Coup critique !")
    if calc["eff"] > 1.0:
        result["messages"].append("C'est super efficace !")
    elif 0 < calc["eff"] < 1.0:
        result["messages"].append("Ce n'est pas très efficace…")

    # Effets additionnels
    result["messages"].extend(apply_move_effects(attacker, defender, move, rng))

    # Statistiques dérivées après effets
    attacker["derived_stats"] = derived_stats_from_stages(attacker)
    defender["derived_stats"] = derived_stats_from_stages(defender)

    result["defender_hp_after"] = int(defender["hp"])
    return result
