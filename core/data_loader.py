# core/data_loader.py
# -*- coding: utf-8 -*-
"""
Utilitaires d'E/S pour les fichiers JSON et la gestion de chemins.
"""
from __future__ import annotations
import json
import os
from typing import Any

def load_json(path: str) -> Any:
    """
    Charge un fichier JSON en UTF-8. Retourne l'objet Python (dict/list).
    Lève une exception claire si le fichier est introuvable ou invalide.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: str, data: Any, indent: int = 2) -> None:
    """
    Sauvegarde un objet Python vers un JSON UTF-8 lisible.
    Crée les dossiers parents si nécessaires.
    """
    ensure_dir(os.path.dirname(path) or ".")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)

def ensure_dir(path: str) -> None:
    """
    Crée le dossier s'il n'existe pas (idempotent).
    """
    if path:
        os.makedirs(path, exist_ok=True)

def file_exists(path: str) -> bool:
    """
    True si le fichier existe.
    """
    return os.path.exists(path)
