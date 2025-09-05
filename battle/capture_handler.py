# battle/capture_handler.py
# -*- coding: utf-8 -*-

import math
import random
from typing import Dict

# Modificateurs appliqués selon le statut du Pokémon (approx Gen III/IV)
STATUS_MODIFIERS = {
    "sleep": 2.0,
    "freeze": 2.0,
    "paralysis": 1.5,
    "poison": 1.5,
    "burn": 1.5,
    None: 1.0,
    "none": 1.0,
}

# Modificateurs de balls (simplifié, extensible)
BALL_MODIFIERS = {
    "Poké Ball": 1.0,
    "Super Ball": 1.5,
    "Hyper Ball": 2.0,
    "Master Ball": 255.0,  # capture auto (court-circuit)
}


def attempt_capture(pokemon: Dict, ball_name: str = "Poké Ball") -> Dict:
    """
    Renvoie {success: bool, shakes: int (0-3), messages: [str]}
    Implémente une version proche de l'algorithme Gen III/IV.

    Inputs attendus dans 'pokemon' :
      - 'name' (str), 'hp' (int courant)
      - 'stats'['hp'] (max HP) ou 'max_hp'
      - 'capture_rate' (int optionnel, défaut 45)
      - 'status' (str optionnel)
    """
    # Master Ball => succès direct
    if ball_name == "Master Ball":
        return {"success": True, "shakes": 3, "messages": [f"{pokemon.get('name','?')} est capturé !"]}

    # HP & capture_rate
    max_hp = int(pokemon.get("stats", {}).get("hp", pokemon.get("max_hp", pokemon.get("hp", 1))))
    cur_hp = int(pokemon.get("hp", max_hp))
    max_hp = max(1, max_hp)
    cur_hp = max(1, min(cur_hp, max_hp))

    rate = int(pokemon.get("capture_rate", 45))

    # Modifs ball/statut
    ball_mod = float(BALL_MODIFIERS.get(ball_name, 1.0))
    status_mod = float(STATUS_MODIFIERS.get(pokemon.get("status", "none"), 1.0))

    # Formule "a"
    a_base = ((3 * max_hp - 2 * cur_hp) * rate * ball_mod) / (3 * max_hp)
    a = int(math.floor(a_base * status_mod))
    a = max(1, min(a, 255))

    if a >= 255:
        return {"success": True, "shakes": 3, "messages": [f"{pokemon.get('name','?')} est capturé !"]}

    # Wobble checks
    b = 1048560 / math.sqrt(math.sqrt((16711680 / a)))
    shakes = 0
    for _ in range(4):  # 4 checks en interne => 3 secousses visibles + capture
        if random.uniform(0, 65535) < b:
            shakes += 1
        else:
            break

    success = shakes >= 4 or shakes == 3  # 3 wobble + clic => OK visuellement ici
    msg = f"{pokemon.get('name','?')} est capturé !" if success else f"{pokemon.get('name','?')} s'est échappé !"

    return {"success": success, "shakes": min(shakes, 3), "messages": [msg]}
