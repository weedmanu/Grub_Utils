"""Application principale GTK pour la gestion de GRUB."""

from typing import Optional

import gi

# GTK requires gi.require_version() before imports
gi.require_version("Gtk", "4.0")
gi.require_version("GLib", "2.0")
try:
    gi.require_version("Adw", "1")
    from gi.repository import Adw

    HAS_ADW = True
except ImportError:
    HAS_ADW = False

from gi.repository import GLib, Gtk

from src.core.grub_manager import GrubManager
from src.ui.dialogs.confirm_dialog import ConfirmDialog
from src.ui.dialogs.error_dialog import ErrorDialog
from src.ui.tab_widgets import TabWidgets
from src.ui.tabs.appearance import AppearanceTab
from src.ui.tabs.general import GeneralTab
from src.ui.tabs.menu import MenuTab
from src.utils.config import MAIN_WINDOW_HEIGHT, MAIN_WINDOW_WIDTH, TOAST_TIMEOUT
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GrubApp(Gtk.Application):
    """Application principale GTK pour la gestion de GRUB."""

    def __init__(self):
        """Initialise l'application et les variables d'état."""
        super().__init__(application_id="com.example.GrubUtils")
        self.manager = GrubManager()
        self.win = None
        self.widgets = TabWidgets()
        self.overlay = None
        self.toast_revealer = None
        self.toast_label = None

    def do_activate(self, *_args, **_kwargs):  # vulture: ignore
        """Active l'application et construit l'interface utilisateur."""
        self.manager.load()
        self._build_ui()

    def _build_ui(self):
        """Construit les composants de l'interface."""
        if not self.win:
            if HAS_ADW:
                self.win = Adw.ApplicationWindow(application=self)
            else:
                self.win = Gtk.ApplicationWindow(application=self)
            self.win.set_title("Grub Customizer (Python)")
            self.win.set_default_size(MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        if HAS_ADW:
            self.win.set_content(box)
            header = Adw.HeaderBar()
        else:
            self.win.set_child(box)
            header = Gtk.HeaderBar()
        box.append(header)

        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        stack_switcher = Gtk.StackSwitcher(stack=stack)
        header.set_title_widget(stack_switcher)

        stack.add_titled(GeneralTab(self), "general", "Général")
        stack.add_titled(AppearanceTab(self), "appearance", "Apparence")
        stack.add_titled(MenuTab(self), "menu", "Menu")

        self._add_footer(box)
        box.append(stack)

        # Overlay pour les notifications
        self.overlay = Gtk.Overlay()
        self.overlay.set_child(box)

        # Revealer pour les notifications toast-like
        self.toast_revealer = Gtk.Revealer()
        self.toast_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.toast_revealer.set_valign(Gtk.Align.START)
        self.toast_revealer.set_halign(Gtk.Align.CENTER)
        self.toast_revealer.set_margin_top(10)

        toast_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        toast_box.set_margin_start(20)
        toast_box.set_margin_end(20)
        toast_box.set_margin_top(10)
        toast_box.set_margin_bottom(10)
        toast_box.get_style_context().add_class("osd")  # Style toast-like

        self.toast_label = Gtk.Label()
        toast_box.append(self.toast_label)

        close_btn = Gtk.Button(icon_name="window-close-symbolic")
        close_btn.connect("clicked", lambda _: self.toast_revealer.set_reveal_child(False))
        toast_box.append(close_btn)

        self.toast_revealer.set_child(toast_box)
        self.overlay.add_overlay(self.toast_revealer)

        self.win.set_content(self.overlay)
        self.win.present()

    def show_toast(self, message: str, timeout: int = TOAST_TIMEOUT):
        """
        Affiche une notification toast.

        Args:
            message: Message à afficher
            timeout: Durée en ms avant disparition automatique
        """
        self.toast_label.set_text(message)
        self.toast_revealer.set_reveal_child(True)

        # Masquer automatiquement après le timeout
        def hide_toast():
            self.toast_revealer.set_reveal_child(False)
            return False  # Ne pas répéter

        # Convertir ms en secondes pour GLib.timeout_add
        GLib.timeout_add(timeout, hide_toast)

    def _add_footer(self, box):
        """Ajoute le pied de page avec les boutons d'action."""
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        for margin in ["top", "bottom", "start", "end"]:
            getattr(footer, f"set_margin_{margin}")(10)
        box.append(footer)

        reset_btn = Gtk.Button(label="Réinitialiser")
        reset_btn.set_tooltip_text("Restaurer la dernière sauvegarde de configuration")
        reset_btn.connect("clicked", self.on_reset_clicked)
        footer.append(reset_btn)

        save_btn = Gtk.Button(label="Sauvegarder et Appliquer", hexpand=True)
        save_btn.set_tooltip_text("Sauvegarder la configuration et mettre à jour GRUB")
        save_btn.connect("clicked", self.on_save_clicked)
        footer.append(save_btn)

        self.win.set_content(self.overlay)

    def on_dropdown_setup(self, _factory, list_item):
        """Configure l'élément de liste du menu déroulant."""
        label = Gtk.Label(xalign=0)
        for margin in ["start", "end"]:
            getattr(label, f"set_margin_{margin}")(10)
        for margin in ["top", "bottom"]:
            getattr(label, f"set_margin_{margin}")(5)
        list_item.set_child(label)

    def on_dropdown_bind(self, _factory, list_item):
        """Lie les données à l'élément de liste du menu déroulant."""
        string_obj = list_item.get_item()
        label = list_item.get_child()
        text = string_obj.get_string()
        label.set_text(text)
        orig_text = text if text != "(aucun)" else ""
        label.set_tooltip_text(self.widgets.kernel_descriptions.get(orig_text, "Paramètres personnalisés"))

    def update_dropdown_tooltip(self, dropdown, _pspec):
        """Met à jour la bulle d'aide du menu déroulant."""
        idx = dropdown.get_selected()
        if 0 <= idx < len(self.widgets.kernel_options):
            opt = self.widgets.kernel_options[idx]
            dropdown.set_tooltip_text(self.widgets.kernel_descriptions.get(opt, "Paramètres personnalisés"))

    def on_file_clicked(self, _btn, entry, title):
        """Ouvre un sélecteur de fichier et met à jour l'entrée correspondante."""
        dialog = Gtk.FileDialog(title=title)
        dialog.open(self.win, None, self._on_file_dialog_response, entry)

    def _on_file_dialog_response(self, dialog, result, entry):
        """Gère la réponse du sélecteur de fichier."""
        try:
            file = dialog.open_finish(result)
            if file:
                entry.set_text(file.get_path())
        except gi.repository.GLib.Error:
            pass

    def on_save_clicked(self, _btn):
        """Gère le clic sur le bouton de sauvegarde."""
        # Mettre à jour les données depuis l'UI
        self._update_manager_from_ui()

        # Demander confirmation
        def on_confirm(confirmed):
            if confirmed:
                self._apply_configuration()

        ConfirmDialog(
            self.win,
            "Appliquer la configuration",
            "Êtes-vous sûr de vouloir appliquer ces changements à GRUB ? " "Une sauvegarde sera créée automatiquement.",
            on_confirm,
        )

    def _update_manager_from_ui(self):
        """Met à jour le manager avec les données de l'UI."""
        self.manager.entries["GRUB_DEFAULT"] = self.widgets.entry_ids[self.widgets.default_dropdown.get_selected()]
        self.manager.entries["GRUB_TIMEOUT"] = self.widgets.timeout_entry.get_text()
        self.manager.entries["GRUB_CMDLINE_LINUX_DEFAULT"] = self.widgets.kernel_options[
            self.widgets.kernel_dropdown.get_selected()
        ]

        # Paramètres d'apparence
        self.manager.entries["GRUB_GFXMODE"] = self.widgets.gfxmode_entry.get_text()
        bg = self.widgets.background_entry.get_text()
        if bg:
            self.manager.entries["GRUB_BACKGROUND"] = bg
        else:
            self.manager.entries.pop("GRUB_BACKGROUND", None)

        theme = self.widgets.theme_entry.get_text()
        if theme:
            self.manager.entries["GRUB_THEME"] = theme
        else:
            self.manager.entries.pop("GRUB_THEME", None)

        if bg or theme:
            self.manager.entries["GRUB_TERMINAL_OUTPUT"] = "gfxterm"

        if self.manager.entries["GRUB_DEFAULT"] == "saved":
            self.manager.entries["GRUB_SAVEDEFAULT"] = "true"
        else:
            self.manager.entries.pop("GRUB_SAVEDEFAULT", None)

        self.manager.hidden_entries = [e for e, c in self.widgets.check_buttons.items() if not c.get_active()]

    def _apply_configuration(self):
        """Applique la configuration GRUB."""
        try:
            success, error_msg = self.manager.save_and_apply()
            if success:
                self.show_toast("Configuration appliquée avec succès !")
                logger.info("Configuration GRUB appliquée via UI")
            else:
                self._show_error(
                    "Erreur d'application",
                    f"Impossible d'appliquer la configuration : {error_msg}",
                )
        except Exception as e:
            logger.exception("Erreur inattendue lors de l'application")
            self._show_error("Erreur inattendue", f"Une erreur inattendue s'est produite : {e}")

    def _show_error(self, title: str, message: str, details: Optional[str] = None):
        """Affiche un dialog d'erreur."""
        error_dialog = ErrorDialog(self.win, title, message, details)
        error_dialog.show()

    def on_reset_clicked(self, _btn):
        """Gère le clic sur le bouton de réinitialisation."""

        def on_confirm(confirmed):
            if confirmed:
                self._restore_backup()

        ConfirmDialog(
            self.win,
            "Restaurer la sauvegarde",
            "Êtes-vous sûr de vouloir restaurer la dernière sauvegarde ? "
            "Les changements non sauvegardés seront perdus.",
            on_confirm,
        )

    def _restore_backup(self):
        """Restaure la sauvegarde."""
        try:
            if self.manager.restore_backup():
                self.show_toast("Configuration restaurée avec succès.")
                self._refresh_ui()
                logger.info("Configuration restaurée via UI")
            else:
                self._show_error("Erreur de restauration", "Impossible de restaurer la sauvegarde.")
        except Exception as e:
            logger.exception("Erreur lors de la restauration")
            self._show_error("Erreur inattendue", f"Erreur lors de la restauration : {e}")

    def _refresh_ui(self):
        """Recharge les données et rafraîchit l'interface utilisateur."""
        self.manager.load()
        if self.win:
            self._build_ui()
