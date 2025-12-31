"""Module pour l'onglet de gestion du menu."""

import gi
from gi.repository import Gtk

from src.ui.tabs.base import BaseTab

gi.require_version("Gtk", "4.0")


class MenuTab(BaseTab):
    """Classe pour l'onglet de gestion du menu."""

    def __init__(self, app):
        """Initialise l'onglet avec une référence à l'application."""
        super().__init__(app)

        scrolled = Gtk.ScrolledWindow(vexpand=True)
        self.app.widgets.menu_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        scrolled.set_child(self.app.widgets.menu_list)
        self.append(scrolled)

        self.app.widgets.check_buttons = {}
        self._render_menu_level(self.app.manager.menu_entries, self.app.widgets.menu_list)

    def _render_menu_level(self, items, container):
        """Rendu récursif des entrées et sous-menus."""
        for item in items:
            if item["type"] == "entry":
                name = item["name"]
                check = Gtk.CheckButton(label=name, active=name not in self.app.manager.hidden_entries)
                container.append(check)
                self.app.widgets.check_buttons[name] = check
            elif item["type"] == "submenu":
                expander = Gtk.Expander(label=item["name"])
                expander.set_margin_start(10)
                sub_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
                sub_box.set_margin_start(20)
                expander.set_child(sub_box)
                container.append(expander)
                self._render_menu_level(item["entries"], sub_box)
