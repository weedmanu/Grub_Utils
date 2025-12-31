"""Module pour l'onglet des paramètres généraux."""

from src.ui.gtk_init import Gtk
from src.ui.tabs.base import BaseTab


class GeneralTab(BaseTab):
    """Classe pour l'onglet des paramètres généraux."""

    def __init__(self, app):
        """Initialise l'onglet avec une référence à l'application."""
        super().__init__(app)

        # Default Entry
        self.grid.attach(Gtk.Label(label="Entrée par défaut :", xalign=0), 0, 0, 1, 1)
        flat_entries = self._get_flat_menu_entries()
        self.entry_ids = ["0", "saved"] + [str(i) for i in range(len(flat_entries))]
        self.entry_labels = [
            "Première entrée (0)",
            "Dernière utilisée (saved)",
        ] + flat_entries
        self.default_dropdown = Gtk.DropDown.new_from_strings(self.entry_labels)
        self.default_dropdown.set_tooltip_text(
            "Sélectionnez l'entrée de menu qui sera démarrée par défaut au lancement de GRUB."
        )
        curr = self.app.facade.entries.get("GRUB_DEFAULT", "0")
        self.default_dropdown.set_selected(
            self.entry_ids.index(curr) if curr in self.entry_ids else 0
        )
        self.grid.attach(self.default_dropdown, 1, 0, 1, 1)

        # Timeout
        self.grid.attach(Gtk.Label(label="Délai (sec) :", xalign=0), 0, 1, 1, 1)
        self.timeout_entry = Gtk.Entry(text=self.app.facade.entries.get("GRUB_TIMEOUT", "5"))
        self.timeout_entry.set_tooltip_text(
            "Temps d'attente en secondes avant de démarrer l'entrée par défaut. 0 = démarrage immédiat."
        )
        self.grid.attach(self.timeout_entry, 1, 1, 1, 1)

        # Kernel params
        self.grid.attach(Gtk.Label(label="Paramètres noyau :", xalign=0), 0, 2, 1, 1)
        self._setup_kernel_dropdown()

    def _setup_kernel_dropdown(self) -> None:
        """Configure le menu déroulant des paramètres noyau."""
        self.kernel_options = [
            "quiet splash",
            "quiet",
            "",
            "nomodeset",
            "quiet splash nomodeset",
        ]
        self.kernel_descriptions = {
            "quiet splash": "Démarrage silencieux avec logo graphique (recommandé).",
            "quiet": "Démarrage silencieux sans logo (écran noir).",
            "": "Mode verbeux : affiche tous les messages techniques du noyau.",
            "nomodeset": "Désactive les pilotes graphiques avancés (utile si l'écran reste noir).",
            "quiet splash nomodeset": "Silencieux avec logo et pilotes graphiques de base.",
        }
        curr = self.app.facade.entries.get("GRUB_CMDLINE_LINUX_DEFAULT", "quiet splash")
        if curr not in self.kernel_options:
            self.kernel_options.append(curr)

        display_opts = [opt if opt else "(aucun)" for opt in self.kernel_options]
        self.kernel_dropdown = Gtk.DropDown.new_from_strings(display_opts)
        self.kernel_dropdown.set_tooltip_text(
            "Paramètres passés au noyau Linux au démarrage. "
            "'quiet splash' est recommandé pour la plupart des utilisateurs."
        )
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self.on_dropdown_setup)
        factory.connect("bind", self.on_dropdown_bind)
        self.kernel_dropdown.set_list_factory(factory)
        self.kernel_dropdown.connect("notify::selected", self.update_dropdown_tooltip)
        self.kernel_dropdown.set_selected(
            self.kernel_options.index(curr) if curr in self.kernel_options else 0
        )
        self.update_dropdown_tooltip(self.kernel_dropdown, None)
        self.grid.attach(self.kernel_dropdown, 1, 2, 1, 1)

    def _get_flat_menu_entries(self):
        """Get flat list of menu entry titles.

        Returns:
            List of menu entry titles

        """
        return [entry["title"] for entry in self.app.facade.menu_entries]

    def on_dropdown_setup(self, _factory, list_item):
        """Configure l'élément de liste du menu déroulant."""
        label = Gtk.Label(xalign=0)
        for margin in ["start", "end"]:
            getattr(label, f"set_margin_{margin}")(10)
        for margin in ["top", "bottom"]:
            getattr(label, f"set_margin_{margin}")(5)
        list_item.set_child(label)

    def on_dropdown_bind(self, _factory, list_item):
        """Lie les données à l'élément de liste du menu déroulant."""
        string_obj = list_item.get_item()
        label = list_item.get_child()
        text = string_obj.get_string()
        label.set_text(text)
        orig_text = text if text != "(aucun)" else ""
        label.set_tooltip_text(self.kernel_descriptions.get(orig_text, "Paramètres personnalisés"))

    def update_dropdown_tooltip(self, dropdown, _pspec):
        """Met à jour la bulle d'aide du menu déroulant."""
        idx = dropdown.get_selected()
        if 0 <= idx < len(self.kernel_options):
            opt = self.kernel_options[idx]
            dropdown.set_tooltip_text(self.kernel_descriptions.get(opt, "Paramètres personnalisés"))

    def get_config(self) -> dict[str, str]:
        """Récupère la configuration de l'onglet.

        Returns:
            dict[str, str]: Configuration modifiée

        """
        config = {}
        
        if self.default_dropdown:
            selected_idx = self.default_dropdown.get_selected()
            if selected_idx < len(self.entry_ids):
                config["GRUB_DEFAULT"] = self.entry_ids[selected_idx]

        if self.timeout_entry:
            config["GRUB_TIMEOUT"] = self.timeout_entry.get_text()

        if self.kernel_dropdown:
            selected_idx = self.kernel_dropdown.get_selected()
            if selected_idx < len(self.kernel_options):
                config["GRUB_CMDLINE_LINUX_DEFAULT"] = self.kernel_options[selected_idx]

        return config
