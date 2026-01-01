"""Module pour l'onglet de gestion du menu."""

from src.ui.gtk_init import Gtk
from src.ui.tabs.base import BaseTab


class MenuTab(BaseTab):
    """Classe pour l'onglet de gestion du menu."""

    def __init__(self, app):
        """Initialise l'onglet avec une référence à l'application."""
        super().__init__(app)

        scrolled = Gtk.ScrolledWindow(vexpand=True)
        self.menu_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        scrolled.set_child(self.menu_list)
        self.append(scrolled)

        self.check_buttons = {}
        self._render_menu_level(self.app.facade.menu_entries, self.menu_list)

    def restore_defaults(self):
        """Restaure les valeurs par défaut (tout afficher)."""
        # Mettre à jour la façade immédiatement
        self.app.facade.hidden_entries = []

        # Mettre à jour l'interface
        for check in self.check_buttons.values():
            check.set_active(True)
        self.app.show_toast("Toutes les entrées sont affichées")

    def _render_menu_level(self, items, container):
        """Rendu récursif des entrées et sous-menus.

        Args:
            items: Liste des entrées de menu
            container: Conteneur GTK pour afficher les entrées

        """
        for item in items:
            title = item["title"]
            is_submenu = item.get("submenu", False)

            check = Gtk.CheckButton(label=title, active=title not in self.app.facade.hidden_entries)

            # Indenter les sous-menus
            if is_submenu:
                check.set_margin_start(20)

            container.append(check)
            self.check_buttons[title] = check

    def get_hidden_entries(self) -> list[str]:
        """Récupère la liste des entrées cachées.

        Returns:
            list[str]: Liste des titres des entrées cachées

        """
        return [title for title, check in self.check_buttons.items() if not check.get_active()]

    def load_data(self) -> None:
        """Charge les données de configuration dans l'interface."""
        # Mettre à jour l'état des cases à cocher en fonction des entrées cachées
        for title, check in self.check_buttons.items():
            check.set_active(title not in self.app.facade.hidden_entries)

    def reload_menu_entries(self) -> None:
        """Recharge complètement les entrées de menu depuis la configuration.

        Cette méthode reconstruit la liste des entrées après une mise à jour de GRUB.
        """
        # Sauvegarder les entrées cachées actuelles
        current_hidden = self.get_hidden_entries()

        # Vider la liste de menu
        while self.menu_list.get_first_child():
            self.menu_list.remove(self.menu_list.get_first_child())

        # Réinitialiser les check buttons
        self.check_buttons.clear()

        # Recharger les nouvelles entrées de menu
        self._render_menu_level(self.app.facade.menu_entries, self.menu_list)

        # Restaurer l'état caché pour les entrées existantes
        for title in current_hidden:
            if title in self.check_buttons:
                self.check_buttons[title].set_active(False)
