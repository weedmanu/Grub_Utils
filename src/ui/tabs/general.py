"""Module pour l'onglet des paramètres généraux."""

import gi
from gi.repository import Gtk

from src.ui.tabs.base import BaseTab

gi.require_version("Gtk", "4.0")


class GeneralTab(BaseTab):
    """Classe pour l'onglet des paramètres généraux."""

    def __init__(self, app):
        """Initialise l'onglet avec une référence à l'application."""
        super().__init__(app)

        # Default Entry
        self.grid.attach(Gtk.Label(label="Entrée par défaut :", xalign=0), 0, 0, 1, 1)
        flat_entries = self.app.manager.get_flat_menu_entries()
        self.app.widgets.entry_ids = ["0", "saved"] + [str(i) for i in range(len(flat_entries))]
        self.app.widgets.entry_labels = [
            "Première entrée (0)",
            "Dernière utilisée (saved)",
        ] + flat_entries
        self.app.widgets.default_dropdown = Gtk.DropDown.new_from_strings(self.app.widgets.entry_labels)
        self.app.widgets.default_dropdown.set_tooltip_text(
            "Sélectionnez l'entrée de menu qui sera démarrée par défaut au lancement de GRUB."
        )
        curr = self.app.manager.entries.get("GRUB_DEFAULT", "0")
        self.app.widgets.default_dropdown.set_selected(
            self.app.widgets.entry_ids.index(curr) if curr in self.app.widgets.entry_ids else 0
        )
        self.grid.attach(self.app.widgets.default_dropdown, 1, 0, 1, 1)

        # Timeout
        self.grid.attach(Gtk.Label(label="Délai (sec) :", xalign=0), 0, 1, 1, 1)
        self.app.widgets.timeout_entry = Gtk.Entry(text=self.app.manager.entries.get("GRUB_TIMEOUT", "5"))
        self.app.widgets.timeout_entry.set_tooltip_text(
            "Temps d'attente en secondes avant de démarrer l'entrée par défaut. 0 = démarrage immédiat."
        )
        self.grid.attach(self.app.widgets.timeout_entry, 1, 1, 1, 1)

        # Kernel params
        self.grid.attach(Gtk.Label(label="Paramètres noyau :", xalign=0), 0, 2, 1, 1)
        self._setup_kernel_dropdown(self.grid)

    def _setup_kernel_dropdown(self, grid):
        """Configure le menu déroulant des paramètres noyau."""
        self.app.widgets.kernel_options = [
            "quiet splash",
            "quiet",
            "",
            "nomodeset",
            "quiet splash nomodeset",
        ]
        self.app.widgets.kernel_descriptions = {
            "quiet splash": "Démarrage silencieux avec logo graphique (recommandé).",
            "quiet": "Démarrage silencieux sans logo (écran noir).",
            "": "Mode verbeux : affiche tous les messages techniques du noyau.",
            "nomodeset": "Désactive les pilotes graphiques avancés (utile si l'écran reste noir).",
            "quiet splash nomodeset": "Silencieux avec logo et pilotes graphiques de base.",
        }
        curr = self.app.manager.entries.get("GRUB_CMDLINE_LINUX_DEFAULT", "quiet splash")
        if curr not in self.app.widgets.kernel_options:
            self.app.widgets.kernel_options.append(curr)

        display_opts = [opt if opt else "(aucun)" for opt in self.app.widgets.kernel_options]
        self.app.widgets.kernel_dropdown = Gtk.DropDown.new_from_strings(display_opts)
        self.app.widgets.kernel_dropdown.set_tooltip_text(
            "Paramètres passés au noyau Linux au démarrage. "
            "'quiet splash' est recommandé pour la plupart des utilisateurs."
        )
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self.app.on_dropdown_setup)
        factory.connect("bind", self.app.on_dropdown_bind)
        self.app.widgets.kernel_dropdown.set_list_factory(factory)
        self.app.widgets.kernel_dropdown.connect("notify::selected", self.app.update_dropdown_tooltip)
        self.app.widgets.kernel_dropdown.set_selected(
            self.app.widgets.kernel_options.index(curr) if curr in self.app.widgets.kernel_options else 0
        )
        self.app.update_dropdown_tooltip(self.app.kernel_dropdown, None)
        self.grid.attach(self.app.kernel_dropdown, 1, 2, 1, 1)
        grid.attach(self.app.kernel_dropdown, 1, 2, 1, 1)
