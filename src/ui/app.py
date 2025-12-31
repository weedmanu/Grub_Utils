"""Application principale GTK pour la gestion de GRUB."""

from src.core.exceptions import GrubConfigError
from src.core.facade import GrubFacade
from src.ui.dialogs.backup_selector_dialog import BackupSelectorDialog
from src.ui.dialogs.confirm_dialog import ConfirmDialog, ConfirmOptions
from src.ui.dialogs.error_dialog import ErrorDialog, ErrorOptions
from src.ui.dialogs.preview_dialog import PreviewDialog
from src.ui.gtk_init import HAS_ADW, Adw, GLib, Gtk
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
        self.facade = GrubFacade()
        self.win = None
        self.tabs = {}
        self.overlay = None
        self.toast_revealer = None
        self.toast_label = None

    def do_activate(self, *_args, **_kwargs):  # vulture: ignore
        """Active l'application et construit l'interface utilisateur."""
        result = self.facade.load_configuration()
        if not result.success:
            logger.error("Failed to load: %s", result.error_details)
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

        # Overlay pour les notifications (parent de la hiérarchie)
        self.overlay = Gtk.Overlay()

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.overlay.set_child(box)

        if HAS_ADW:
            self.win.set_content(self.overlay)
            header = Adw.HeaderBar()
        else:
            self.win.set_child(self.overlay)
            header = Gtk.HeaderBar()
        box.append(header)

        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        stack_switcher = Gtk.StackSwitcher(stack=stack)
        header.set_title_widget(stack_switcher)

        # Initialisation des onglets
        self.tabs["general"] = GeneralTab(self)
        stack.add_titled(self.tabs["general"], "general", "Général")

        self.tabs["appearance"] = AppearanceTab(self)
        stack.add_titled(self.tabs["appearance"], "appearance", "Apparence")

        self.tabs["menu"] = MenuTab(self)
        stack.add_titled(self.tabs["menu"], "menu", "Menu")

        self._add_footer(box)
        box.append(stack)

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

        self.win.present()

    def show_toast(self, message: str, timeout: int = TOAST_TIMEOUT):
        """Affiche une notification toast.

        Args:
            message: Message à afficher
            timeout: Durée en ms avant disparition automatique

        """
        if self.toast_label is not None:
            self.toast_label.set_text(message)
        if self.toast_revealer is not None:
            self.toast_revealer.set_reveal_child(True)

        # Masquer automatiquement après le timeout
        def hide_toast():
            if self.toast_revealer is not None:
                self.toast_revealer.set_reveal_child(False)
            return False  # Ne pas répéter

        # Convertir ms en secondes pour GLib.timeout_add
        GLib.timeout_add(timeout, hide_toast)

    def _add_footer(self, box: Gtk.Box) -> None:
        """Add footer with action buttons."""
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        for margin in ["top", "bottom", "start", "end"]:
            getattr(footer, f"set_margin_{margin}")(10)
        box.append(footer)

        reset_btn = Gtk.Button(label="Réinitialiser")
        reset_btn.set_tooltip_text("Restaurer la dernière sauvegarde de configuration")
        reset_btn.connect("clicked", self.on_reset_clicked)
        footer.append(reset_btn)

        preview_btn = Gtk.Button(label="Aperçu")
        preview_btn.set_tooltip_text("Voir l'aperçu de la configuration GRUB")
        preview_btn.connect("clicked", self.on_preview_clicked)
        footer.append(preview_btn)

        save_btn = Gtk.Button(label="Sauvegarder et Appliquer", hexpand=True)
        save_btn.set_tooltip_text("Sauvegarder la configuration et mettre à jour GRUB")
        save_btn.connect("clicked", self.on_save_clicked)
        footer.append(save_btn)

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
        except GLib.Error:
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
            on_confirm,
            ConfirmOptions(
                title="Appliquer la configuration",
                message=(
                    "Êtes-vous sûr de vouloir appliquer ces changements à GRUB ? "
                    "Une sauvegarde sera créée automatiquement."
                ),
            ),
        )

    def _collect_ui_configuration(self) -> dict[str, str]:
        """Collect modified values from the UI widgets.

        Returns:
            Dictionnaire avec la configuration modifiée depuis les onglets UI

        """
        config = self.facade.entries.copy()

        # Collecter la configuration de chaque onglet
        for tab in self.tabs.values():
            if hasattr(tab, "get_config"):
                config.update(tab.get_config())

        # Appliquer la logique métier (effets de bord)
        
        # Gérer savedefault
        if config.get("GRUB_DEFAULT") == "saved":
            config["GRUB_SAVEDEFAULT"] = "true"
        else:
            config.pop("GRUB_SAVEDEFAULT", None)

        # Gérer gfxterm si background ou theme est défini
        bg = config.get("GRUB_BACKGROUND", "")
        theme = config.get("GRUB_THEME", "")
        
        # Nettoyer les valeurs vides
        if not bg:
            config.pop("GRUB_BACKGROUND", None)
        if not theme:
            config.pop("GRUB_THEME", None)

        if bg or theme:
            config["GRUB_TERMINAL_OUTPUT"] = "gfxterm"

        return config

    def _update_manager_from_ui(self):
        """Met à jour le manager avec les données de l'UI."""
        # Récupérer la configuration complète depuis l'UI
        new_config = self._collect_ui_configuration()
        
        # Mettre à jour la façade
        self.facade.entries = new_config

        # Mettre à jour les entrées cachées
        if "menu" in self.tabs:
            self.facade.hidden_entries = self.tabs["menu"].get_hidden_entries()

    def _apply_configuration(self):
        """Applique la configuration GRUB."""
        try:
            result = self.facade.apply_changes()
            if result.success:
                self.show_toast("Configuration appliquée avec succès !")
                logger.info("Configuration GRUB appliquée via UI")
            else:
                self._show_error(
                    "Erreur d'application",
                    f"Impossible d'appliquer la configuration : {result.error_details}",
                )
        except GrubConfigError as e:
            logger.exception("Erreur de configuration")
            self._show_error("Erreur de configuration", f"Erreur de configuration : {e}")
        except OSError as e:
            logger.exception("Erreur d'accès fichier")
            self._show_error("Erreur d'accès", f"Erreur d'accès au fichier : {e}")
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.exception("Erreur inattendue lors de l'application")
            self._show_error("Erreur inattendue", f"Une erreur inattendue s'est produite : {e}")

    def _show_error(self, title: str, message: str, details: str | None = None) -> None:
        """Affiche un dialog d'erreur."""
        ErrorDialog(
            self.win,
            ErrorOptions(title=title, message=message, details=details),
        )

    def on_reset_clicked(self, _btn):
        """Gère le clic sur le bouton de réinitialisation."""
        try:
            if not self.facade.has_backups():
                self.show_toast("Aucune sauvegarde disponible à restaurer.")
                return

            # Get list of backups
            backups_info = self.facade.list_backups()
            if not backups_info:
                self.show_toast("Aucune sauvegarde disponible.")
                return

            # Extract paths from BackupInfoDTO
            backup_paths = [backup.path for backup in backups_info]

            # Show backup selector dialog
            BackupSelectorDialog(self.win, backup_paths, self._on_backup_selected)

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.exception("Erreur lors de la sélection de sauvegarde")
            self._show_error("Erreur", f"Impossible de lister les sauvegardes : {e}")

    def _on_backup_selected(self, backup_path: str | None):
        """Handle backup selection from dialog.

        Args:
            backup_path: Selected backup path or None if cancelled

        """
        if backup_path:
            self._restore_backup(backup_path)

    def _restore_backup(self, backup_path: str | None = None):
        """Restaure la sauvegarde.

        Args:
            backup_path: Path to backup to restore, or None for latest

        """
        try:
            result = self.facade.restore_backup(backup_path)
            if result.success:
                self.show_toast("Configuration restaurée avec succès.")
                self._refresh_ui()
                logger.info("Configuration restaurée via UI: %s", backup_path or "latest")
            else:
                self._show_error("Erreur de restauration", "Impossible de restaurer la sauvegarde.")
        except OSError as e:
            logger.exception("Erreur d'accès fichier lors de la restauration")
            self._show_error("Erreur d'accès", f"Erreur lors de la restauration : {e}")
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.exception("Erreur lors de la restauration")
            self._show_error("Erreur inattendue", f"Erreur lors de la restauration : {e}")

    def _refresh_ui(self):
        """Recharge les données et rafraîchit l'interface utilisateur."""
        result = self.facade.load_configuration()
        if not result.success:
            logger.error("Failed to load: %s", result.error_details)
        if self.win:
            self._build_ui()

    def on_preview_clicked(self, _button: Gtk.Button) -> None:
        """Affiche un aperçu de la configuration avant sauvegarde.

        Args:
            _button: Bouton cliqué

        """
        try:
            current_config = self.facade.entries
            modified_config = self._collect_ui_configuration()

            if current_config == modified_config:
                self.show_toast("Aucun changement à prévisualiser.")
                return

            menu_entries = [
                {"title": e.title, "linux": e.description}
                for e in self.facade.get_menu_entries()
            ]
            
            # Get current hidden entries from UI widgets
            hidden_entries = []
            if "menu" in self.tabs:
                hidden_entries = self.tabs["menu"].get_hidden_entries()

            PreviewDialog(
                self.win,
                "Aperçu de la configuration",
                current_config,
                modified_config,
                menu_entries,
                hidden_entries
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.exception("Erreur lors de l'affichage de l'aperçu")
            self._show_error("Erreur", f"Impossible d'afficher l'aperçu : {e}")
