"""Dialog d'erreur avec détails techniques."""

from dataclasses import dataclass

from src.ui.dialogs.base_dialog import BaseDialog
from src.ui.dialogs.text_view_utils import create_monospace_text_view
from src.ui.gtk_init import Gtk


@dataclass
class ErrorOptions:
    """Configuration options for error dialog."""

    title: str
    message: str
    details: str | None = None


class ErrorDialog(BaseDialog):
    """Dialog d'erreur avec option pour afficher les détails techniques."""

    def __init__(
        self,
        parent: Gtk.Window,
        options: ErrorOptions,
    ) -> None:
        """Initialise le dialog d'erreur.

        Args:
            parent: Fenêtre parente
            options: Error dialog configuration options

        """
        super().__init__(parent, options.title, (500, 250))

        main_box = self.create_main_box()

        # Message principal
        label = self.create_message_label(options.message)
        main_box.append(label)

        # Détails si présents
        if options.details:
            expander = Gtk.Expander(label="Détails techniques")
            details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

            scrolled = Gtk.ScrolledWindow()
            scrolled.set_vexpand(True)

            text_view = create_monospace_text_view(editable=False)
            text_view.get_buffer().set_text(options.details)

            scrolled.set_child(text_view)
            details_box.append(scrolled)

            expander.set_child(details_box)
            main_box.append(expander)

        # Boutons
        button_box = self.create_button_box()

        close_btn = Gtk.Button(label="Fermer")
        close_btn.get_style_context().add_class("suggested-action")
        close_btn.connect("clicked", lambda _: self.close())

        button_box.append(close_btn)
        main_box.append(button_box)

        self.finalize_dialog(main_box)
