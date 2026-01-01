"""Helper pour construire l'interface de l'onglet Appearance."""

from src.ui.gtk_init import Gtk
from src.utils.config import GRUB_COLORS


class AppearanceUIBuilder:
    """Construit l'interface utilisateur de l'onglet Appearance."""

    @staticmethod
    def attach_horizontal_separator(
        grid: Gtk.Grid,
        row: int,
        *,
        margin_top: int = 10,
        margin_bottom: int = 10,
        col_span: int = 2,
    ) -> int:
        """Attach a horizontal separator to the given grid.

        Args:
            grid: Target GTK grid
            row: Current row
            margin_top: Top margin in pixels
            margin_bottom: Bottom margin in pixels
            col_span: Number of columns spanned by the separator

        Returns:
            Next row index

        """
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_top(margin_top)
        separator.set_margin_bottom(margin_bottom)
        grid.attach(separator, 0, row, col_span, 1)
        return row + 1

    @staticmethod
    def create_color_section(grid: Gtk.Grid, row: int) -> tuple[int, dict]:
        """Crée la section des couleurs.

        Args:
            grid: Grille GTK
            row: Ligne de départ

        Returns:
            Tuple (nouvelle_ligne, widgets_dict)

        """
        # Section Couleurs
        title_label = Gtk.Label(label="Couleurs", xalign=0)
        title_label.get_style_context().add_class("heading")
        grid.attach(title_label, 0, row, 2, 1)
        row += 1

        widgets = {}

        # Couleur normale - Texte
        grid.attach(Gtk.Label(label="Texte normal :", xalign=0), 0, row, 1, 1)
        widgets["normal_fg_dropdown"] = AppearanceUIBuilder._create_color_dropdown()
        grid.attach(widgets["normal_fg_dropdown"], 1, row, 1, 1)
        row += 1

        # Couleur normale - Fond
        grid.attach(Gtk.Label(label="Fond normal :", xalign=0), 0, row, 1, 1)
        widgets["normal_bg_dropdown"] = AppearanceUIBuilder._create_color_dropdown()
        grid.attach(widgets["normal_bg_dropdown"], 1, row, 1, 1)
        row += 1

        # Couleur sélection - Texte
        grid.attach(Gtk.Label(label="Texte sélection :", xalign=0), 0, row, 1, 1)
        widgets["highlight_fg_dropdown"] = AppearanceUIBuilder._create_color_dropdown()
        grid.attach(widgets["highlight_fg_dropdown"], 1, row, 1, 1)
        row += 1

        # Couleur sélection - Fond
        grid.attach(Gtk.Label(label="Fond sélection :", xalign=0), 0, row, 1, 1)
        widgets["highlight_bg_dropdown"] = AppearanceUIBuilder._create_color_dropdown()
        grid.attach(widgets["highlight_bg_dropdown"], 1, row, 1, 1)
        row += 1

        return row, widgets

    @staticmethod
    def create_background_section(grid: Gtk.Grid, row: int) -> tuple[int, dict]:
        """Crée la section de l'image de fond.

        Args:
            grid: Grille GTK
            row: Ligne de départ

        Returns:
            Tuple (nouvelle_ligne, widgets_dict)

        """
        row = AppearanceUIBuilder.attach_horizontal_separator(grid, row)

        # Section Image de fond
        title_label = Gtk.Label(label="Image de fond", xalign=0)
        title_label.get_style_context().add_class("heading")
        grid.attach(title_label, 0, row, 2, 1)
        row += 1

        widgets = {}

        # Chemin image
        grid.attach(Gtk.Label(label="Chemin de l'image :", xalign=0), 0, row, 1, 1)
        widgets["background_entry"] = Gtk.Entry()
        widgets["background_entry"].set_hexpand(True)
        grid.attach(widgets["background_entry"], 1, row, 1, 1)
        row += 1

        # Bouton parcourir
        widgets["background_file_button"] = Gtk.Button(label="Parcourir...")
        grid.attach(widgets["background_file_button"], 1, row, 1, 1)
        row += 1

        return row, widgets

    @staticmethod
    def create_info_section() -> Gtk.Frame:
        """Crée la section d'informations.

        Returns:
            Gtk.Frame contenant les informations

        """
        info_frame = Gtk.Frame(label="Informations")
        info_frame.set_margin_top(20)

        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        info_box.set_margin_top(10)
        info_box.set_margin_bottom(10)
        info_box.set_margin_start(10)
        info_box.set_margin_end(10)

        info_label = Gtk.Label(wrap=True, xalign=0)
        info_label.set_markup(
            "<b>Configuration de l'apparence GRUB</b>\n\n"
            "Ces paramètres contrôlent l'apparence de l'écran de démarrage.\n\n"
            "• <b>Couleurs</b>: Texte et fond pour les entrées normales et sélectionnées\n"
            "• <b>Image de fond</b>: Image d'arrière-plan (optionnel)\n\n"
            "Formats supportés: PNG, JPG, TGA"
        )
        info_box.append(info_label)
        info_frame.set_child(info_box)

        return info_frame

    @staticmethod
    def _create_color_dropdown() -> Gtk.DropDown:
        """Crée un dropdown de sélection de couleur.

        Returns:
            Gtk.DropDown configuré

        """
        return Gtk.DropDown.new_from_strings(GRUB_COLORS)
