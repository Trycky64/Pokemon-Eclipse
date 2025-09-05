# battle/move_effects.py
# -*- coding: utf-8 -*-

"""
Application des effets d'attaque : altérations de statut, buffs/debuffs, effets spéciaux.
Les données viennent du move (ailment/effect/effect_chance/priority/target...).
On reste volontairement générique & tolérant.
"""

from typing import Dict, List
import random

# Liste de stat stages gérés (tu peux étendre : accuracy, evasion, etc.)
STAT_KEYS = {
    "attack": "atk_stage",
    "defense": "def_stage",
    "sp_attack": "spa_stage",
    "sp_defense": "spd_stage",
    "speed": "spe_stage",
}

def _init_stages(pokemon: Dict):
    for k in STAT_KEYS.values():
        pokemon.setdefault(k, 0)

def _apply_stage(pokemon: Dict, key: str, delta: int) -> int:
    """Applique un delta de stage entre -6..+6, retourne la nouvelle valeur."""
    _init_stages(pokemon)
    k = STAT_KEYS.get(key)
    if not k:
        return 0
    cur = int(pokemon.get(k, 0))
    cur = max(-6, min(6, cur + int(delta)))
    pokemon[k] = cur
    return cur

def _stage_multiplier(stage: int) -> float:
    """Mult pour convertir stage en facteur (simplifié 2+n / 2-n)."""
    if stage >= 0:
        return (2 + stage) / 2
    return 2 / (2 + abs(stage))

def derived_stats_from_stages(pokemon: Dict):
    """
    Recalcule les stats dérivées d'affichage/usage à partir des stages.
    À appeler après buffs/debuffs si tu veux refléter immédiatement.
    """
    base = pokemon.get("stats", {})
    result = {}
    for key, st_key in STAT_KEYS.items():
        stage = int(pokemon.get(st_key, 0))
        mult = _stage_multiplier(stage)
        result[key] = int(max(1, (base.get(key, 10)) * mult))
    return result

def try_apply_status(target: Dict, ailment: str, rng: random.Random, chance: int = None) -> bool:
    """
    Applique un statut si possible : "paralysis", "burn", "poison", "sleep", "freeze".
    On respecte l'éventuelle chance d'effet (effect_chance).
    """
    if not ailment or ailment == "none":
        return False
    if chance is not None:
        if rng.randint(1, 100) > int(chance):
            return False
    if target.get("status", "none") != "none":
        return False  # déjà affecté
    target["status"] = ailment
    return True

def apply_move_effects(attacker: Dict, defender: Dict, move: Dict, rng: random.Random = None) -> List[str]:
    """
    Applique les effets non-dégâts décrits par 'move'.
    Retourne une liste de messages (FR) décrivant ce qui s'est passé.
    Supporte :
      - move["ailment"] + move["effect_chance"]
      - move["effects"] : { "target": {"attack": -1, "defense": +2}, "self": {...} }
    """
    if rng is None:
        rng = random.Random()

    messages = []

    # 1) Statut (ex: "paralysis")
    ailment = (move.get("ailment") or "none").lower()
    eff_chance = move.get("effect_chance", None)
    if try_apply_status(defender, ailment, rng, eff_chance):
        messages.append(f"{defender.get('name','Le Pokémon')} est affecté par {ailment} !")

    # 2) Buffs/debuffs
    effs = move.get("effects") or {}
    for scope, deltas in effs.items():
        target = attacker if scope == "self" else defender
        if not isinstance(deltas, dict):
            continue
        for stat_key, delta in deltas.items():
            new_stage = _apply_stage(target, stat_key, int(delta))
            who = "Votre Pokémon" if target is attacker else "Le Pokémon ennemi"
            sign = "augmente" if delta > 0 else "baisse"
            messages.append(f"{who} voit son {stat_key} {sign} (palier {new_stage}).")

    return messages
