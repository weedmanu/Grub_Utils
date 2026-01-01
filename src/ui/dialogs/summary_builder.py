"""Helper pour créer le résumé des changements de configuration."""

from dataclasses import dataclass

from src.ui.gtk_init import Gtk


@dataclass
class ChangeCounters:
    """Compteurs de changements de configuration."""

    added: int = 0
    removed: int = 0
    modified: int = 0


# pylint: disable=too-few-public-methods
class SummaryBuilder:
    """Construit le résumé visuel des changements de configuration."""

    @staticmethod
    def create_summary_frame(old_config: dict[str, str], new_config: dict[str, str]) -> Gtk.Frame:
        """Crée le frame résumé des changements.

        Args:
            old_config: Configuration actuelle
            new_config: Nouvelle configuration

        Returns:
            Gtk.Frame contenant le résumé

        """
        frame = Gtk.Frame()
        frame.set_label("Modifications de la configuration")
        frame.set_label_align(0.0)

        scrolled = SummaryBuilder._create_scrolled_window()
        summary_box = SummaryBuilder._create_summary_box()

        counters = ChangeCounters()
        all_keys = sorted(set(old_config.keys()) | set(new_config.keys()))

        for key in all_keys:
            SummaryBuilder._add_change_row(summary_box, key, old_config.get(key), new_config.get(key), counters)

        if not summary_box.get_first_child():
            SummaryBuilder._add_no_changes_label(summary_box)

        scrolled.set_child(summary_box)
        frame.set_child(scrolled)
        return frame

    @staticmethod
    def _create_scrolled_window() -> Gtk.ScrolledWindow:
        """Crée la fenêtre scrollable."""
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_max_content_height(150)
        scrolled.set_propagate_natural_height(True)
        return scrolled

    @staticmethod
    def _create_summary_box() -> Gtk.Box:
        """Crée la box principale du résumé."""
        summary_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        summary_box.set_margin_top(10)
        summary_box.set_margin_bottom(10)
        summary_box.set_margin_start(10)
        summary_box.set_margin_end(10)
        return summary_box

    @staticmethod
    def _add_change_row(
        summary_box: Gtk.Box,
        key: str,
        old_value: str | None,
        new_value: str | None,
        counters: ChangeCounters,
    ) -> None:
        """Ajoute une ligne de changement au résumé.

        Args:
            summary_box: Box conteneur
            key: Clé de configuration
            old_value: Ancienne valeur
            new_value: Nouvelle valeur
            counters: Compteurs de changements

        """
        if old_value is None and new_value is not None:
            SummaryBuilder._add_added_row(summary_box, key, new_value)
            counters.added += 1
        elif new_value is None and old_value is not None:
            SummaryBuilder._add_removed_row(summary_box, key, old_value)
            counters.removed += 1
        elif old_value != new_value:
            # Ici on sait que old_value et new_value ne sont pas None grâce aux checks précédents
            # et au fait qu'ils sont différents (donc pas tous les deux None)
            SummaryBuilder._add_modified_row(summary_box, key, str(old_value), str(new_value))
            counters.modified += 1

    @staticmethod
    def _add_added_row(summary_box: Gtk.Box, key: str, value: str) -> None:
        """Ajoute une ligne pour une valeur ajoutée."""
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        icon = Gtk.Label(label="➕")
        row.append(icon)
        label = Gtk.Label(label=f'{key} = "{value}"')
        label.set_halign(Gtk.Align.START)
        label.get_style_context().add_class("success")
        row.append(label)
        summary_box.append(row)

    @staticmethod
    def _add_removed_row(summary_box: Gtk.Box, key: str, old_value: str) -> None:
        """Ajoute une ligne pour une valeur supprimée."""
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        icon = Gtk.Label(label="➖")
        row.append(icon)
        label = Gtk.Label(label=f'{key} (était: "{old_value}")')
        label.set_halign(Gtk.Align.START)
        label.get_style_context().add_class("error")
        row.append(label)
        summary_box.append(row)

    @staticmethod
    def _add_modified_row(summary_box: Gtk.Box, key: str, old_value: str, new_value: str) -> None:
        """Ajoute une ligne pour une valeur modifiée."""
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        icon = Gtk.Label(label="🔄")
        row.append(icon)
        label = Gtk.Label(label=f'{key}: "{old_value}" → "{new_value}"')
        label.set_halign(Gtk.Align.START)
        label.get_style_context().add_class("warning")
        row.append(label)
        summary_box.append(row)

    @staticmethod
    def _add_no_changes_label(summary_box: Gtk.Box) -> None:
        """Ajoute un label si aucun changement."""
        label = Gtk.Label(label="Aucune modification détectée")
        label.get_style_context().add_class("dim-label")
        summary_box.append(label)
