"""Dialog de confirmation pour les actions critiques."""

from typing import Callable

import gi
from gi.repository import Gtk

gi.require_version("Gtk", "4.0")


class ConfirmDialog(Gtk.AlertDialog):
    """Dialog de confirmation avec checkbox 'Ne plus demander'."""

    def __init__(
        self,
        parent: Gtk.Window,
        title: str,
        message: str,
        callback: Callable[[bool], None],
        allow_dont_ask: bool = True,
    ):
        """
        Initialise le dialog de confirmation.

        Args:
            parent: Fenêtre parente
            title: Titre du dialog
            message: Message de confirmation
            callback: Fonction appelée avec True si confirmé
            allow_dont_ask: Si True, ajoute la checkbox "Ne plus demander"
        """
        super().__init__()
        self.set_modal(True)
        self.set_message(title)
        self.set_detail(message)

        self.callback = callback
        self.dont_ask_again = False

        self.add_response("cancel", "Annuler")
        self.add_response("confirm", "Confirmer")
        self.set_default_response("cancel")

        if allow_dont_ask:
            # Créer un dialog personnalisé avec checkbox
            self._create_custom_dialog(parent, title, message)
        else:
            self.connect("response", self._on_response)

    def _create_custom_dialog(self, parent: Gtk.Window, title: str, message: str):
        """Crée un dialog personnalisé avec checkbox."""
        dialog = Gtk.Window(title=title)
        dialog.set_modal(True)
        dialog.set_transient_for(parent)
        dialog.set_default_size(400, 150)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        box.set_margin_start(20)
        box.set_margin_end(20)

        # Message
        label = Gtk.Label(label=message)
        label.set_wrap(True)
        box.append(label)

        # Checkbox "Ne plus demander"
        self.dont_ask_check = Gtk.CheckButton(label="Ne plus demander")
        box.append(self.dont_ask_check)

        # Boutons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(10)

        cancel_btn = Gtk.Button(label="Annuler")
        cancel_btn.connect("clicked", lambda _: dialog.destroy())

        confirm_btn = Gtk.Button(label="Confirmer")
        confirm_btn.get_style_context().add_class("destructive-action")
        confirm_btn.connect("clicked", self._on_confirm, dialog)

        button_box.append(cancel_btn)
        button_box.append(confirm_btn)

        box.append(button_box)
        dialog.set_child(box)
        dialog.present()

    def _on_confirm(self, _button, _dialog):
        """Gère la confirmation."""
        self.dont_ask_again = self.dont_ask_check.get_active()
        _dialog.destroy()
        self.callback(True)

    def _on_response(self, _dialog, response):
        """Gère la réponse du dialog standard."""
        if response == "confirm":
            self.callback(True)
