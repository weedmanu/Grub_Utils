"""Dialog d'erreur avec détails techniques."""

from typing import Optional

import gi
from gi.repository import Gtk

from src.utils.config import DIALOG_HEIGHT, DIALOG_WIDTH

gi.require_version("Gtk", "4.0")


class ErrorDialog(Gtk.AlertDialog):
    """Dialog d'erreur avec option pour afficher les détails techniques."""

    # pylint: disable=no-member

    def __init__(
        self,
        _parent: Gtk.Window,
        title: str,
        message: str,
        details: Optional[str] = None,
    ):
        """
        Initialise le dialog d'erreur.

        Args:
            parent: Fenêtre parente
            title: Titre du dialog
            message: Message d'erreur principal
            details: Détails techniques optionnels
        """
        super().__init__()
        self.set_modal(True)
        self.set_message(title)
        self.set_detail(message)

        if details:
            # Ajouter un bouton pour afficher les détails
            self.add_response("details", "Détails techniques")
            self.add_response("ok", "OK")
            self.set_default_response("ok")
            self.connect("response", self._on_response, details)
        else:
            self.add_response("ok", "OK")
            self.set_default_response("ok")

    def _on_response(self, _dialog, response, details):
        """Gère la réponse du dialog."""
        if response == "details":
            self._show_details(details)

    def _show_details(self, details: str):
        """Affiche les détails techniques dans un dialog séparé."""
        details_dialog = Gtk.Window(title="Détails techniques")
        details_dialog.set_default_size(DIALOG_WIDTH, DIALOG_HEIGHT)
        details_dialog.set_modal(True)

        scrolled = Gtk.ScrolledWindow()
        text_view = Gtk.TextView()
        text_view.set_editable(False)
        text_view.set_monospace(True)
        text_view.get_buffer().set_text(details)
        scrolled.set_child(text_view)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(scrolled)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(10)
        button_box.set_margin_bottom(10)
        button_box.set_margin_start(10)
        button_box.set_margin_end(10)

        close_btn = Gtk.Button(label="Fermer")
        close_btn.connect("clicked", lambda _: details_dialog.destroy())
        button_box.append(close_btn)

        box.append(button_box)
        details_dialog.set_child(box)
        details_dialog.present()
