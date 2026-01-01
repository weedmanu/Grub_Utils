"""Classe de base pour les onglets de l'application."""

from src.ui.enums import ActionType
from src.ui.gtk_init import Gtk
from src.utils.config import (
    DEFAULT_MARGIN,
    DEFAULT_SPACING,
    GRID_COLUMN_SPACING,
    GRID_ROW_SPACING,
)


class BaseTab(Gtk.Box):
    """Classe de base pour les onglets avec une grille standard."""

    def __init__(self, app):
        """Initialise l'onglet avec des marges et une grille."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=DEFAULT_SPACING)
        self.app = app
        for margin in ["top", "bottom", "start", "end"]:
            getattr(self, f"set_margin_{margin}")(DEFAULT_MARGIN)

        self.grid = Gtk.Grid(column_spacing=GRID_COLUMN_SPACING, row_spacing=GRID_ROW_SPACING)
        self.append(self.grid)

    def get_available_actions(self) -> set[ActionType]:
        """Retourne les actions disponibles pour cet onglet.

        Par défaut, les onglets de configuration ont Save, Default et Preview.
        """
        return {ActionType.SAVE, ActionType.DEFAULT, ActionType.PREVIEW}

    def can_perform_action(self, _action: ActionType) -> bool:
        """Vérifie si une action peut être exécutée dans l'état actuel.

        Args:
            action: L'action à vérifier

        Returns:
            True si l'action est possible (bouton activé), False sinon (bouton grisé)

        """
        return True

    def on_action(self, action: ActionType) -> bool:
        """Gère une action déclenchée depuis la barre globale.

        Args:
            action: L'action à exécuter

        Returns:
            True si l'action a été gérée, False sinon (pour laisser l'app gérer le défaut)

        """
        if action == ActionType.DEFAULT:
            self.restore_defaults()
            return True
        return False
        # Les autres actions (SAVE, PREVIEW) sont souvent gérées globalement par l'App
        # mais peuvent être surchargées ici si nécessaire.

    def get_config(self) -> dict[str, str]:
        """Récupère la configuration de l'onglet.

        Returns:
            dict[str, str]: Configuration modifiée

        """
        return {}

    def restore_defaults(self) -> None:
        """Restaure les valeurs par défaut de l'onglet."""

    @staticmethod
    def create_info_box() -> Gtk.Box:
        """Crée une Gtk.Box avec les marges standards pour les info frames.

        Returns:
            Gtk.Box: Box configurée avec espacement et marges

        """
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        info_box.set_margin_top(10)
        info_box.set_margin_bottom(10)
        info_box.set_margin_start(10)
        info_box.set_margin_end(10)
        return info_box
