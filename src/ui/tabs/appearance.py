"""Module pour l'onglet des paramètres d'apparence."""

from src.ui.gtk_init import Gtk
from src.ui.tabs.base import BaseTab
from src.utils.config import (
    GRUB_COLORS,
    GRUB_RESOLUTIONS,
    PREVIEW_WINDOW_HEIGHT,
    PREVIEW_WINDOW_WIDTH,
)


class AppearanceTab(BaseTab):
    """Classe pour l'onglet des paramètres d'apparence."""

    def __init__(self, app):
        """Initialise l'onglet avec une référence à l'application."""
        super().__init__(app)

        # Résolution - Liste déroulante au lieu d'un champ texte
        self.grid.attach(Gtk.Label(label="Résolution (GFXMODE) :", xalign=0), 0, 0, 1, 1)
        
        # Créer le modèle de liste pour le dropdown
        self.gfxmode_model = Gtk.StringList()
        for value, label in GRUB_RESOLUTIONS:
            self.gfxmode_model.append(label)
        
        self.gfxmode_dropdown = Gtk.DropDown(model=self.gfxmode_model)
        self.gfxmode_dropdown.set_tooltip_text(
            "Résolution d'affichage de GRUB. 'Automatique' détecte la meilleure résolution."
        )
        
        # Sélectionner la valeur actuelle
        current_gfxmode = self.app.facade.entries.get("GRUB_GFXMODE", "auto")
        self._select_resolution(current_gfxmode)
        
        self.grid.attach(self.gfxmode_dropdown, 1, 0, 1, 1)

        # Image de fond
        self.grid.attach(Gtk.Label(label="Image de fond :", xalign=0), 0, 1, 1, 1)
        bg_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.background_entry = Gtk.Entry(
            text=self.app.facade.entries.get("GRUB_BACKGROUND", ""), hexpand=True
        )
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

        preview_btn = Gtk.Button(icon_name="image-x-generic-symbolic")
        preview_btn.set_tooltip_text("Aperçu de l'image")
        preview_btn.connect("clicked", self.on_preview_clicked)
        bg_box.append(preview_btn)

        self.grid.attach(bg_box, 1, 1, 1, 1)

        # Séparateur pour les couleurs
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_top(10)
        separator.set_margin_bottom(10)
        self.grid.attach(separator, 0, 2, 2, 1)

        # Titre section couleurs
        color_title = Gtk.Label(label="Couleurs du menu", xalign=0)
        color_title.get_style_context().add_class("heading")
        self.grid.attach(color_title, 0, 3, 2, 1)

        # Couleur texte normal
        self.grid.attach(Gtk.Label(label="Texte normal :", xalign=0), 0, 4, 1, 1)
        self.normal_text_dropdown = self._create_color_dropdown("light-gray")
        self.grid.attach(self.normal_text_dropdown, 1, 4, 1, 1)

        # Couleur fond normal
        self.grid.attach(Gtk.Label(label="Fond normal :", xalign=0), 0, 5, 1, 1)
        self.normal_bg_dropdown = self._create_color_dropdown("black")
        self.grid.attach(self.normal_bg_dropdown, 1, 5, 1, 1)

        # Couleur texte sélectionné
        self.grid.attach(Gtk.Label(label="Texte sélectionné :", xalign=0), 0, 6, 1, 1)
        self.highlight_text_dropdown = self._create_color_dropdown("black")
        self.grid.attach(self.highlight_text_dropdown, 1, 6, 1, 1)

        # Couleur fond sélectionné
        self.grid.attach(Gtk.Label(label="Fond sélectionné :", xalign=0), 0, 7, 1, 1)
        self.highlight_bg_dropdown = self._create_color_dropdown("light-gray")
        self.grid.attach(self.highlight_bg_dropdown, 1, 7, 1, 1)

        # Charger les couleurs actuelles
        self._load_current_colors()

    def _create_color_dropdown(self, default: str) -> Gtk.DropDown:
        """Crée un dropdown de sélection de couleur.

        Args:
            default: Couleur par défaut

        Returns:
            Gtk.DropDown: Le dropdown créé

        """
        model = Gtk.StringList()
        for _, label in GRUB_COLORS:
            model.append(label)
        
        dropdown = Gtk.DropDown(model=model)
        
        # Sélectionner la couleur par défaut
        for idx, (value, _) in enumerate(GRUB_COLORS):
            if value == default:
                dropdown.set_selected(idx)
                break
        
        return dropdown

    def _get_color_value(self, dropdown: Gtk.DropDown) -> str:
        """Récupère la valeur de couleur sélectionnée.

        Args:
            dropdown: Le dropdown de couleur

        Returns:
            str: La valeur GRUB de la couleur

        """
        idx = dropdown.get_selected()
        if 0 <= idx < len(GRUB_COLORS):
            return GRUB_COLORS[idx][0]
        return "black"

    def _select_color(self, dropdown: Gtk.DropDown, value: str) -> None:
        """Sélectionne une couleur dans un dropdown.

        Args:
            dropdown: Le dropdown
            value: La valeur GRUB de la couleur

        """
        for idx, (color_value, _) in enumerate(GRUB_COLORS):
            if color_value == value:
                dropdown.set_selected(idx)
                return
        dropdown.set_selected(0)

    def _load_current_colors(self) -> None:
        """Charge les couleurs actuelles depuis la configuration."""
        # Format: "texte/fond" (ex: "light-gray/black")
        normal = self.app.facade.entries.get("GRUB_COLOR_NORMAL", "light-gray/black")
        highlight = self.app.facade.entries.get("GRUB_COLOR_HIGHLIGHT", "black/light-gray")
        
        if "/" in normal:
            text, bg = normal.split("/", 1)
            self._select_color(self.normal_text_dropdown, text)
            self._select_color(self.normal_bg_dropdown, bg)
        
        if "/" in highlight:
            text, bg = highlight.split("/", 1)
            self._select_color(self.highlight_text_dropdown, text)
            self._select_color(self.highlight_bg_dropdown, bg)

    def _select_resolution(self, value: str) -> None:
        """Sélectionne la résolution dans le dropdown.

        Args:
            value: Valeur de résolution (ex: "1920x1080" ou "auto")

        """
        for idx, (res_value, _) in enumerate(GRUB_RESOLUTIONS):
            if res_value == value:
                self.gfxmode_dropdown.set_selected(idx)
                return
        # Si la valeur n'est pas dans la liste, sélectionner "auto"
        self.gfxmode_dropdown.set_selected(0)

    def _get_selected_resolution(self) -> str:
        """Récupère la résolution sélectionnée.

        Returns:
            str: Valeur de résolution (ex: "1920x1080" ou "auto")

        """
        selected_idx = self.gfxmode_dropdown.get_selected()
        if 0 <= selected_idx < len(GRUB_RESOLUTIONS):
            return GRUB_RESOLUTIONS[selected_idx][0]
        return "auto"

    def on_preview_clicked(self, _btn):
        """Affiche un aperçu de l'image de fond."""
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
        """Récupère la configuration de l'onglet.

        Returns:
            dict[str, str]: Configuration modifiée

        """
        config = {}
        
        # Récupérer la résolution depuis le dropdown
        config["GRUB_GFXMODE"] = self._get_selected_resolution()

        if self.background_entry:
            bg = self.background_entry.get_text()
            if bg:
                config["GRUB_BACKGROUND"] = bg

        # Récupérer les couleurs
        normal_text = self._get_color_value(self.normal_text_dropdown)
        normal_bg = self._get_color_value(self.normal_bg_dropdown)
        config["GRUB_COLOR_NORMAL"] = f"{normal_text}/{normal_bg}"

        highlight_text = self._get_color_value(self.highlight_text_dropdown)
        highlight_bg = self._get_color_value(self.highlight_bg_dropdown)
        config["GRUB_COLOR_HIGHLIGHT"] = f"{highlight_text}/{highlight_bg}"
        
        return config
