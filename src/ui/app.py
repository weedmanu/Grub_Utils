"""Application principale GTK pour la gestion de GRUB."""

from src.core.dtos import PreviewConfigDTO
from src.core.exceptions import GrubConfigError
from src.core.facade import GrubFacade
from src.ui.dialogs.confirm_dialog import ConfirmDialog, ConfirmOptions
from src.ui.dialogs.error_dialog import ErrorDialog, ErrorOptions
from src.ui.dialogs.preview_dialog import PreviewDialog
from src.ui.enums import ActionType
from src.ui.gtk_init import HAS_ADW, Adw, GLib, Gtk
from src.ui.tabs.appearance import AppearanceTab
from src.ui.tabs.backup import BackupTab
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
        self.logger = logger  # Exposer le logger pour les onglets
        self.win = None
        self.tabs = {}
        self.overlay = None
        self.toast_revealer = None
        self.toast_label = None

        # UI Components initialized later
        self.preview_btn = None
        self.default_btn = None
        self.save_btn = None
        self.restore_btn = None
        self.delete_btn = None

    def run(self, argv: list[str] | None = None) -> int:
        """Lance l'application GTK.

        Args:
            argv: Arguments de ligne de commande

        Returns:
            Code de sortie de l'application

        """
        # Appeler la méthode run() de la classe parent Gtk.Application
        return super().run(argv)

    def do_activate(self, *_args, **_kwargs):  # vulture: ignore
        """Active l'application et construit l'interface utilisateur."""
        # Créer le backup original si nécessaire (premier lancement)
        try:
            created = self.facade.ensure_original_backup()
            if created:
                logger.info("Backup original créé lors du premier lancement")
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.warning("Impossible de créer le backup original: %s", e)

        result = self.facade.load_configuration()
        if not result.success:
            logger.error("Failed to load: %s", result.error_details)
        self._build_ui()

    def _build_ui(self):
        """Construit les composants de l'interface."""
        self._setup_window()
        self._setup_overlay()

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.overlay.set_child(box)

        header = self._create_header()
        box.append(header)

        # Barre d'actions en haut
        self._add_action_bar(box)

        stack = self._create_stack(header)

        # Contenu principal
        box.append(stack)

        # Toast notification
        self._setup_toast()

        self.win.present()

    def _setup_window(self):
        """Configure la fenêtre principale."""
        if not self.win:
            if HAS_ADW:
                self.win = Adw.ApplicationWindow(application=self)
            else:
                self.win = Gtk.ApplicationWindow(application=self)
            self.win.set_title("Grub Customizer (Python)")
            self.win.set_default_size(MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT)

    def _setup_overlay(self):
        """Configure l'overlay pour les notifications."""
        self.overlay = Gtk.Overlay()
        if HAS_ADW:
            self.win.set_content(self.overlay)
        else:
            self.win.set_child(self.overlay)

    def _create_header(self):
        """Crée la barre d'en-tête."""
        if HAS_ADW:
            return Adw.HeaderBar()
        return Gtk.HeaderBar()

    def _create_stack(self, header):
        """Crée et configure le stack de navigation."""
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

        self.tabs["backup"] = BackupTab(self)
        stack.add_titled(self.tabs["backup"], "backup", "Sauvegardes")

        # Connecter le changement d'onglet pour gérer la visibilité des boutons
        stack.connect("notify::visible-child-name", self._on_tab_changed)

        return stack

    def _setup_toast(self):
        """Configure le système de notification toast."""
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

    def show_toast(self, message: str, timeout: int = TOAST_TIMEOUT) -> None:
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

    def _add_action_bar(self, box: Gtk.Box) -> None:
        """Add action bar with action buttons."""
        action_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        for margin in ["top", "bottom", "start", "end"]:
            getattr(action_bar, f"set_margin_{margin}")(10)
        box.append(action_bar)

        # Spacer gauche pour centrer
        spacer_l = Gtk.Box()
        spacer_l.set_hexpand(True)
        action_bar.append(spacer_l)

        # Bouton Aperçu (visible pour Général, Apparence, Menu)
        self.preview_btn = Gtk.Button(label="Aperçu")
        self.preview_btn.set_tooltip_text("Voir l'aperçu de la configuration GRUB")
        self.preview_btn.connect("clicked", self.on_preview_clicked)
        action_bar.append(self.preview_btn)

        # Bouton Défaut
        self.default_btn = Gtk.Button(label="Défaut")
        self.default_btn.set_tooltip_text("Remettre les valeurs par défaut pour cet onglet")
        self.default_btn.connect("clicked", self.on_default_clicked)
        action_bar.append(self.default_btn)

        # Bouton Sauvegarder et Appliquer (visible pour Général, Apparence, Menu)
        self.save_btn = Gtk.Button(label="Sauvegarder et Appliquer")
        self.save_btn.set_tooltip_text("Sauvegarder la configuration et mettre à jour GRUB")
        self.save_btn.add_css_class("suggested-action")
        self.save_btn.connect("clicked", self.on_save_clicked)
        action_bar.append(self.save_btn)

        # Bouton Restaurer (visible pour Backup)
        self.restore_btn = Gtk.Button(label="Restaurer")
        self.restore_btn.set_tooltip_text("Restaurer la sauvegarde sélectionnée")
        self.restore_btn.connect("clicked", self.on_restore_clicked)
        self.restore_btn.set_visible(False)
        action_bar.append(self.restore_btn)

        # Bouton Supprimer (visible pour Backup)
        self.delete_btn = Gtk.Button(label="Supprimer")
        self.delete_btn.set_tooltip_text("Supprimer la sauvegarde sélectionnée")
        self.delete_btn.add_css_class("destructive-action")
        self.delete_btn.connect("clicked", self.on_delete_clicked)
        self.delete_btn.set_visible(False)
        action_bar.append(self.delete_btn)

        # Spacer droit pour centrer
        spacer_r = Gtk.Box()
        spacer_r.set_hexpand(True)
        action_bar.append(spacer_r)

    def _get_current_tab(self):
        """Récupère l'onglet actuellement visible."""
        if not self.overlay:
            return None

        box = self.overlay.get_child()
        if not box:
            return None

        stack = box.get_last_child()
        if not isinstance(stack, Gtk.Stack):
            return None

        visible_name = stack.get_visible_child_name()
        return self.tabs.get(visible_name)

    def _on_stack_switch(self, stack, _param):  # pylint: disable=unused-argument
        """Gère le changement d'onglet pour afficher/masquer les boutons appropriés."""
        # Cette méthode est conservée pour compatibilité mais redirige vers _on_tab_changed
        # qui est connectée directement au signal notify::visible-child-name
        self._on_tab_changed(stack, _param)

    def _on_tab_changed(self, stack, _param):
        """Gère le changement d'onglet pour afficher/masquer les boutons appropriés."""
        # Récupérer le nom de l'enfant visible directement depuis le stack passé en argument
        visible_name = stack.get_visible_child_name()
        current_tab = self.tabs.get(visible_name)

        if current_tab:
            actions = current_tab.get_available_actions()

            self.save_btn.set_visible(ActionType.SAVE in actions)
            self.restore_btn.set_visible(ActionType.RESTORE in actions)
            self.delete_btn.set_visible(ActionType.DELETE in actions)
            self.preview_btn.set_visible(ActionType.PREVIEW in actions)
            self.default_btn.set_visible(ActionType.DEFAULT in actions)

        # Reset common properties
        self.preview_btn.set_label("Aperçu")
        self.preview_btn.set_tooltip_text("Voir l'aperçu de la configuration GRUB")
        self.preview_btn.remove_css_class("destructive-action")
        self.preview_btn.set_sensitive(True)

        self.save_btn.set_label("Sauvegarder et Appliquer")
        self.save_btn.set_tooltip_text("Sauvegarder la configuration et mettre à jour GRUB")
        self.save_btn.set_sensitive(True)

        self.update_action_buttons_state()

    def update_action_buttons_state(self) -> None:
        """Met à jour l'état (activé/désactivé) des boutons d'action."""
        current_tab = self._get_current_tab()
        if not current_tab:
            return

        # Mettre à jour la sensibilité des boutons en fonction de l'onglet
        self.save_btn.set_sensitive(current_tab.can_perform_action(ActionType.SAVE))
        self.restore_btn.set_sensitive(current_tab.can_perform_action(ActionType.RESTORE))
        self.delete_btn.set_sensitive(current_tab.can_perform_action(ActionType.DELETE))
        self.preview_btn.set_sensitive(current_tab.can_perform_action(ActionType.PREVIEW))
        self.default_btn.set_sensitive(current_tab.can_perform_action(ActionType.DEFAULT))

    def on_preview_clicked(self, _btn) -> None:
        """Gère le clic sur le bouton Aperçu."""
        try:
            current_tab = self._get_current_tab()

            # Laisser l'onglet gérer l'aperçu s'il le souhaite (ex: BackupTab)
            if current_tab and current_tab.on_action(ActionType.PREVIEW):
                return

            # Sinon, comportement par défaut (Aperçu global de la configuration)
            new_config = self._collect_ui_configuration()
            old_config = self.facade.entries

            config_dto = PreviewConfigDTO(
                old_config=old_config,
                new_config=new_config,
                menu_entries=self.facade.menu_entries,
            )
            PreviewDialog(
                self.win,
                "Aperçu de la configuration",
                config_dto,
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Erreur lors de l'aperçu: %s", e)
            ErrorDialog(
                self.win,
                ErrorOptions(
                    title="Erreur",
                    message=f"Impossible d'afficher l'aperçu: {e}",
                ),
            ).present()

    def on_save_clicked(self, _btn) -> None:
        """Gère le clic sur le bouton Sauvegarder."""
        # Logique originale de save
        self._update_manager_from_ui()

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

    def on_delete_clicked(self, _btn) -> None:
        """Gère le clic sur le bouton Supprimer (Backup)."""
        current_tab = self._get_current_tab()
        if current_tab:
            current_tab.on_action(ActionType.DELETE)

    def on_restore_clicked(self, _btn) -> None:
        """Gère le clic sur le bouton Restaurer (Backup)."""
        current_tab = self._get_current_tab()
        if current_tab:
            current_tab.on_action(ActionType.RESTORE)

    def on_default_clicked(self, _btn):
        """Gère le clic sur le bouton Défaut."""
        current_tab = self._get_current_tab()
        if current_tab:
            current_tab.on_action(ActionType.DEFAULT)

    def on_file_clicked(self, _btn, entry, title) -> None:
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

        # Force gfxterm if background, theme, or custom colors are used
        if bg or theme or config.get("GRUB_COLOR_NORMAL") or config.get("GRUB_COLOR_HIGHLIGHT"):
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

    def _hide_toast(self) -> bool:
        """Masque le toast.

        Returns:
            False pour arrêter le timeout

        """
        if self.toast_revealer:
            self.toast_revealer.set_reveal_child(False)
        return False

    def _show_error(self, title: str, message: str, details: str | None = None) -> None:
        """Affiche un dialog d'erreur."""
        ErrorDialog(
            self.win,
            ErrorOptions(title=title, message=message, details=details),
        )

    def _refresh_ui(self):
        """Recharge les données et rafraîchit l'interface utilisateur."""
        result = self.facade.load_configuration()
        if not result.success:
            logger.error("Failed to load: %s", result.error_details)
        if self.win:
            self._build_ui()

    def reload_config(self) -> None:
        """Recharge la configuration après une restauration de backup.

        Alias pour _refresh_ui() exposé publiquement pour les onglets.
        """
        self._refresh_ui()
