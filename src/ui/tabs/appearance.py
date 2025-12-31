"""Module pour l'onglet des paramètres d'apparence."""

from src.ui.gtk_init import Gtk
from src.ui.tabs.base import BaseTab
from src.utils.config import PREVIEW_WINDOW_HEIGHT, PREVIEW_WINDOW_WIDTH


class AppearanceTab(BaseTab):
    """Classe pour l'onglet des paramètres d'apparence."""

    def __init__(self, app):
        """Initialise l'onglet avec une référence à l'application."""
        super().__init__(app)

        # Résolution
        self.grid.attach(Gtk.Label(label="Résolution (GFXMODE) :", xalign=0), 0, 0, 1, 1)
        self.gfxmode_entry = Gtk.Entry(text=self.app.facade.entries.get("GRUB_GFXMODE", "auto"))
        self.gfxmode_entry.set_tooltip_text(
            "Résolution d'affichage de GRUB. 'auto' détecte automatiquement la meilleure résolution."
        )
        self.grid.attach(self.gfxmode_entry, 1, 0, 1, 1)

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

        # Thème
        self.grid.attach(Gtk.Label(label="Thème (theme.txt) :", xalign=0), 0, 2, 1, 1)
        theme_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.theme_entry = Gtk.Entry(
            text=self.app.facade.entries.get("GRUB_THEME", ""), hexpand=True
        )
        self.theme_entry.set_tooltip_text("Chemin vers un fichier de thème GRUB (fichier .txt).")
        theme_box.append(self.theme_entry)
        theme_btn = Gtk.Button(icon_name="folder-open-symbolic")
        theme_btn.set_tooltip_text("Sélectionner un thème")
        theme_btn.connect(
            "clicked",
            self.app.on_file_clicked,
            self.theme_entry,
            "Sélectionner un thème",
        )
        theme_box.append(theme_btn)
        self.grid.attach(theme_box, 1, 2, 1, 1)

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
        
        if self.gfxmode_entry:
            config["GRUB_GFXMODE"] = self.gfxmode_entry.get_text()

        if self.background_entry:
            config["GRUB_BACKGROUND"] = self.background_entry.get_text()

        if self.theme_entry:
            config["GRUB_THEME"] = self.theme_entry.get_text()
            
        # Note: GRUB_TERMINAL_OUTPUT logic is in App, but could be inferred here.
        # App logic: if bg or theme, set GRUB_TERMINAL_OUTPUT=gfxterm
        
        return config
