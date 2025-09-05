# battle/ai.py
# -*- coding: utf-8 -*-

"""
IA simple pour le choix de l'action ennemie.
Stratégie :
 - si PV bas et objet de soin dispo → soigner (skill >= 2)
 - sinon choisir l'attaque la plus prometteuse (power * efficacité * STAB)
 - sinon aléatoire de secours
"""

import random
from typing import Dict, List
from battle.engine import calculate_damage

class BattleAI:
    """
    Intelligence artificielle de combat basique.
    skill_level:
      0 = random safe
      1 = préfère power/efficacité
      2 = gère soin simple si PV bas
    """
    def __init__(self, skill_level: int = 1, rng: random.Random = None):
        self.skill_level = int(skill_level)
        self.rng = rng or random.Random()

    def choose_action(self, enemy: Dict, target: Dict) -> Dict:
        """
        Choisit une action :
          return {"type": "move", "index": i} ou {"type": "item", "item": "Potion"}
        """
        moves: List[Dict] = enemy.get("moves", [])
        hp = int(enemy.get("hp", 1))
        max_hp = int(enemy.get("stats", {}).get("hp", hp))

        # Soins si HP < 30% et skill >= 2
        if self.skill_level >= 2 and hp < 0.3 * max_hp:
            bag = enemy.get("bag", [])
            for it in bag:
                if it.get("name") in ("Potion", "Super Potion", "Hyper Potion") and it.get("quantity", 0) > 0:
                    return {"type": "item", "item": it["name"]}

        # Choix de move
        if not moves:
            return {"type": "skip"}

        scored = []
        for i, mv in enumerate(moves):
            power = int(mv.get("power", 0) or 0)
            if power <= 0 and self.skill_level >= 1:
                # évite les status-only si d'autres choix existent
                continue
            calc = calculate_damage(enemy, target, mv, self.rng)
            score = calc["damage"]
            # bonus efficacité/STAB
            score *= (1.25 if calc["eff"] > 1.0 else 1.0)
            score *= (1.15 if calc["eff"] >= 2.0 else 1.0)
            score *= (1.10 if calc["eff"] == 0.5 else 1.0)  # léger ajustement
            score *= (1.10 if calc["stab"] > 1.0 else 1.0)
            scored.append((score, i))

        if not scored:
            # tous status-only ou indisponibles → random
            idx = self.rng.randrange(len(moves))
            return {"type": "move", "index": idx}

        scored.sort(reverse=True)
        best_idx = scored[0][1]
        return {"type": "move", "index": best_idx}
