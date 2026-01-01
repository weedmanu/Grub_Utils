"""Enums pour les actions de l'interface utilisateur."""

from enum import Enum, auto


class ActionType(Enum):
    """Types d'actions disponibles dans la barre d'outils."""

    SAVE = auto()
    DEFAULT = auto()
    PREVIEW = auto()
    RESTORE = auto()
    DELETE = auto()
