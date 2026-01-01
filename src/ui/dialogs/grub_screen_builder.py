"""Builder pour créer les éléments visuels de l'écran GRUB."""

# pylint: disable=too-few-public-methods
# Classes utilitaires spécialisées avec responsabilité unique

from dataclasses import dataclass

from src.ui.gtk_init import Gtk
from src.utils.config import (
    ALLOWED_GRUB_COLOR_NAMES,
    grub_color_to_hex,
    parse_grub_color_pair,
)


@dataclass
class GrubColors:
    """Configuration des couleurs GRUB validées."""

    normal_fg: str
    normal_bg: str
    highlight_fg: str
    highlight_bg: str

    @property
    def normal_fg_hex(self) -> str:
        """Convertit la couleur normale avant-plan en hexadécimal."""
        return grub_color_to_hex(self.normal_fg)

    @property
    def normal_bg_hex(self) -> str:
        """Convertit la couleur normale arrière-plan en hexadécimal."""
        return grub_color_to_hex(self.normal_bg)

    @property
    def highlight_fg_hex(self) -> str:
        """Convertit la couleur sélection avant-plan en hexadécimal."""
        return grub_color_to_hex(self.highlight_fg)

    @property
    def highlight_bg_hex(self) -> str:
        """Convertit la couleur sélection arrière-plan en hexadécimal."""
        return grub_color_to_hex(self.highlight_bg)


class GrubColorParser:
    """Parse et valide les couleurs GRUB depuis la configuration."""

    @staticmethod
    def parse_and_validate(config: dict[str, str]) -> GrubColors:
        """Parse et valide les couleurs depuis la configuration.

        Args:
            config: Configuration GRUB

        Returns:
            GrubColors validées avec fallback par défaut

        """
        normal_colors = config.get("GRUB_COLOR_NORMAL", "light-gray/black")
        highlight_colors = config.get("GRUB_COLOR_HIGHLIGHT", "black/light-gray")

        normal_fg, normal_bg = parse_grub_color_pair(normal_colors)
        highlight_fg, highlight_bg = parse_grub_color_pair(highlight_colors)

        # Valider et appliquer les fallbacks
        return GrubColors(
            normal_fg=normal_fg if normal_fg in ALLOWED_GRUB_COLOR_NAMES else "light-gray",
            normal_bg=normal_bg if normal_bg in ALLOWED_GRUB_COLOR_NAMES else "black",
            highlight_fg=highlight_fg if highlight_fg in ALLOWED_GRUB_COLOR_NAMES else "black",
            highlight_bg=highlight_bg if highlight_bg in ALLOWED_GRUB_COLOR_NAMES else "light-gray",
        )


class GrubCSSBuilder:
    """Construit le CSS pour la simulation de l'écran GRUB."""

    @staticmethod
    def build_css(colors: GrubColors, has_background: bool) -> str:
        """Construit le CSS complet pour l'écran GRUB.

        Args:
            colors: Couleurs GRUB validées
            has_background: Si une image de fond est configurée

        Returns:
            CSS complet en tant que chaîne

        """
        # CSS de base pour l'écran
        base_css = GrubCSSBuilder._build_screen_css(colors, has_background)

        # CSS pour le menu
        menu_css = GrubCSSBuilder._build_menu_css(colors)

        # CSS pour les textes
        text_css = GrubCSSBuilder._build_text_css(colors)

        return base_css + menu_css + text_css

    @staticmethod
    def _build_screen_css(colors: GrubColors, has_background: bool) -> str:
        """Construit le CSS pour l'écran principal."""
        if has_background:
            return f"""
            .grub-screen {{
                background-color: {colors.normal_bg_hex};
                background-image: linear-gradient(rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.3));
                padding: 30px 40px;
                border-radius: 0;
            }}"""
        return f"""
            .grub-screen {{
                background-color: {colors.normal_bg_hex};
                padding: 30px 40px;
                border-radius: 0;
            }}"""

    @staticmethod
    def _build_menu_css(colors: GrubColors) -> str:
        """Construit le CSS pour les éléments de menu."""
        return f"""
            .grub-menu-border {{
                background-color: {colors.normal_bg_hex};
                border: 2px solid {colors.normal_fg_hex};
                padding: 0;
            }}
            .grub-menu-title {{
                background-color: {colors.normal_fg_hex};
                color: {colors.normal_bg_hex};
                font-family: "DejaVu Sans Mono", "Liberation Mono", monospace;
                font-size: 14px;
                font-weight: bold;
                padding: 4px 10px;
            }}
            .grub-menu-content {{
                background-color: {colors.normal_bg_hex};
                padding: 6px 0;
            }}
            .grub-entry {{
                color: {colors.normal_fg_hex};
                background-color: {colors.normal_bg_hex};
                font-family: "DejaVu Sans Mono", "Liberation Mono", monospace;
                font-size: 14px;
                padding: 4px 10px;
                margin: 0;
                min-height: 22px;
            }}
            .grub-entry-selected {{
                background-color: {colors.highlight_bg_hex};
                color: {colors.highlight_fg_hex};
                font-family: "DejaVu Sans Mono", "Liberation Mono", monospace;
                font-size: 14px;
                padding: 4px 10px;
                margin: 0;
                min-height: 22px;
            }}"""

    @staticmethod
    def _build_text_css(colors: GrubColors) -> str:
        """Construit le CSS pour les textes d'aide et countdown."""
        return f"""
            .grub-footer {{
                color: {colors.normal_fg_hex};
                font-family: "DejaVu Sans Mono", "Liberation Mono", monospace;
                font-size: 12px;
            }}
            .grub-countdown {{
                color: {colors.normal_fg_hex};
                font-family: "DejaVu Sans Mono", "Liberation Mono", monospace;
                font-size: 12px;
            }}
        """


class GrubMenuBuilder:
    """Construit les éléments visuels du menu GRUB."""

    @staticmethod
    def create_menu_entries(
        container: Gtk.Box,
        config: dict[str, str],
        menu_entries: list[dict] | None,
        hidden_entries: list[str] | None,
        css_provider: Gtk.CssProvider,
    ) -> None:
        """Crée les entrées de menu GRUB.

        Args:
            container: Conteneur GTK pour les entrées
            config: Configuration GRUB
            menu_entries: Liste des entrées de menu
            hidden_entries: Liste des entrées masquées
            css_provider: Fournisseur CSS pour le style

        """
        default_entry = config.get("GRUB_DEFAULT", "0")
        default_idx = GrubMenuBuilder._parse_default_index(default_entry)

        entries = GrubMenuBuilder._prepare_entries(menu_entries, hidden_entries)

        max_visible = 8
        visible_entries = entries[:max_visible]

        for idx, name in enumerate(visible_entries):
            label = GrubMenuBuilder._create_entry_label(name, idx == default_idx, css_provider)
            container.append(label)

        # Indicateur pour les entrées supplémentaires
        if len(entries) > max_visible:
            more_label = Gtk.Label(label=f"  ... ({len(entries) - max_visible} more entries)  ")
            more_label.set_halign(Gtk.Align.FILL)
            more_label.set_xalign(0.0)
            more_label.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            more_label.get_style_context().add_class("grub-entry")
            container.append(more_label)

    @staticmethod
    def _parse_default_index(default_entry: str) -> int:
        """Parse l'index de l'entrée par défaut."""
        try:
            return int(default_entry)
        except ValueError:
            return 0

    @staticmethod
    def _prepare_entries(menu_entries: list[dict] | None, hidden_entries: list[str] | None) -> list[str]:
        """Prépare la liste des entrées visibles."""
        hidden_set = set(hidden_entries or [])

        if menu_entries:
            entries = []
            for entry in menu_entries:
                title = entry.get("title", "Unknown")
                if title not in hidden_set:
                    entries.append(title)
            return entries

        # Entrées par défaut si non fournies
        return [
            "Ubuntu",
            "Advanced options for Ubuntu",
            "Memory test (memtest86+x64.efi)",
            "Memory test (memtest86+x64.efi, serial console)",
        ]

    @staticmethod
    def _create_entry_label(name: str, is_selected: bool, css_provider: Gtk.CssProvider) -> Gtk.Label:
        """Crée un label GTK pour une entrée de menu."""
        label = Gtk.Label(label=f"  {name}  ")
        label.set_halign(Gtk.Align.FILL)
        label.set_xalign(0.0)
        label.set_wrap(True)
        label.set_natural_wrap_mode(Gtk.NaturalWrapMode.WORD)
        label.set_max_width_chars(80)

        label.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        css_class = "grub-entry-selected" if is_selected else "grub-entry"
        label.get_style_context().add_class(css_class)

        return label
