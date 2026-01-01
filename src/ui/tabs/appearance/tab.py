"""Onglet Apparence.

Responsabilité: orchestration UI + adaptation config <-> widgets.
Les utilitaires (widgets/parse theme) sont déportés dans des sous-modules.
"""

from __future__ import annotations

import sys

from src.core.config.theme_config import ThemeConfigManager, ThemeConfiguration
from src.ui.dialogs.error_dialog import ErrorDialog, ErrorOptions
from src.ui.gtk_init import Gtk
from src.ui.tabs.base import BaseTab
from src.utils.config import PREVIEW_WINDOW_HEIGHT, PREVIEW_WINDOW_WIDTH
from src.utils.logger import get_logger

from .theme import hex_to_color_name, parse_theme_file
from .widgets import (
    create_color_dropdown,
    create_percentage_dropdown,
    create_simple_dropdown,
    get_dropdown_value,
    select_from_dropdown,
    select_from_simple_dropdown,
)

logger = get_logger(__name__)


class AppearanceTab(BaseTab):
    """Classe pour l'onglet des paramètres d'apparence."""

    def __init__(self, app):
        """Initialise l'onglet avec une référence à l'application."""
        super().__init__(app)

        # Accès dynamique aux constantes du package (compatible patchs tests).
        pkg = sys.modules[__package__]
        self._pkg = pkg

        # Initialisation des widgets
        self.gfxmode_model = None
        self.gfxmode_dropdown = None
        self.theme_enabled_switch = None
        self.background_entry = None
        self.theme_entry = None
        self.font_entry = None
        self.normal_fg_dropdown = None
        self.normal_bg_dropdown = None
        self.highlight_fg_dropdown = None
        self.highlight_bg_dropdown = None
        self.preview_image = None
        self.preview_label = None
        self.preview_frame = None
        self.preview_box = None
        self.theme_listbox = None
        self.theme_preview_image = None
        self.theme_author_label = None
        self.theme_desc_label = None
        self.theme_version_label = None
        self.theme_date_label = None
        self.theme_license_label = None
        self.theme_resolution_label = None
        self.theme_boot_menu_label = None
        self.theme_progress_bar_label = None
        self.theme_icons_label = None
        self.theme_terminal_label = None
        self.theme_animation_label = None
        self.theme_scroll_label = None
        self.theme_input_label = None
        self.theme_hotkey_label = None
        self.theme_footer_label = None
        self.theme_header_label = None
        self.theme_countdown_label = None
        self.theme_message_label = None
        self.theme_console_label = None
        self.theme_editor_label = None
        self.theme_help_label = None
        self.theme_popup_label = None
        self.theme_dialog_label = None
        self.theme_menu_label = None
        self.theme_term_label = None
        self.theme_list_label = None
        self.theme_item_label = None
        self.theme_selected_item_label = None
        self.theme_icon_label = None
        self.theme_arrow_label = None
        self.theme_slider_label = None
        self.theme_scrollbar_label = None
        self.theme_box_label = None
        self.theme_text_label = None
        self.theme_null_label = None

        self.remove(self.grid)

        # Créer le layout principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        main_box.set_margin_start(10)
        main_box.set_margin_end(10)

        notebook = Gtk.Notebook()
        notebook.set_vexpand(True)
        notebook.set_hexpand(True)
        notebook.set_margin_top(10)
        notebook.set_margin_bottom(10)
        notebook.set_margin_start(10)
        notebook.set_margin_end(10)

        # ===== Page 1: Style Global (Affichage) =====
        page1_box = self._create_global_style_page()
        notebook.append_page(page1_box, Gtk.Label(label="Style Global"))

        # ===== Page 2: Couleurs =====
        page_colors_box = self._create_colors_page()
        notebook.append_page(page_colors_box, Gtk.Label(label="Couleurs"))

        # Créer les pages restantes via _build_remaining_pages() qui les construit toutes
        self._build_remaining_pages(notebook)

        main_box.append(notebook)
        self.append(main_box)

        self._load_current_colors()
        self._load_current_advanced_settings()

    def _create_global_style_page(self) -> Gtk.Box:
        """Crée la page de style global (affichage seulement)."""
        page1_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        page1_box.set_margin_top(20)
        page1_box.set_margin_bottom(20)
        page1_box.set_margin_start(20)
        page1_box.set_margin_end(20)

        left_grid = Gtk.Grid(column_spacing=10, row_spacing=10)

        self._setup_display_section(left_grid)

        page1_box.append(left_grid)

        return page1_box

    def _setup_display_section(self, grid: Gtk.Grid):
        """Configure la section affichage."""
        row = 0

        title_label = Gtk.Label(label="Affichage", xalign=0)
        title_label.get_style_context().add_class("heading")
        grid.attach(title_label, 0, row, 2, 1)
        row += 1

        # Option pour activer/désactiver le thème
        grid.attach(Gtk.Label(label="Utiliser le thème :", xalign=0), 0, row, 1, 1)
        self.theme_enabled_switch = Gtk.Switch()
        self.theme_enabled_switch.set_active(self.app.facade.entries.get("GRUB_USE_THEME", "true").lower() == "true")
        self.theme_enabled_switch.set_tooltip_text("Activer ou désactiver l'utilisation du theme.txt")
        self.theme_enabled_switch.set_halign(Gtk.Align.START)
        switch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        switch_box.append(self.theme_enabled_switch)
        grid.attach(switch_box, 1, row, 1, 1)
        row += 1

        grid.attach(Gtk.Label(label="Résolution :", xalign=0), 0, row, 1, 1)
        self.gfxmode_model = Gtk.StringList()
        for _value, label in self._pkg.GRUB_RESOLUTIONS:
            self.gfxmode_model.append(label)

        self.gfxmode_dropdown = Gtk.DropDown(model=self.gfxmode_model)
        self.gfxmode_dropdown.set_tooltip_text(
            "Résolution d'affichage de GRUB. 'Automatique' détecte la meilleure résolution."
        )
        current_gfxmode = self.app.facade.entries.get("GRUB_GFXMODE", "auto")
        self._select_resolution(current_gfxmode)
        grid.attach(self.gfxmode_dropdown, 1, row, 1, 1)
        row += 1

        grid.attach(Gtk.Label(label="Image de fond :", xalign=0), 0, row, 1, 1)
        bg_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.background_entry = Gtk.Entry(text=self.app.facade.entries.get("GRUB_BACKGROUND", ""), hexpand=True)
        self.background_entry.set_tooltip_text("Chemin vers une image de fond pour GRUB (PNG, JPG, TGA).")
        bg_box.append(self.background_entry)

        bg_btn = Gtk.Button(icon_name="folder-open-symbolic")
        bg_btn.set_tooltip_text("Sélectionner une image")
        bg_btn.connect(
            "clicked",
            self.app.on_file_clicked,
            self.background_entry,
            "Sélectionner une image",
        )
        bg_box.append(bg_btn)

        grid.attach(bg_box, 1, row, 1, 1)
        row += 1

        sep1 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        grid.attach(sep1, 0, row, 2, 1)
        row += 1

    def _setup_colors_section(self, grid: Gtk.Grid):
        """Configure la section couleurs."""
        # Trouver la prochaine ligne disponible
        row = 0
        while grid.get_child_at(0, row) is not None or grid.get_child_at(1, row) is not None:
            row += 1

        color_title = Gtk.Label(label="Couleurs du menu", xalign=0)
        color_title.get_style_context().add_class("heading")
        grid.attach(color_title, 0, row, 2, 1)
        row += 1

        grid.attach(Gtk.Label(label="Texte normal :", xalign=0), 0, row, 1, 1)
        self.normal_fg_dropdown = create_color_dropdown(
            Gtk,
            self._pkg.GRUB_COLORS,
            "light-gray",
            color_to_hex=self._pkg.GRUB_COLOR_TO_HEX,
        )
        grid.attach(self.normal_fg_dropdown, 1, row, 1, 1)
        row += 1

        grid.attach(Gtk.Label(label="Fond normal :", xalign=0), 0, row, 1, 1)
        self.normal_bg_dropdown = create_color_dropdown(
            Gtk,
            self._pkg.GRUB_COLORS,
            "black",
            color_to_hex=self._pkg.GRUB_COLOR_TO_HEX,
        )
        grid.attach(self.normal_bg_dropdown, 1, row, 1, 1)
        row += 1

        grid.attach(Gtk.Label(label="Texte sélectionné :", xalign=0), 0, row, 1, 1)
        self.highlight_fg_dropdown = create_color_dropdown(
            Gtk,
            self._pkg.GRUB_COLORS,
            "white",
            color_to_hex=self._pkg.GRUB_COLOR_TO_HEX,
        )
        grid.attach(self.highlight_fg_dropdown, 1, row, 1, 1)
        row += 1

        grid.attach(Gtk.Label(label="Fond sélectionné :", xalign=0), 0, row, 1, 1)
        self.highlight_bg_dropdown = create_color_dropdown(
            Gtk,
            self._pkg.GRUB_COLORS,
            "dark-gray",
            color_to_hex=self._pkg.GRUB_COLOR_TO_HEX,
        )
        grid.attach(self.highlight_bg_dropdown, 1, row, 1, 1)
        row += 1

    def _create_colors_page(self) -> Gtk.Box:
        """Crée la page de gestion des couleurs."""
        page_colors_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        page_colors_box.set_margin_top(20)
        page_colors_box.set_margin_bottom(20)
        page_colors_box.set_margin_start(20)
        page_colors_box.set_margin_end(20)

        colors_grid = Gtk.Grid(column_spacing=10, row_spacing=10)
        self._setup_colors_section(colors_grid)

        page_colors_box.append(colors_grid)

        return page_colors_box

    def _build_remaining_pages(self, notebook: Gtk.Notebook) -> None:
        """Construit et attache les pages restantes au notebook."""
        pkg = self._pkg

        # ===== Page 3: Positionnement =====
        page_positionnement = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        page_positionnement.set_margin_top(20)
        page_positionnement.set_margin_bottom(20)
        page_positionnement.set_margin_start(20)
        page_positionnement.set_margin_end(20)

        middle_grid = Gtk.Grid(column_spacing=10, row_spacing=10)

        # ===== Colonne 2: Positionnement + Éléments =====
        row = 0
        pos_title = Gtk.Label(label="Positionnement", xalign=0)
        pos_title.get_style_context().add_class("heading")
        middle_grid.attach(pos_title, 0, row, 2, 1)
        row += 1

        middle_grid.attach(Gtk.Label(label="Position gauche :", xalign=0), 0, row, 1, 1)
        self.menu_left_dropdown = create_percentage_dropdown(Gtk, self._pkg.GRUB_MENU_POSITIONS, "5%")
        middle_grid.attach(self.menu_left_dropdown, 1, row, 1, 1)
        row += 1

        middle_grid.attach(Gtk.Label(label="Position haut :", xalign=0), 0, row, 1, 1)
        self.menu_top_dropdown = create_percentage_dropdown(Gtk, self._pkg.GRUB_MENU_TOPS, "25%")
        middle_grid.attach(self.menu_top_dropdown, 1, row, 1, 1)
        row += 1

        middle_grid.attach(Gtk.Label(label="Largeur :", xalign=0), 0, row, 1, 1)
        self.menu_width_dropdown = create_percentage_dropdown(Gtk, self._pkg.GRUB_MENU_WIDTHS, "90%")
        middle_grid.attach(self.menu_width_dropdown, 1, row, 1, 1)
        row += 1

        middle_grid.attach(Gtk.Label(label="Hauteur :", xalign=0), 0, row, 1, 1)
        self.menu_height_dropdown = create_percentage_dropdown(Gtk, self._pkg.GRUB_MENU_HEIGHTS, "50%")
        middle_grid.attach(self.menu_height_dropdown, 1, row, 1, 1)
        row += 1

        sep2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        middle_grid.attach(sep2, 0, row, 2, 1)
        row += 1

        item_title = Gtk.Label(label="Éléments de menu", xalign=0)
        item_title.get_style_context().add_class("heading")
        middle_grid.attach(item_title, 0, row, 2, 1)
        row += 1

        middle_grid.attach(Gtk.Label(label="Hauteur (px) :", xalign=0), 0, row, 1, 1)
        self.item_height_dropdown = create_simple_dropdown(Gtk, pkg.GRUB_ITEM_HEIGHTS, "36")
        middle_grid.attach(self.item_height_dropdown, 1, row, 1, 1)
        row += 1

        middle_grid.attach(Gtk.Label(label="Espacement (px) :", xalign=0), 0, row, 1, 1)
        self.item_spacing_dropdown = create_simple_dropdown(Gtk, pkg.GRUB_ITEM_SPACINGS, "5")
        middle_grid.attach(self.item_spacing_dropdown, 1, row, 1, 1)
        row += 1

        middle_grid.attach(Gtk.Label(label="Rembourrage (px) :", xalign=0), 0, row, 1, 1)
        self.item_padding_dropdown = create_simple_dropdown(Gtk, pkg.GRUB_ITEM_PADDINGS, "10")
        middle_grid.attach(self.item_padding_dropdown, 1, row, 1, 1)
        row += 1

        middle_grid.attach(Gtk.Label(label="Espacement icône (px) :", xalign=0), 0, row, 1, 1)
        self.icon_spacing_dropdown = create_simple_dropdown(Gtk, pkg.GRUB_ICON_SPACINGS, "10")
        middle_grid.attach(self.icon_spacing_dropdown, 1, row, 1, 1)
        row += 1

        page_positionnement.append(middle_grid)
        notebook.append_page(page_positionnement, Gtk.Label(label="Positionnement"))

        # ===== Page 4: Textes (Titre/Label + Progress) =====
        page3_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        page3_box.set_margin_top(20)
        page3_box.set_margin_bottom(20)
        page3_box.set_margin_start(20)
        page3_box.set_margin_end(20)

        text_grid = Gtk.Grid(column_spacing=10, row_spacing=10)

        row = 0
        label_title = Gtk.Label(label="Titre et Label", xalign=0)
        label_title.get_style_context().add_class("heading")
        text_grid.attach(label_title, 0, row, 2, 1)
        row += 1

        text_grid.attach(Gtk.Label(label="Titre :", xalign=0), 0, row, 1, 1)
        self.title_text_entry = Gtk.Entry(text="Start booting")
        self.title_text_entry.set_tooltip_text("Texte du titre (vide pour aucun)")
        text_grid.attach(self.title_text_entry, 1, row, 1, 1)
        row += 1

        text_grid.attach(Gtk.Label(label="Label :", xalign=0), 0, row, 1, 1)
        self.label_text_entry = Gtk.Entry(text="GNU GRUB version %v")
        self.label_text_entry.set_tooltip_text("Texte du label (version, etc)")
        text_grid.attach(self.label_text_entry, 1, row, 1, 1)
        row += 1

        text_grid.attach(Gtk.Label(label="Label left (%) :", xalign=0), 0, row, 1, 1)
        self.label_left_dropdown = create_percentage_dropdown(Gtk, pkg.GRUB_LABEL_LEFTS, "5%")
        text_grid.attach(self.label_left_dropdown, 1, row, 1, 1)
        row += 1

        text_grid.attach(Gtk.Label(label="Label top (%) :", xalign=0), 0, row, 1, 1)
        self.label_top_dropdown = create_percentage_dropdown(Gtk, pkg.GRUB_LABEL_TOPS, "2%")
        text_grid.attach(self.label_top_dropdown, 1, row, 1, 1)
        row += 1

        text_grid.attach(Gtk.Label(label="Couleur du label :", xalign=0), 0, row, 1, 1)
        self.label_color_dropdown = create_color_dropdown(
            Gtk,
            pkg.GRUB_PROGRESS_COLORS,
            "light-gray",
            color_to_hex=pkg.GRUB_COLOR_TO_HEX,
        )
        text_grid.attach(self.label_color_dropdown, 1, row, 1, 1)
        row += 1

        text_grid.attach(Gtk.Label(label="Progress bottom (%) :", xalign=0), 0, row, 1, 1)
        self.progress_bottom_dropdown = create_percentage_dropdown(Gtk, pkg.GRUB_PROGRESS_BOTTOMS, "90%")
        text_grid.attach(self.progress_bottom_dropdown, 1, row, 1, 1)
        row += 1

        sep4 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        text_grid.attach(sep4, 0, row, 2, 1)
        row += 1

        prog_title = Gtk.Label(label="Barre de progression", xalign=0)
        prog_title.get_style_context().add_class("heading")
        text_grid.attach(prog_title, 0, row, 2, 1)
        row += 1

        text_grid.attach(Gtk.Label(label="Position left (%) :", xalign=0), 0, row, 1, 1)
        self.progress_left_dropdown = create_percentage_dropdown(Gtk, pkg.GRUB_PROGRESS_LEFTS, "5%")
        text_grid.attach(self.progress_left_dropdown, 1, row, 1, 1)
        row += 1

        text_grid.attach(Gtk.Label(label="Largeur (%) :", xalign=0), 0, row, 1, 1)
        self.progress_width_dropdown = create_percentage_dropdown(Gtk, pkg.GRUB_PROGRESS_WIDTHS, "90%")
        text_grid.attach(self.progress_width_dropdown, 1, row, 1, 1)
        row += 1

        text_grid.attach(Gtk.Label(label="Hauteur (px) :", xalign=0), 0, row, 1, 1)
        self.progress_height_dropdown = create_simple_dropdown(Gtk, pkg.GRUB_PROGRESS_HEIGHTS, "12")
        text_grid.attach(self.progress_height_dropdown, 1, row, 1, 1)
        row += 1

        text_grid.attach(Gtk.Label(label="Couleur bordure :", xalign=0), 0, row, 1, 1)
        self.progress_border_dropdown = create_color_dropdown(
            Gtk,
            pkg.GRUB_PROGRESS_COLORS,
            "white",
            color_to_hex=pkg.GRUB_COLOR_TO_HEX,
        )
        text_grid.attach(self.progress_border_dropdown, 1, row, 1, 1)
        row += 1

        text_grid.attach(Gtk.Label(label="Couleur barre :", xalign=0), 0, row, 1, 1)
        self.progress_bar_dropdown = create_color_dropdown(
            Gtk,
            pkg.GRUB_PROGRESS_COLORS,
            "light-gray",
            color_to_hex=pkg.GRUB_COLOR_TO_HEX,
        )
        text_grid.attach(self.progress_bar_dropdown, 1, row, 1, 1)
        row += 1

        text_grid.attach(Gtk.Label(label="Couleur fond barre :", xalign=0), 0, row, 1, 1)
        self.progress_bg_dropdown = create_color_dropdown(
            Gtk,
            pkg.GRUB_PROGRESS_COLORS,
            "black",
            color_to_hex=pkg.GRUB_COLOR_TO_HEX,
        )
        text_grid.attach(self.progress_bg_dropdown, 1, row, 1, 1)
        row += 1

        page3_box.append(text_grid)
        notebook.append_page(page3_box, Gtk.Label(label="Textes"))

        # ===== Page 5: Polices =====
        page4_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        page4_box.set_margin_top(20)
        page4_box.set_margin_bottom(20)
        page4_box.set_margin_start(20)
        page4_box.set_margin_end(20)

        font_grid = Gtk.Grid(column_spacing=10, row_spacing=10)

        row = 0
        font_title = Gtk.Label(label="Polices", xalign=0)
        font_title.get_style_context().add_class("heading")
        font_grid.attach(font_title, 0, row, 2, 1)
        row += 1

        # NOTE: GRUB supports ONLY the "unicode" font in gfxmenu mode
        # Font family selection is disabled since only unicode is available
        font_grid.attach(Gtk.Label(label="Police (unicode uniquement) :", xalign=0), 0, row, 1, 1)
        self.font_item_dropdown = create_simple_dropdown(Gtk, pkg.GRUB_FONTS, "unicode")
        self.font_item_dropdown.set_sensitive(False)  # Read-only since only unicode is available
        font_grid.attach(self.font_item_dropdown, 1, row, 1, 1)
        row += 1

        font_grid.attach(Gtk.Label(label="Taille item (pt) :", xalign=0), 0, row, 1, 1)
        self.font_size_item_dropdown = create_simple_dropdown(Gtk, pkg.GRUB_FONT_SIZES, "14")
        font_grid.attach(self.font_size_item_dropdown, 1, row, 1, 1)
        row += 1

        font_grid.attach(Gtk.Label(label="Taille item sel. (pt) :", xalign=0), 0, row, 1, 1)
        self.font_size_item_hl_dropdown = create_simple_dropdown(Gtk, pkg.GRUB_FONT_SIZES, "16")
        font_grid.attach(self.font_size_item_hl_dropdown, 1, row, 1, 1)
        row += 1

        font_grid.attach(Gtk.Label(label="Taille label (pt) :", xalign=0), 0, row, 1, 1)
        self.font_size_label_dropdown = create_simple_dropdown(Gtk, pkg.GRUB_FONT_SIZES, "12")
        font_grid.attach(self.font_size_label_dropdown, 1, row, 1, 1)
        row += 1

        # Info sur les limitations
        info_label = Gtk.Label(
            label="⚠️ GRUB ne supporte que la police 'unicode' en mode thème.\n"
            "Les polices système (DejaVu, Liberation, etc.) ne sont pas supportées.",
            xalign=0,
            wrap=True,
        )
        info_label.add_css_class("dim-label")
        font_grid.attach(info_label, 0, row, 2, 1)
        row += 1

        page4_box.append(font_grid)
        notebook.append_page(page4_box, Gtk.Label(label="Polices"))

    def _get_color_value(self, dropdown: Gtk.DropDown) -> str:
        idx = dropdown.get_selected()
        if 0 <= idx < len(self._pkg.GRUB_COLORS):
            return self._pkg.GRUB_COLORS[idx][0]
        return "black"

    def _select_color(self, dropdown: Gtk.DropDown, value: str) -> None:
        for idx, (color_value, _) in enumerate(self._pkg.GRUB_COLORS):
            if color_value == value:
                dropdown.set_selected(idx)
                return
        dropdown.set_selected(0)

    def _load_current_colors(self) -> None:
        normal = self.app.facade.entries.get("GRUB_COLOR_NORMAL", "light-gray/black")
        highlight = self.app.facade.entries.get("GRUB_COLOR_HIGHLIGHT", "white/dark-gray")

        if "/" in normal:
            text, bg = normal.split("/", 1)
            self._select_color(self.normal_fg_dropdown, text)
            self._select_color(self.normal_bg_dropdown, bg)

        if "/" in highlight:
            text, bg = highlight.split("/", 1)
            self._select_color(self.highlight_fg_dropdown, text)
            self._select_color(self.highlight_bg_dropdown, bg)

    def _load_current_advanced_settings(self) -> None:
        theme_values = self._parse_theme_file()

        # Charger l'état d'activation du thème
        use_theme = self.app.facade.entries.get("GRUB_USE_THEME", "true").lower() == "true"
        self.theme_enabled_switch.set_active(use_theme)

        menu_left = theme_values.get("menu_left") or self.app.facade.entries.get("GRUB_MENU_LEFT", "5%")
        select_from_dropdown(self.menu_left_dropdown, menu_left, self._pkg.GRUB_MENU_POSITIONS)

        menu_top = theme_values.get("menu_top") or self.app.facade.entries.get("GRUB_MENU_TOP", "25%")
        select_from_dropdown(self.menu_top_dropdown, menu_top, self._pkg.GRUB_MENU_TOPS)

        menu_width = theme_values.get("menu_width") or self.app.facade.entries.get("GRUB_MENU_WIDTH", "90%")
        select_from_dropdown(self.menu_width_dropdown, menu_width, self._pkg.GRUB_MENU_WIDTHS)

        menu_height = theme_values.get("menu_height") or self.app.facade.entries.get("GRUB_MENU_HEIGHT", "50%")
        select_from_dropdown(self.menu_height_dropdown, menu_height, self._pkg.GRUB_MENU_HEIGHTS)

        item_height = theme_values.get("item_height") or self.app.facade.entries.get("GRUB_ITEM_HEIGHT", "36")
        select_from_simple_dropdown(self.item_height_dropdown, item_height, self._pkg.GRUB_ITEM_HEIGHTS)

        item_spacing = theme_values.get("item_spacing") or self.app.facade.entries.get("GRUB_ITEM_SPACING", "5")
        select_from_simple_dropdown(self.item_spacing_dropdown, item_spacing, self._pkg.GRUB_ITEM_SPACINGS)

        item_padding = theme_values.get("item_padding") or self.app.facade.entries.get("GRUB_ITEM_PADDING", "10")
        select_from_simple_dropdown(self.item_padding_dropdown, item_padding, self._pkg.GRUB_ITEM_PADDINGS)

        # Polices - GRUB supporte uniquement "unicode"
        font_item = theme_values.get("font_item") or self.app.facade.entries.get("GRUB_FONT_ITEM", "unicode 14")
        font_parts = font_item.rsplit(" ", 1)
        if len(font_parts) == 2:
            font_size = font_parts[1]
        else:
            font_size = "14"
        select_from_simple_dropdown(self.font_size_item_dropdown, font_size, self._pkg.GRUB_FONT_SIZES)

        font_item_hl = theme_values.get("font_item_highlight") or self.app.facade.entries.get(
            "GRUB_FONT_ITEM_HIGHLIGHT", "unicode 16"
        )
        font_parts = font_item_hl.rsplit(" ", 1)
        if len(font_parts) == 2:
            font_size = font_parts[1]
        else:
            font_size = "16"
        select_from_simple_dropdown(self.font_size_item_hl_dropdown, font_size, self._pkg.GRUB_FONT_SIZES)

        font_label = theme_values.get("font_label") or self.app.facade.entries.get("GRUB_FONT_LABEL", "unicode 12")
        font_parts = font_label.rsplit(" ", 1)
        if len(font_parts) == 2:
            font_size = font_parts[1]
        else:
            font_size = "12"
        select_from_simple_dropdown(self.font_size_label_dropdown, font_size, self._pkg.GRUB_FONT_SIZES)

        icon_spacing = theme_values.get("icon_spacing") or self.app.facade.entries.get("GRUB_ICON_SPACING", "10")
        select_from_simple_dropdown(self.icon_spacing_dropdown, icon_spacing, self._pkg.GRUB_ICON_SPACINGS)

        label_left = theme_values.get("label_left") or self.app.facade.entries.get("GRUB_LABEL_LEFT", "5%")
        select_from_dropdown(self.label_left_dropdown, label_left, self._pkg.GRUB_LABEL_LEFTS)

        label_top = theme_values.get("label_top") or self.app.facade.entries.get("GRUB_LABEL_TOP", "2%")
        select_from_dropdown(self.label_top_dropdown, label_top, self._pkg.GRUB_LABEL_TOPS)

        progress_bottom = theme_values.get("progress_bottom") or self.app.facade.entries.get(
            "GRUB_PROGRESS_BOTTOM", "90%"
        )
        select_from_dropdown(self.progress_bottom_dropdown, progress_bottom, self._pkg.GRUB_PROGRESS_BOTTOMS)

        progress_border = theme_values.get("progress_border") or self.app.facade.entries.get(
            "GRUB_PROGRESS_BORDER", "white"
        )
        if progress_border.startswith("#"):
            progress_border = hex_to_color_name(progress_border, self._pkg.GRUB_COLOR_TO_HEX) or "white"
        select_from_simple_dropdown(
            self.progress_border_dropdown,
            progress_border,
            self._pkg.GRUB_PROGRESS_COLORS,
        )

        progress_bar = theme_values.get("progress_bar") or self.app.facade.entries.get(
            "GRUB_PROGRESS_BAR", "light-gray"
        )
        if progress_bar.startswith("#"):
            progress_bar = hex_to_color_name(progress_bar, self._pkg.GRUB_COLOR_TO_HEX) or "light-gray"
        select_from_simple_dropdown(self.progress_bar_dropdown, progress_bar, self._pkg.GRUB_PROGRESS_COLORS)

        # Nouvelles valeurs: label_color, progress_left, progress_width, progress_height, progress_bg
        label_color = theme_values.get("label_color") or self.app.facade.entries.get("GRUB_LABEL_COLOR", "light-gray")
        if label_color.startswith("#"):
            label_color = hex_to_color_name(label_color, self._pkg.GRUB_COLOR_TO_HEX) or "light-gray"
        select_from_simple_dropdown(self.label_color_dropdown, label_color, self._pkg.GRUB_PROGRESS_COLORS)

        progress_left = theme_values.get("progress_left") or self.app.facade.entries.get("GRUB_PROGRESS_LEFT", "5%")
        select_from_dropdown(self.progress_left_dropdown, progress_left, self._pkg.GRUB_PROGRESS_LEFTS)

        progress_width = theme_values.get("progress_width") or self.app.facade.entries.get("GRUB_PROGRESS_WIDTH", "90%")
        select_from_dropdown(self.progress_width_dropdown, progress_width, self._pkg.GRUB_PROGRESS_WIDTHS)

        progress_height = theme_values.get("progress_height") or self.app.facade.entries.get(
            "GRUB_PROGRESS_HEIGHT", "12"
        )
        select_from_simple_dropdown(self.progress_height_dropdown, progress_height, self._pkg.GRUB_PROGRESS_HEIGHTS)

        progress_bg = theme_values.get("progress_bg") or self.app.facade.entries.get("GRUB_PROGRESS_BG", "black")
        if progress_bg.startswith("#"):
            progress_bg = hex_to_color_name(progress_bg, self._pkg.GRUB_COLOR_TO_HEX) or "black"
        select_from_simple_dropdown(self.progress_bg_dropdown, progress_bg, self._pkg.GRUB_PROGRESS_COLORS)

    def _select_resolution(self, value: str) -> None:
        for idx, (res_value, _) in enumerate(self._pkg.GRUB_RESOLUTIONS):
            if res_value == value:
                self.gfxmode_dropdown.set_selected(idx)
                return
        self.gfxmode_dropdown.set_selected(0)

    def _get_selected_resolution(self) -> str:
        selected_idx = self.gfxmode_dropdown.get_selected()
        if 0 <= selected_idx < len(self._pkg.GRUB_RESOLUTIONS):
            return self._pkg.GRUB_RESOLUTIONS[selected_idx][0]
        return "auto"

    def on_preview_clicked(self, _btn):
        """Handle preview button click."""
        path = self.background_entry.get_text()
        if not path:
            return

        preview_win = Gtk.Window(title="Aperçu de l'image")
        preview_win.set_default_size(PREVIEW_WINDOW_WIDTH, PREVIEW_WINDOW_HEIGHT)
        preview_win.set_transient_for(self.app.win)
        preview_win.set_modal(True)

        picture = Gtk.Picture.new_for_filename(path)
        picture.set_can_shrink(True)
        preview_win.set_child(picture)
        preview_win.present()

    def get_config(self) -> dict[str, str]:
        """Get current configuration from UI.

        Saves theme settings to theme_config.json and returns only GRUB standard parameters.
        """
        # Create theme configuration from UI
        theme_config = ThemeConfiguration(
            # Background
            background_image=self.background_entry.get_text() if self.background_entry else "",
            desktop_color="#000000",
            # Menu positioning
            menu_left=get_dropdown_value(self.menu_left_dropdown, self._pkg.GRUB_MENU_POSITIONS),
            menu_top=get_dropdown_value(self.menu_top_dropdown, self._pkg.GRUB_MENU_TOPS),
            menu_width=get_dropdown_value(self.menu_width_dropdown, self._pkg.GRUB_MENU_WIDTHS),
            menu_height=get_dropdown_value(self.menu_height_dropdown, self._pkg.GRUB_MENU_HEIGHTS),
            item_height=get_dropdown_value(self.item_height_dropdown, self._pkg.GRUB_ITEM_HEIGHTS),
            item_spacing=get_dropdown_value(self.item_spacing_dropdown, self._pkg.GRUB_ITEM_SPACINGS),
            item_padding=get_dropdown_value(self.item_padding_dropdown, self._pkg.GRUB_ITEM_PADDINGS),
            # Colors
            normal_fg=self._get_color_value(self.normal_fg_dropdown),
            normal_bg=self._get_color_value(self.normal_bg_dropdown),
            highlight_fg=self._get_color_value(self.highlight_fg_dropdown),
            highlight_bg=self._get_color_value(self.highlight_bg_dropdown),
            # Textes
            title_text=self.title_text_entry.get_text() or "",
            label_text=self.label_text_entry.get_text() or "",
            label_left=get_dropdown_value(self.label_left_dropdown, self._pkg.GRUB_LABEL_LEFTS),
            label_top=get_dropdown_value(self.label_top_dropdown, self._pkg.GRUB_LABEL_TOPS),
            label_color=get_dropdown_value(self.label_color_dropdown, self._pkg.GRUB_PROGRESS_COLORS),
            # Progress bar
            progress_left=get_dropdown_value(self.progress_left_dropdown, self._pkg.GRUB_PROGRESS_LEFTS),
            progress_bottom=get_dropdown_value(self.progress_bottom_dropdown, self._pkg.GRUB_PROGRESS_BOTTOMS),
            progress_width=get_dropdown_value(self.progress_width_dropdown, self._pkg.GRUB_PROGRESS_WIDTHS),
            progress_height=get_dropdown_value(self.progress_height_dropdown, self._pkg.GRUB_PROGRESS_HEIGHTS),
            progress_fg=get_dropdown_value(self.progress_bar_dropdown, self._pkg.GRUB_PROGRESS_COLORS),
            progress_bg=get_dropdown_value(self.progress_bg_dropdown, self._pkg.GRUB_PROGRESS_COLORS),
            progress_border=get_dropdown_value(self.progress_border_dropdown, self._pkg.GRUB_PROGRESS_COLORS),
            # Polices (GRUB supporte uniquement "unicode")
            font_normal="unicode",
            font_highlight="unicode",
            font_label="unicode",
            font_normal_size=get_dropdown_value(self.font_size_item_dropdown, self._pkg.GRUB_FONT_SIZES),
            font_highlight_size=get_dropdown_value(self.font_size_item_hl_dropdown, self._pkg.GRUB_FONT_SIZES),
            font_label_size=get_dropdown_value(self.font_size_label_dropdown, self._pkg.GRUB_FONT_SIZES),
            # Activation
            enabled=self.theme_enabled_switch.get_active(),
        )

        # Save theme configuration to JSON file
        config_manager = ThemeConfigManager()
        success, error = config_manager.save(theme_config, self.app.facade.grub_service.executor)

        if not success:
            logger.error("Failed to save theme configuration: %s", error)
            # Show error dialog but continue
            ErrorDialog(
                parent=self.get_root(),
                options=ErrorOptions(
                    title="Erreur",
                    message="Erreur lors de la sauvegarde de la configuration du thème",
                    details=error,
                ),
            )
        else:
            logger.info("Theme configuration saved to theme_config.json")

        # Return only standard GRUB parameters for /etc/default/grub
        config: dict[str, str] = {}
        config["GRUB_GFXMODE"] = self._get_selected_resolution()

        # GRUB_THEME is set automatically by grub_service when generating theme.txt
        # GRUB_TERMINAL_OUTPUT is set to gfxterm by app.py if theme is enabled

        return config

    def on_reset_defaults_clicked(self, _btn):
        """Handle reset defaults button click."""
        self.normal_fg_dropdown.set_selected(0)
        self.normal_bg_dropdown.set_selected(0)
        self.highlight_fg_dropdown.set_selected(0)
        self.highlight_bg_dropdown.set_selected(0)

        self.menu_left_dropdown.set_selected(1)
        self.menu_top_dropdown.set_selected(2)
        self.menu_width_dropdown.set_selected(4)
        self.menu_height_dropdown.set_selected(1)

        self.item_height_dropdown.set_selected(4)
        self.item_spacing_dropdown.set_selected(1)
        self.item_padding_dropdown.set_selected(1)

        # Polices - GRUB supporte uniquement "unicode"
        self.font_size_item_dropdown.set_selected(2)
        self.font_size_item_hl_dropdown.set_selected(3)
        self.font_size_label_dropdown.set_selected(1)

    def restore_defaults(self):
        """Restaure les valeurs par défaut (style grub-update)."""
        # Activation du thème
        self.theme_enabled_switch.set_active(True)

        # Resolution
        self._select_resolution("auto")

        # Background
        self.background_entry.set_text("")

        # Colors
        self._select_color(self.normal_fg_dropdown, "light-gray")
        self._select_color(self.normal_bg_dropdown, "black")
        self._select_color(self.highlight_fg_dropdown, "white")
        self._select_color(self.highlight_bg_dropdown, "dark-gray")

        # Position
        select_from_dropdown(self.menu_left_dropdown, "5%", self._pkg.GRUB_MENU_POSITIONS)
        select_from_dropdown(self.menu_top_dropdown, "25%", self._pkg.GRUB_MENU_TOPS)
        select_from_dropdown(self.menu_width_dropdown, "90%", self._pkg.GRUB_MENU_WIDTHS)
        select_from_dropdown(self.menu_height_dropdown, "50%", self._pkg.GRUB_MENU_HEIGHTS)

        # Items
        select_from_simple_dropdown(self.item_height_dropdown, "36", self._pkg.GRUB_ITEM_HEIGHTS)
        select_from_simple_dropdown(self.item_spacing_dropdown, "5", self._pkg.GRUB_ITEM_SPACINGS)
        select_from_simple_dropdown(self.item_padding_dropdown, "10", self._pkg.GRUB_ITEM_PADDINGS)
        select_from_simple_dropdown(self.icon_spacing_dropdown, "10", self._pkg.GRUB_ICON_SPACINGS)

        # Text / Label
        self.title_text_entry.set_text("")
        self.label_text_entry.set_text("GNU GRUB version %v")
        select_from_dropdown(self.label_left_dropdown, "5%", self._pkg.GRUB_LABEL_LEFTS)
        select_from_dropdown(self.label_top_dropdown, "2%", self._pkg.GRUB_LABEL_TOPS)

        # Progress
        select_from_dropdown(self.progress_bottom_dropdown, "90%", self._pkg.GRUB_PROGRESS_BOTTOMS)
        select_from_simple_dropdown(self.progress_border_dropdown, "white", self._pkg.GRUB_PROGRESS_COLORS)
        select_from_simple_dropdown(self.progress_bar_dropdown, "light-gray", self._pkg.GRUB_PROGRESS_COLORS)
        select_from_simple_dropdown(self.label_color_dropdown, "light-gray", self._pkg.GRUB_PROGRESS_COLORS)
        select_from_dropdown(self.progress_left_dropdown, "5%", self._pkg.GRUB_PROGRESS_LEFTS)
        select_from_dropdown(self.progress_width_dropdown, "90%", self._pkg.GRUB_PROGRESS_WIDTHS)
        select_from_simple_dropdown(self.progress_height_dropdown, "12", self._pkg.GRUB_PROGRESS_HEIGHTS)
        select_from_simple_dropdown(self.progress_bg_dropdown, "black", self._pkg.GRUB_PROGRESS_COLORS)

        # Polices - GRUB supporte uniquement "unicode"
        select_from_simple_dropdown(self.font_size_item_dropdown, "14", self._pkg.GRUB_FONT_SIZES)
        select_from_simple_dropdown(self.font_size_item_hl_dropdown, "16", self._pkg.GRUB_FONT_SIZES)
        select_from_simple_dropdown(self.font_size_label_dropdown, "12", self._pkg.GRUB_FONT_SIZES)

        self.app.show_toast("Valeurs par défaut restaurées")

        self.icon_spacing_dropdown.set_selected(2)
        self.label_left_dropdown.set_selected(1)
        self.label_top_dropdown.set_selected(1)
        self.progress_bottom_dropdown.set_selected(2)
        self.progress_border_dropdown.set_selected(15)
        self.progress_bar_dropdown.set_selected(7)

        self.title_text_entry.set_text("")
        self.label_text_entry.set_text("GNU GRUB version %v")

        self.app.show_toast("Valeurs par défaut réinitialisées")

    def _parse_theme_file(self) -> dict:
        theme_path = "/boot/grub/themes/custom/theme.txt"
        return parse_theme_file(theme_path, logger)
