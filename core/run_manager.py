# core/run_manager.py
# -*- coding: utf-8 -*-
"""
Gestion de la "run" courante (équipe du joueur, inventaire, starters, état global).
Singleton accessible via `run_manager`.
"""
from __future__ import annotations
from typing import List, Dict, Optional
from core.data_loader import load_json, file_exists
from data.pokemon_loader import get_pokemon_by_id, get_all_pokemon
from data.items_loader import get_all_items

class RunManager:
    def __init__(self):
        # Équipe du joueur (liste de dicts Pokémon)
        self.team: List[Dict] = []
        # Inventaire ({nom: quantité})
        self.items: Dict[str, int] = {}
        # Catalogue items (nom -> data)
        self.item_data: Dict[str, Dict] = {it["name"]: it for it in get_all_items()} if callable(get_all_items) else {}
        # Starters possibles (liste de dicts)
        self.starters: List[Dict] = []
        # Indique si une partie est active
        self.active: bool = False

        # Précharge starters si dispo
        self._load_starters_if_any()

    # --- Starters --------------------------------------------------------
    def _load_starters_if_any(self, path: str = "data/starters.json") -> None:
        if file_exists(path):
            try:
                data = load_json(path)
                self.starters = data if isinstance(data, list) else []
            except Exception as e:
                print(f"[RunManager] Impossible de lire {path}: {e}")

    # --- Run lifecycle ---------------------------------------------------
    def start_new_run(self, starter: Dict) -> None:
        """
        Démarre une nouvelle run avec un starter (dict Pokémon complet).
        """
        self.team = []
        self.items = {}
        self.active = True
        if starter:
            self.add_pokemon_to_team(starter)

    def end_run(self) -> None:
        """
        Termine la run en cours (réinitialise l'état).
        """
        self.active = False
        self.team.clear()
        self.items.clear()

    # --- Équipe ----------------------------------------------------------
    def add_pokemon_to_team(self, pokemon: Dict) -> bool:
        """
        Ajoute un Pokémon à l'équipe si moins de 6. Retourne True si ajouté.
        """
        if len(self.team) >= 6 or not pokemon:
            return False
        # Normalise quelques champs essentiels
        pokemon.setdefault("name", "???")
        pokemon.setdefault("level", 5)
        pokemon.setdefault("stats", {})
        pokemon.setdefault("hp", int(pokemon.get("stats", {}).get("hp", 20)))
        pokemon.setdefault("status", "none")
        self.team.append(pokemon)
        return True

    def get_active_pokemon(self) -> Optional[Dict]:
        """
        Retourne le Pokémon en tête d'équipe (ou None).
        """
        return self.team[0] if self.team else None

    def remove_fainted(self) -> None:
        """
        Retire les Pokémon K.O. de l'équipe (hp <= 0).
        """
        self.team = [p for p in self.team if int(p.get("hp", 0)) > 0]

    # --- Inventaire ------------------------------------------------------
    @property
    def item_names(self) -> List[str]:
        return list(self.items.keys())

    def add_item(self, item_name: str, quantity: int = 1) -> None:
        """
        Ajoute une quantité d'objet à l'inventaire.
        """
        if not item_name:
            return
        self.items[item_name] = self.items.get(item_name, 0) + max(0, int(quantity))

    def remove_item(self, item_name: str, quantity: int = 1) -> bool:
        """
        Retire une quantité d'objet si disponible. Retourne True si succès.
        """
        if self.items.get(item_name, 0) >= quantity > 0:
            self.items[item_name] -= quantity
            if self.items[item_name] <= 0:
                self.items.pop(item_name, None)
            return True
        return False

    def has_item(self, item_name: str, min_qty: int = 1) -> bool:
        return self.items.get(item_name, 0) >= max(1, min_qty)

    def get_items_as_inventory(self):
        """
        Retourne une liste adaptée à l'UI: [{name, quantity}].
        """
        return [{"name": n, "quantity": q} for n, q in self.items.items()]

# Singleton
run_manager = RunManager()
