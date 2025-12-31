"""Utilitaires pour la configuration des TextViews."""

from src.ui.gtk_init import Gtk


def create_monospace_text_view(editable: bool = False, cursor_visible: bool = False) -> Gtk.TextView:
    """Create a preconfigured monospace TextView.

    Args:
        editable: Whether the text view is editable (default: False)
        cursor_visible: Whether the cursor is visible (default: False)

    Returns:
        Configured Gtk.TextView instance

    """
    text_view = Gtk.TextView()
    text_view.set_editable(editable)
    text_view.set_monospace(True)
    text_view.set_cursor_visible(cursor_visible)
    return text_view
