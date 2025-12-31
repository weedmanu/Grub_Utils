"""Classe de base pour les onglets de l'application."""

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

    def get_config(self) -> dict[str, str]:
        """Récupère la configuration de l'onglet.

        Returns:
            dict[str, str]: Configuration modifiée

        """
        return {}
