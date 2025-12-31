"""Dialog d'aperçu des différences avant application."""

import difflib
from typing import Dict, List

import gi
from gi.repository import Gtk

gi.require_version("Gtk", "4.0")


class DiffDialog(Gtk.Window):
    """Dialog affichant l'aperçu des changements de configuration."""

    def __init__(self, parent: Gtk.Window, old_config: Dict[str, str], new_config: Dict[str, str]):
        """
        Initialise le dialog d'aperçu des différences.

        Args:
            parent: Fenêtre parente
            old_config: Ancienne configuration
            new_config: Nouvelle configuration
        """
        super().__init__(title="Aperçu des changements")
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_default_size(700, 500)

        # Calculer les différences
        diff_lines = self._calculate_diff(old_config, new_config)

        # Interface
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)

        # Titre
        title_label = Gtk.Label(label="Changements à appliquer à /etc/default/grub:")
        title_label.set_halign(Gtk.Align.START)
        box.append(title_label)

        # Zone de texte avec différences
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        text_view = Gtk.TextView()
        text_view.set_editable(False)
        text_view.set_monospace(True)

        # Appliquer la coloration syntaxique simple
        buffer = text_view.get_buffer()
        buffer.set_text("".join(diff_lines))

        # Coloration basique (rouge pour suppressions, vert pour ajouts)
        self._apply_syntax_highlighting(buffer, diff_lines)

        scrolled.set_child(text_view)
        box.append(scrolled)

        # Boutons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.END)

        cancel_btn = Gtk.Button(label="Annuler")
        cancel_btn.connect("clicked", lambda _: self.destroy())

        apply_btn = Gtk.Button(label="Appliquer")
        apply_btn.get_style_context().add_class("suggested-action")
        apply_btn.connect("clicked", self._on_apply)

        button_box.append(cancel_btn)
        button_box.append(apply_btn)
        box.append(button_box)

        self.set_child(box)
        self.present()

    def _calculate_diff(self, old_config: Dict[str, str], new_config: Dict[str, str]) -> List[str]:
        """Calculate the differences between configurations."""
        # Convertir en format texte pour diff
        def config_to_lines(config: Dict[str, str]) -> List[str]:
            lines = []
            for key in sorted(config.keys()):
                value = config[key]
                lines.append(f'{key}="{value}"\n')
            return lines

        old_lines = config_to_lines(old_config)
        new_lines = config_to_lines(new_config)

        # Générer le diff
        diff = difflib.unified_diff(old_lines, new_lines, fromfile="Ancien", tofile="Nouveau", lineterm="")

        return list(diff)

    def _apply_syntax_highlighting(self, buffer: Gtk.TextBuffer, diff_lines: List[str]):
        """Applique une coloration syntaxique basique au diff."""
        # Pour une implémentation simple, on pourrait utiliser des tags
        # Mais pour GTK4, c'est plus complexe. Pour l'instant, on laisse tel quel.

    def _on_apply(self, _button):
        """Gère l'application des changements."""
        # Émettre un signal ou appeler un callback
        self.destroy()
        # Implementation will be added in future versions
