"""Onglet Apparence - Simple configuration des couleurs et de l'image de fond."""

from __future__ import annotations

import os

from src.ui.gtk_init import Gtk
from src.ui.tabs.appearance_ui_builder import AppearanceUIBuilder
from src.ui.tabs.base import BaseTab
from src.utils.config import GRUB_COLORS
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AppearanceTab(BaseTab):
    """Classe pour l'onglet des paramètres d'apparence basiques."""

    # pylint: disable=too-many-statements
    def __init__(self, app):
        """Initialise l'onglet avec une référence à l'application."""
        super().__init__(app)

        # Initialisation des widgets
        self.normal_fg_dropdown = None
        self.normal_bg_dropdown = None
        self.highlight_fg_dropdown = None
        self.highlight_bg_dropdown = None
        self.background_type_dropdown = None
        self.background_entry = None
        self.background_file_button = None

        self.remove(self.grid)

        # Créer le layout principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)

        # Grille pour les paramètres
        grid = Gtk.Grid(column_spacing=10, row_spacing=15)
        grid.set_halign(Gtk.Align.CENTER)

        row = 0

        # Section Couleurs
        title_label = Gtk.Label(label="Couleurs", xalign=0)
        title_label.get_style_context().add_class("heading")
        grid.attach(title_label, 0, row, 2, 1)
        row += 1

        # Couleur normale - Texte
        grid.attach(Gtk.Label(label="Texte normal :", xalign=0), 0, row, 1, 1)
        self.normal_fg_dropdown = self._create_color_dropdown()
        grid.attach(self.normal_fg_dropdown, 1, row, 1, 1)
        row += 1

        # Couleur normale - Fond
        grid.attach(Gtk.Label(label="Fond normal :", xalign=0), 0, row, 1, 1)
        self.normal_bg_dropdown = self._create_color_dropdown()
        grid.attach(self.normal_bg_dropdown, 1, row, 1, 1)
        row += 1

        # Couleur sélection - Texte
        grid.attach(Gtk.Label(label="Texte sélection :", xalign=0), 0, row, 1, 1)
        self.highlight_fg_dropdown = self._create_color_dropdown()
        grid.attach(self.highlight_fg_dropdown, 1, row, 1, 1)
        row += 1

        # Couleur sélection - Fond
        grid.attach(Gtk.Label(label="Fond sélection :", xalign=0), 0, row, 1, 1)
        self.highlight_bg_dropdown = self._create_color_dropdown()
        grid.attach(self.highlight_bg_dropdown, 1, row, 1, 1)
        row += 1

        row = AppearanceUIBuilder.attach_horizontal_separator(grid, row)

        # Section Fond d'écran
        title_label = Gtk.Label(label="Fond d'écran", xalign=0)
        title_label.get_style_context().add_class("heading")
        grid.attach(title_label, 0, row, 2, 1)
        row += 1

        # Type de fond
        grid.attach(Gtk.Label(label="Type de fond :", xalign=0), 0, row, 1, 1)
        background_types = ["Couleur unie (thème standard)", "Image de fond"]
        self.background_type_dropdown = Gtk.DropDown.new_from_strings(background_types)
        self.background_type_dropdown.connect("notify::selected", self._on_background_type_changed)
        grid.attach(self.background_type_dropdown, 1, row, 1, 1)
        row += 1

        # Note explicative pour couleur unie
        info_label = Gtk.Label(
            label="Note : La couleur unie utilise la couleur de fond définie ci-dessus", xalign=0, wrap=True
        )
        info_label.get_style_context().add_class("dim-label")
        info_label.set_margin_bottom(5)
        grid.attach(info_label, 0, row, 2, 1)
        row += 1

        # Image de fond
        grid.attach(Gtk.Label(label="Fichier image :", xalign=0), 0, row, 1, 1)

        bg_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        self.background_entry = Gtk.Entry()
        self.background_entry.set_hexpand(True)
        self.background_entry.set_placeholder_text("/chemin/vers/image.png")
        bg_box.append(self.background_entry)

        self.background_file_button = Gtk.Button(label="Parcourir...")
        self.background_file_button.connect("clicked", self._on_background_file_clicked)
        bg_box.append(self.background_file_button)

        grid.attach(bg_box, 1, row, 1, 1)
        row += 1

        main_box.append(grid)
        self.append(main_box)

        # Charger les valeurs actuelles
        self._load_current_values()

    def _create_color_dropdown(self) -> Gtk.DropDown:
        """Crée un dropdown pour les couleurs GRUB."""
        model = Gtk.StringList()
        for _color_value, color_label in GRUB_COLORS:
            model.append(color_label)
        dropdown = Gtk.DropDown(model=model)
        dropdown.set_size_request(200, -1)
        return dropdown

    def _on_background_type_changed(self, dropdown, _pspec):
        """Gère le changement de type de fond (couleur unie vs image)."""
        selected = dropdown.get_selected()
        # 0 = Couleur unie, 1 = Image de fond
        use_image = selected == 1

        # Activer/désactiver les widgets d'image
        assert self.background_entry is not None
        assert self.background_file_button is not None
        self.background_entry.set_sensitive(use_image)
        self.background_file_button.set_sensitive(use_image)

        # Si on passe en couleur unie, vider le champ image
        if not use_image:
            self.background_entry.set_text("")

    def _load_current_values(self):
        """Charge les valeurs actuelles depuis la configuration."""
        # Couleurs normales
        normal = self.app.facade.entries.get("GRUB_COLOR_NORMAL", "light-gray/black")
        logger.debug("Chargement GRUB_COLOR_NORMAL: %s", normal)
        normal_fg, normal_bg = self._parse_color_pair(normal, "light-gray", "black")
        logger.debug("  -> Parsed: fg=%s, bg=%s", normal_fg, normal_bg)
        self._select_color(self.normal_fg_dropdown, normal_fg)
        self._select_color(self.normal_bg_dropdown, normal_bg)

        # Couleurs de sélection
        highlight = self.app.facade.entries.get("GRUB_COLOR_HIGHLIGHT", "white/dark-gray")
        logger.debug("Chargement GRUB_COLOR_HIGHLIGHT: %s", highlight)
        highlight_fg, highlight_bg = self._parse_color_pair(highlight, "white", "dark-gray")
        logger.debug("  -> Parsed: fg=%s, bg=%s", highlight_fg, highlight_bg)
        self._select_color(self.highlight_fg_dropdown, highlight_fg)
        self._select_color(self.highlight_bg_dropdown, highlight_bg)

        # Image de fond
        background = self.app.facade.entries.get("GRUB_BACKGROUND", "")
        assert self.background_entry is not None
        assert self.background_type_dropdown is not None

        # Déterminer le type de fond (0 = couleur unie, 1 = image)
        if background:
            self.background_type_dropdown.set_selected(1)  # Image de fond
            self.background_entry.set_text(background)
        else:
            self.background_type_dropdown.set_selected(0)  # Couleur unie
            self.background_entry.set_text("")
            # Désactiver les widgets d'image
            self.background_entry.set_sensitive(False)
            if self.background_file_button:
                self.background_file_button.set_sensitive(False)

    def _parse_color_pair(self, color_str: str, default_fg: str, default_bg: str) -> tuple[str, str]:
        """Parse une paire de couleurs au format 'fg/bg'."""
        if "/" in color_str:
            parts = color_str.split("/", 1)
            return parts[0].strip(), parts[1].strip()
        return default_fg, default_bg

    def _select_color(self, dropdown: Gtk.DropDown, color: str):
        """Sélectionne une couleur dans le dropdown."""
        try:
            # Chercher l'index par la valeur (premier élément du tuple)
            index = next(i for i, (c, _) in enumerate(GRUB_COLORS) if c == color)
            logger.debug("  Couleur '%s' trouvée à l'index %d, sélection en cours...", color, index)
            dropdown.set_selected(index)
            # Vérifier que la sélection a bien été prise en compte
            actual_index = dropdown.get_selected()
            if actual_index != index:
                logger.warning("  ATTENTION: Index sélectionné (%d) != Index demandé (%d)", actual_index, index)
        except StopIteration:
            # Couleur non trouvée, utiliser la première
            logger.warning("  Couleur '%s' non trouvée dans GRUB_COLORS, utilisation de l'index 0", color)
            dropdown.set_selected(0)

    def _get_selected_color(self, dropdown: Gtk.DropDown) -> str:
        """Récupère la couleur sélectionnée dans le dropdown."""
        index = dropdown.get_selected()
        if index < len(GRUB_COLORS):
            return GRUB_COLORS[index][0]  # Retourner la valeur, pas le label
        return GRUB_COLORS[0][0]

    def _on_background_file_clicked(self, _button):
        """Ouvre le dialogue de sélection de fichier pour l'image de fond."""
        dialog = Gtk.FileChooserDialog(
            title="Sélectionner une image de fond",
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.set_transient_for(self.app.win)
        dialog.set_modal(True)

        dialog.add_button("Annuler", Gtk.ResponseType.CANCEL)
        dialog.add_button("Ouvrir", Gtk.ResponseType.ACCEPT)

        # Filtre pour les images
        filter_images = Gtk.FileFilter()
        filter_images.set_name("Images")
        filter_images.add_mime_type("image/png")
        filter_images.add_mime_type("image/jpeg")
        filter_images.add_mime_type("image/jpg")
        filter_images.add_mime_type("image/tga")
        dialog.add_filter(filter_images)

        filter_all = Gtk.FileFilter()
        filter_all.set_name("Tous les fichiers")
        filter_all.add_pattern("*")
        dialog.add_filter(filter_all)

        dialog.connect("response", self._on_file_dialog_response)
        dialog.show()

    def _on_file_dialog_response(self, dialog, response):
        """Gère la réponse du dialogue de sélection de fichier."""
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            if file:
                path = file.get_path()
                assert self.background_entry is not None
                self.background_entry.set_text(path)
        dialog.destroy()

    def load_data(self):
        """Charge les données de configuration."""
        self._load_current_values()

    def get_config(self) -> dict[str, str]:
        """Récupère la configuration de l'onglet.

        Returns:
            dict[str, str]: Configuration modifiée

        """
        config = {}

        # Sauvegarder les couleurs
        normal_fg = self._get_selected_color(self.normal_fg_dropdown)
        normal_bg = self._get_selected_color(self.normal_bg_dropdown)
        config["GRUB_COLOR_NORMAL"] = f"{normal_fg}/{normal_bg}"

        highlight_fg = self._get_selected_color(self.highlight_fg_dropdown)
        highlight_bg = self._get_selected_color(self.highlight_bg_dropdown)
        config["GRUB_COLOR_HIGHLIGHT"] = f"{highlight_fg}/{highlight_bg}"

        # Sauvegarder l'image de fond
        assert self.background_entry is not None
        assert self.background_type_dropdown is not None

        # Vérifier le type de fond sélectionné
        use_image = self.background_type_dropdown.get_selected() == 1

        logger.debug("Type de fond sélectionné: %s", "Image" if use_image else "Couleur unie")

        if use_image:
            background = self.background_entry.get_text().strip()
            if background and os.path.exists(background):
                config["GRUB_BACKGROUND"] = background
            else:
                # Image sélectionné mais pas de fichier : chaîne vide pour suppression
                config["GRUB_BACKGROUND"] = ""
        else:
            # Couleur unie : chaîne vide pour que le code de nettoyage supprime l'entrée
            config["GRUB_BACKGROUND"] = ""

        return config

    def save_data(self) -> bool:
        """Sauvegarde les modifications dans la façade.

        Returns:
            True si la sauvegarde est réussie

        """
        # Sauvegarder les couleurs
        normal_fg = self._get_selected_color(self.normal_fg_dropdown)
        normal_bg = self._get_selected_color(self.normal_bg_dropdown)
        self.app.facade.entries["GRUB_COLOR_NORMAL"] = f"{normal_fg}/{normal_bg}"

        highlight_fg = self._get_selected_color(self.highlight_fg_dropdown)
        highlight_bg = self._get_selected_color(self.highlight_bg_dropdown)
        self.app.facade.entries["GRUB_COLOR_HIGHLIGHT"] = f"{highlight_fg}/{highlight_bg}"

        # Sauvegarder l'image de fond
        assert self.background_entry is not None
        assert self.background_type_dropdown is not None

        # Vérifier le type de fond sélectionné
        use_image = self.background_type_dropdown.get_selected() == 1

        if use_image:
            background = self.background_entry.get_text().strip()
            if background:
                # Vérifier que le fichier existe
                if not os.path.exists(background):
                    logger.warning("Image de fond non trouvée: %s", background)
                    return False
                self.app.facade.entries["GRUB_BACKGROUND"] = background
            else:
                # Si "Image de fond" est sélectionné mais aucun fichier n'est spécifié,
                # on supprime l'entrée (équivalent à couleur unie)
                self.app.facade.entries.pop("GRUB_BACKGROUND", None)
        else:
            # Type "Couleur unie" : supprimer GRUB_BACKGROUND pour utiliser uniquement les couleurs
            self.app.facade.entries.pop("GRUB_BACKGROUND", None)

        return True

    def restore_defaults(self):
        """Restaure les valeurs par défaut recommandées pour l'apparence GRUB."""
        # Couleurs par défaut de GRUB (valeurs officielles)
        # Normal: light-gray/black (texte gris clair sur fond noir)
        self._select_color(self.normal_fg_dropdown, "light-gray")
        self._select_color(self.normal_bg_dropdown, "black")

        # Highlight: white/dark-gray (texte blanc sur fond gris foncé)
        self._select_color(self.highlight_fg_dropdown, "white")
        self._select_color(self.highlight_bg_dropdown, "dark-gray")

        # Type de fond: Couleur unie (pas d'image)
        assert self.background_type_dropdown is not None
        self.background_type_dropdown.set_selected(0)  # 0 = Couleur unie

        # Vider le champ image
        assert self.background_entry is not None
        self.background_entry.set_text("")

        logger.info("Valeurs par défaut d'apparence restaurées")
        self.app.show_toast("Valeurs par défaut restaurées")
