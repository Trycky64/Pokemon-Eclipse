# battle/use_item.py
# -*- coding: utf-8 -*-

"""
Pont d'utilisation d'objet en combat.
Distingue automatiquement : ball de capture (capture_handler) vs objet de soin/statut (item_handler).
"""

from typing import Dict
from battle.item_handler import use_item_on_pokemon
from battle.capture_handler import attempt_capture

BALLS = {"Poké Ball", "Super Ball", "Hyper Ball", "Master Ball"}

def use_item(context: Dict) -> Dict:
    """
    context attendu:
      {
        "item": {"name": str, "quantity": int},
        "user": Dict (celui qui utilise),
        "target": Dict (cible),
        "is_capture": bool (optionnel, sinon déduit par BALLS)
      }
    Retour:
      { "success": bool, "messages": [str], "capture": Optional[Dict] }
    """
    item = context.get("item", {})
    name = item.get("name", "")
    target = context.get("target")

    if not name or not target:
        return {"success": False, "messages": ["Objet ou cible invalide."]}

    if context.get("is_capture", name in BALLS):
        # Capture sur la cible (ennemie)
        res = attempt_capture(target, name)
        return {"success": res["success"], "messages": res["messages"], "capture": res}

    # Objet de soin/statut sur la cible (alliée)
    res = use_item_on_pokemon(name, target)
    return {"success": res["success"], "messages": res["messages"]}
