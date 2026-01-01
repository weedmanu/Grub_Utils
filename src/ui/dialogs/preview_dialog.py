"""Dialogue de prévisualisation de la configuration GRUB de base (couleurs et fond)."""

from src.core.dtos import PreviewConfigDTO
from src.ui.dialogs.grub_screen_builder import (
    GrubColorParser,
    GrubCSSBuilder,
    GrubMenuBuilder,
)
from src.ui.dialogs.summary_builder import SummaryBuilder
from src.ui.gtk_init import Gtk
from src.utils.config import PREVIEW_WINDOW_HEIGHT, PREVIEW_WINDOW_WIDTH


class PreviewDialog(Gtk.Window):
    """Affiche un aperçu visuel réaliste de l'écran de démarrage GRUB.

    Prévisualise uniquement les paramètres GRUB de base:
    - GRUB_COLOR_NORMAL (couleur texte/fond normal)
    - GRUB_COLOR_HIGHLIGHT (couleur texte/fond sélection)
    - GRUB_BACKGROUND (image de fond optionnelle)
    - GRUB_TIMEOUT, GRUB_DEFAULT, GRUB_GFXMODE

    N'utilise PAS de fichier theme.txt ni de configuration de thème avancée.
    """

    def __init__(
        self,
        parent: Gtk.Window,
        title: str,
        config: PreviewConfigDTO,
    ) -> None:
        """Initialize preview dialog.

        Args:
            parent: Parent window
            title: Dialog title
            config: Preview configuration DTO with old/new configs and entries

        """
        super().__init__(title=title)
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_default_size(PREVIEW_WINDOW_WIDTH, PREVIEW_WINDOW_HEIGHT)

        # Store configs for comparison
        self._old_config = config.old_config
        self._new_config = config.new_config
        self._has_changes = config.has_changes
        self._menu_entries = config.menu_entries or []
        self._hidden_entries = config.hidden_entries or []

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_top(12)
        main_box.set_margin_bottom(12)
        main_box.set_margin_start(12)
        main_box.set_margin_end(12)

        # Header with status indicator
        header_box = self._create_header(title)
        main_box.append(header_box)

        # Main preview area - the boot screen simulation
        preview_frame = self._create_boot_screen(self._new_config, self._menu_entries, self._hidden_entries)
        preview_frame.set_vexpand(True)
        main_box.append(preview_frame)

        # Changes summary (only if there are changes)
        if self._has_changes:
            summary_frame = self._create_summary_frame(self._old_config, self._new_config)
            main_box.append(summary_frame)
        else:
            info_label = Gtk.Label(label="ℹ️ Aperçu de la configuration actuelle (aucune modification)")
            info_label.set_halign(Gtk.Align.START)
            info_label.get_style_context().add_class("dim-label")
            main_box.append(info_label)

        # Close button
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.END)

        close_btn = Gtk.Button(label="Fermer")
        close_btn.connect("clicked", lambda _: self.close())
        button_box.append(close_btn)

        main_box.append(button_box)
        self.set_child(main_box)
        self.present()

    def _create_header(self, title: str) -> Gtk.Box:
        """Create header with title and status.

        Args:
            title: Dialog title

        Returns:
            Gtk.Box: Header box

        """
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        title_label = Gtk.Label(label=title)
        title_label.set_halign(Gtk.Align.START)
        title_label.get_style_context().add_class("title-2")
        title_label.set_hexpand(True)
        header_box.append(title_label)

        # Status badge
        if self._has_changes:
            status_label = Gtk.Label(label="● Modifications en attente")
            status_label.get_style_context().add_class("warning")
        else:
            status_label = Gtk.Label(label="● Configuration actuelle")
            status_label.get_style_context().add_class("success")
        status_label.set_halign(Gtk.Align.END)
        header_box.append(status_label)

        return header_box

    def _create_boot_screen(
        self,
        config: dict[str, str],
        menu_entries: list[dict] | None = None,
        hidden_entries: list[str] | None = None,
    ) -> Gtk.Frame:
        """Crée une visualisation réaliste de l'écran de démarrage GRUB.

        Utilise uniquement les paramètres GRUB standards (couleurs et fond),
        sans système de thème avancé ni fichier theme.txt.

        Args:
            config: Configuration GRUB (GRUB_COLOR_*, GRUB_BACKGROUND, etc.)
            menu_entries: Liste des entrées de menu
            hidden_entries: Liste des entrées masquées

        Returns:
            Gtk.Frame: Cadre contenant l'écran de démarrage simulé

        """
        frame = Gtk.Frame()
        frame.set_label("Simulation de l'écran de démarrage")
        frame.set_label_align(0.0)

        # Parser et valider les couleurs
        colors = GrubColorParser.parse_and_validate(config)

        # Vérifier l'image de fond
        background_image = config.get("GRUB_BACKGROUND", "")
        has_background = bool(background_image and background_image.strip())

        # Créer le CSS
        css_content = GrubCSSBuilder.build_css(colors, has_background)
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css_content.encode("utf-8"))

        # Créer le conteneur principal
        outer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer_box.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        outer_box.get_style_context().add_class("grub-screen")

        # Créer le contenu de l'écran
        screen_box = self._create_screen_content(config, menu_entries, hidden_entries, css_provider)

        outer_box.append(screen_box)
        frame.set_child(outer_box)
        return frame

    def _create_screen_content(
        self,
        config: dict[str, str],
        menu_entries: list[dict] | None,
        hidden_entries: list[str] | None,
        css_provider: Gtk.CssProvider,
    ) -> Gtk.Box:
        """Crée le contenu de l'écran GRUB.

        Args:
            config: Configuration GRUB
            menu_entries: Liste des entrées de menu
            hidden_entries: Liste des entrées masquées
            css_provider: Fournisseur CSS

        Returns:
            Gtk.Box contenant tout le contenu de l'écran

        """
        screen_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        # Indicateur d'image de fond
        background_image = config.get("GRUB_BACKGROUND", "")
        if background_image and background_image.strip():
            self._add_background_indicator(screen_box, background_image, css_provider)

        # Menu GRUB
        menu_border = self._create_grub_menu(config, menu_entries, hidden_entries, css_provider)
        screen_box.append(menu_border)

        # Spacer
        screen_box.append(Gtk.Label(label=""))

        # Textes d'aide
        self._add_help_text(screen_box, css_provider)

        # Informations de statut
        timeout = config.get("GRUB_TIMEOUT", "5")
        gfxmode = config.get("GRUB_GFXMODE", "auto")
        self._add_status_info(screen_box, timeout, gfxmode, css_provider)

        return screen_box

    def _add_background_indicator(
        self, container: Gtk.Box, background_image: str, css_provider: Gtk.CssProvider
    ) -> None:
        """Ajoute un indicateur visuel pour l'image de fond."""
        bg_info = Gtk.Label(label=f"🖼️ Image de fond: {background_image}")
        bg_info.set_halign(Gtk.Align.CENTER)
        bg_info.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        bg_info.get_style_context().add_class("grub-footer")
        container.append(bg_info)
        container.append(Gtk.Label(label=""))  # Spacer

    def _create_grub_menu(
        self,
        config: dict[str, str],
        menu_entries: list[dict] | None,
        hidden_entries: list[str] | None,
        css_provider: Gtk.CssProvider,
    ) -> Gtk.Box:
        """Crée le menu GRUB."""
        menu_border = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        menu_border.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        menu_border.get_style_context().add_class("grub-menu-border")
        menu_border.set_halign(Gtk.Align.CENTER)
        menu_border.set_size_request(700, -1)

        # Barre de titre
        title_bar = Gtk.Label(label="  GNU GRUB  ")
        title_bar.set_halign(Gtk.Align.FILL)
        title_bar.set_hexpand(True)
        title_bar.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        title_bar.get_style_context().add_class("grub-menu-title")
        menu_border.append(title_bar)

        # Contenu du menu
        menu_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        menu_content.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        menu_content.get_style_context().add_class("grub-menu-content")

        GrubMenuBuilder.create_menu_entries(menu_content, config, menu_entries, hidden_entries, css_provider)

        menu_border.append(menu_content)
        return menu_border

    def _add_help_text(self, container: Gtk.Box, css_provider: Gtk.CssProvider) -> None:
        """Ajoute les textes d'aide GRUB."""
        help_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        help_box.set_halign(Gtk.Align.CENTER)

        help_texts = [
            "Use the ↑ and ↓ keys to select which entry is highlighted.",
            "Press enter to boot the selected OS, 'e' to edit the commands",
            "before booting or 'c' for a command-line.",
        ]

        for text in help_texts:
            label = Gtk.Label(label=text)
            label.set_halign(Gtk.Align.CENTER)
            label.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            label.get_style_context().add_class("grub-footer")
            help_box.append(label)

        container.append(help_box)

    def _add_status_info(
        self,
        container: Gtk.Box,
        timeout: str,
        _gfxmode: str,
        css_provider: Gtk.CssProvider,
    ) -> None:
        """Ajoute les informations de statut (timeout).

        Args:
            container: Conteneur GTK
            timeout: Valeur du timeout en secondes
            _gfxmode: Mode graphique (non utilisé pour l'instant)
            css_provider: Fournisseur CSS

        """
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        info_box.set_halign(Gtk.Align.CENTER)

        timeout_msg = self._get_timeout_message(timeout)

        timeout_label = Gtk.Label(label=timeout_msg)
        timeout_label.set_halign(Gtk.Align.CENTER)
        timeout_label.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        timeout_label.get_style_context().add_class("grub-countdown")
        info_box.append(timeout_label)

        container.append(info_box)

    @staticmethod
    def _get_timeout_message(timeout: str) -> str:
        """Détermine le message de timeout approprié.

        Args:
            timeout: Valeur du timeout

        Returns:
            Message formaté pour le timeout

        """
        try:
            timeout_int = int(timeout)
            if timeout_int > 0:
                return f"The highlighted entry will be executed automatically in {timeout}s."
            if timeout_int == 0:
                return "Démarrage instantané configuré (timeout=0)"
            return "Menu affiché indéfiniment (timeout=-1)"
        except ValueError:
            return f"Timeout: {timeout}"

    @staticmethod
    def _create_summary_frame(old_config: dict[str, str], new_config: dict[str, str]) -> Gtk.Frame:
        """Create summary of configuration changes.

        Args:
            old_config: Current configuration
            new_config: New configuration

        Returns:
            Gtk.Frame: Summary frame

        """
        return SummaryBuilder.create_summary_frame(old_config, new_config)
