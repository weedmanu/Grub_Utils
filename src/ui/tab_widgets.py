"""Gestion centralisée des widgets des onglets."""

from typing import Dict

import gi
from gi.repository import Gtk

gi.require_version("Gtk", "4.0")


class TabWidgets:
    """Classe pour gérer les widgets des différents onglets de manière centralisée."""

    def __init__(self):
        """Initialise le gestionnaire de widgets."""
        # Onglet Général
        self.default_dropdown: Gtk.DropDown = None
        self.entry_ids: list = []
        self.entry_labels: list = []
        self.timeout_entry: Gtk.Entry = None
        self.kernel_dropdown: Gtk.DropDown = None
        self.kernel_options: list = []
        self.kernel_descriptions: Dict[str, str] = {}

        # Onglet Apparence
        self.gfxmode_entry: Gtk.Entry = None
        self.background_entry: Gtk.Entry = None
        self.theme_entry: Gtk.Entry = None

        # Onglet Menu
        self.menu_list: Gtk.Box = None
        self.check_buttons: Dict[str, Gtk.CheckButton] = {}
