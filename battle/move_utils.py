# battle/engine.py
# -*- coding: utf-8 -*-

"""
Moteur de calculs de combat : dégâts, critique, STAB, efficacité type, etc.
Aucune I/O, pur calcul pour être testable.
"""

from typing import Dict, Tuple
import random

# Tableau d'efficacité simplifié (extrait le plus courant)
# Tu peux l'étendre si besoin. Les types inconnus retombent sur 1.0
TYPE_CHART = {
    ("feu", "plante"): 2.0,
    ("feu", "eau"): 0.5,
    ("eau", "feu"): 2.0,
    ("eau", "plante"): 0.5,
    ("plante", "eau"): 2.0,
    ("plante", "feu"): 0.5,
    ("électrik", "eau"): 2.0,
    ("électrik", "plante"): 0.5,
    ("sol", "électrik"): 2.0,
    # etc. (à compléter si tu as la table complète)
}

def get_types(entity: Dict) -> Tuple[str, str]:
    """Retourne les types (1 ou 2), en minuscule."""
    types = entity.get("types", [])
    a = (types[0] or "").lower() if len(types) >= 1 else ""
    b = (types[1] or "").lower() if len(types) >= 2 else ""
    return a, b

def type_multiplier(move_type: str, defender: Dict) -> float:
    """Produit des multiplicateurs sur 1 ou 2 types."""
    if not move_type:
        return 1.0
    mt = move_type.lower()
    t1, t2 = get_types(defender)
    mult = 1.0
    if t1:
        mult *= TYPE_CHART.get((mt, t1), 1.0)
    if t2:
        mult *= TYPE_CHART.get((mt, t2), 1.0)
    return mult

def stab_multiplier(move_type: str, attacker: Dict) -> float:
    """STAB si le lanceur a le même type que l'attaque."""
    if not move_type:
        return 1.0
    mt = move_type.lower()
    t1, t2 = get_types(attacker)
    return 1.5 if (mt == t1 or mt == t2) else 1.0

def roll_crit(rng: random.Random) -> Tuple[bool, float]:
    """Critique simple (1/24 par défaut GBA-like)."""
    is_crit = rng.random() < (1.0 / 24.0)
    return is_crit, (2.0 if is_crit else 1.0)

def calculate_damage(attacker: Dict, defender: Dict, move: Dict, rng: random.Random = None) -> Dict:
    """
    Calcule les dégâts d'une attaque physique/spéciale simplifiée.
    Attendu:
      attacker["level"], attacker["stats"]["attack"/"sp_attack"]
      defender["stats"]["defense"/"sp_defense"]
      move["power"], move["type"], move["damage_class"] ("physical"/"special")
    Retour:
      { "damage": int, "crit": bool, "eff": float, "stab": float, "roll": float }
    """
    if rng is None:
        rng = random.Random()

    power = int(move.get("power", 0) or 0)
    if power <= 0:
        return {"damage": 0, "crit": False, "eff": 1.0, "stab": 1.0, "roll": 1.0}

    dmg_cls = (move.get("damage_class") or "physical").lower()
    level = max(1, int(attacker.get("level", 1)))
    atk_stat = "attack" if dmg_cls == "physical" else "sp_attack"
    def_stat = "defense" if dmg_cls == "physical" else "sp_defense"

    atk = max(1, int(attacker.get("stats", {}).get(atk_stat, 10)))
    dfc = max(1, int(defender.get("stats", {}).get(def_stat, 10)))

    # Critique
    is_crit, crit_mult = roll_crit(rng)

    # Variance 0.85..1.00
    roll = rng.uniform(0.85, 1.0)

    # STAB + efficacité
    stab = stab_multiplier(move.get("type", ""), attacker)
    eff = type_multiplier(move.get("type", ""), defender)

    # Formule simplifiée proche des GBA
    base = (((2 * level / 5 + 2) * power * atk / dfc) / 50) + 2
    damage = int(base * stab * eff * crit_mult * roll)
    if damage < 1 and power > 0:
        damage = 1

    return {"damage": damage, "crit": is_crit, "eff": eff, "stab": stab, "roll": roll}
