"""Dialog de confirmation pour les actions critiques."""

from collections.abc import Callable
from dataclasses import dataclass

from src.ui.dialogs.base_dialog import BaseDialog
from src.ui.gtk_init import Gtk


@dataclass(frozen=True)
class ConfirmOptions:
    """Configuration options for confirmation dialog."""

    title: str
    message: str
    allow_dont_ask: bool = True


class ConfirmDialog(BaseDialog):
    """Custom confirmation dialog for critical actions."""

    def __init__(
        self,
        parent: Gtk.Window,
        callback: Callable[[bool], None],
        options: ConfirmOptions,
    ) -> None:
        """Initialize confirmation dialog.

        Args:
            parent: Parent window
            callback: Function called with True if confirmed
            options: Dialog configuration options

        """
        super().__init__(parent, options.title, (400, 180))

        self.callback = callback
        self.dont_ask_again = False

        # Main container
        main_box = self.create_main_box()

        # Message
        label = self.create_message_label(options.message)
        main_box.append(label)

        # Optional checkbox
        if options.allow_dont_ask:
            self.dont_ask_check = Gtk.CheckButton(label="Ne plus demander")
            main_box.append(self.dont_ask_check)
        else:
            self.dont_ask_check = None

        # Button container
        button_box = self.create_button_box()

        cancel_btn = Gtk.Button(label="Annuler")
        cancel_btn.connect("clicked", self._on_cancel)

        confirm_btn = Gtk.Button(label="Confirmer")
        confirm_btn.get_style_context().add_class("destructive-action")
        confirm_btn.connect("clicked", self._on_confirm)

        button_box.append(cancel_btn)
        button_box.append(confirm_btn)

        main_box.append(button_box)
        self.set_child(main_box)
        self.present()

    def _on_cancel(self, _button: Gtk.Button) -> None:
        """Handle cancel button."""
        self.callback(False)
        self.close()

    def _on_confirm(self, _button: Gtk.Button) -> None:
        """Handle confirm button."""
        if self.dont_ask_check is not None:
            self.dont_ask_again = self.dont_ask_check.get_active()
        self.callback(True)
        self.close()
