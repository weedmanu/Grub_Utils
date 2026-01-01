"""État de l'application pour regrouper les attributs d'interface."""

from dataclasses import dataclass, field

from src.ui.gtk_init import Gtk


# pylint: disable=too-many-instance-attributes
@dataclass
class AppUIState:
    """État des composants UI de l'application."""

    # Fenêtre principale
    win: Gtk.Window | None = None
    overlay: Gtk.Overlay | None = None

    # Onglets
    tabs: dict[str, Gtk.Widget] = field(default_factory=dict)

    # Composants de toast
    toast_revealer: Gtk.Revealer | None = None
    toast_label: Gtk.Label | None = None

    # Boutons d'action
    preview_btn: Gtk.Button | None = None
    default_btn: Gtk.Button | None = None
    save_btn: Gtk.Button | None = None
    restore_btn: Gtk.Button | None = None
    delete_btn: Gtk.Button | None = None
