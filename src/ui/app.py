"""Application principale GTK pour la gestion de GRUB."""

from src.core.dtos import PreviewConfigDTO
from src.core.exceptions import GrubConfigError
from src.core.facade import GrubFacade
from src.ui.app_state import AppUIState
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
        super().__init__(application_id="com.github.grubutils.GrubManager")
        self.facade = GrubFacade()
        self.logger = logger  # Exposer le logger pour les onglets
        self.ui = AppUIState()

    # pylint: disable=arguments-differ
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
        assert self.ui.overlay is not None
        self.ui.overlay.set_child(box)

        header = self._create_header()
        box.append(header)

        # Barre d'actions en haut
        self._add_action_bar(box)

        stack = self._create_stack(header)

        # Contenu principal
        box.append(stack)

        # Toast notification
        self._setup_toast()

        assert self.ui.win is not None
        self.ui.win.present()

    def _setup_window(self):
        """Configure la fenêtre principale."""
        if not self.ui.win:
            if HAS_ADW:
                self.ui.win = Adw.ApplicationWindow(application=self)
            else:
                self.ui.win = Gtk.ApplicationWindow(application=self)
            self.ui.win.set_title("Grub Customizer (Python)")
            self.ui.win.set_default_size(MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT)

    def _setup_overlay(self):
        """Configure l'overlay pour les notifications."""
        self.ui.overlay = Gtk.Overlay()
        assert self.ui.win is not None
        if HAS_ADW:
            self.ui.win.set_content(self.ui.overlay)
        else:
            self.ui.win.set_child(self.ui.overlay)

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
        self.ui.tabs["general"] = GeneralTab(self)
        stack.add_titled(self.ui.tabs["general"], "general", "Général")

        self.ui.tabs["appearance"] = AppearanceTab(self)
        stack.add_titled(self.ui.tabs["appearance"], "appearance", "Apparence")

        self.ui.tabs["menu"] = MenuTab(self)
        stack.add_titled(self.ui.tabs["menu"], "menu", "Menu")

        self.ui.tabs["backup"] = BackupTab(self)
        stack.add_titled(self.ui.tabs["backup"], "backup", "Sauvegardes")

        # Charger les données dans tous les onglets après leur création
        for tab in self.ui.tabs.values():
            if hasattr(tab, "load_data"):
                tab.load_data()

        # Connecter le changement d'onglet pour gérer la visibilité des boutons
        stack.connect("notify::visible-child-name", self._on_tab_changed)

        return stack

    def _setup_toast(self):
        """Configure le système de notification toast."""
        self.ui.toast_revealer = Gtk.Revealer()
        self.ui.toast_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.ui.toast_revealer.set_valign(Gtk.Align.START)
        self.ui.toast_revealer.set_halign(Gtk.Align.CENTER)
        self.ui.toast_revealer.set_margin_top(10)

        toast_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        toast_box.set_margin_start(20)
        toast_box.set_margin_end(20)
        toast_box.set_margin_top(10)
        toast_box.set_margin_bottom(10)
        toast_box.get_style_context().add_class("osd")  # Style toast-like

        self.ui.toast_label = Gtk.Label()
        toast_box.append(self.ui.toast_label)

        close_btn = Gtk.Button(icon_name="window-close-symbolic")
        close_btn.connect("clicked", lambda _: self.ui.toast_revealer.set_reveal_child(False))
        toast_box.append(close_btn)

        self.ui.toast_revealer.set_child(toast_box)
        assert self.ui.overlay is not None
        self.ui.overlay.add_overlay(self.ui.toast_revealer)

    def show_toast(self, message: str, timeout: int = TOAST_TIMEOUT) -> None:
        """Affiche une notification toast.

        Args:
            message: Message à afficher
            timeout: Durée en ms avant disparition automatique

        """
        if self.ui.toast_label is not None:
            self.ui.toast_label.set_text(message)
        if self.ui.toast_revealer is not None:
            self.ui.toast_revealer.set_reveal_child(True)

        # Masquer automatiquement après le timeout
        def hide_toast():
            if self.ui.toast_revealer is not None:
                self.ui.toast_revealer.set_reveal_child(False)
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
        self.ui.preview_btn = Gtk.Button(label="Aperçu")
        self.ui.preview_btn.set_tooltip_text("Voir l'aperçu de la configuration GRUB")
        self.ui.preview_btn.connect("clicked", self.on_preview_clicked)
        action_bar.append(self.ui.preview_btn)

        # Bouton Défaut
        self.ui.default_btn = Gtk.Button(label="Défaut")
        self.ui.default_btn.set_tooltip_text("Remettre les valeurs par défaut pour cet onglet")
        self.ui.default_btn.connect("clicked", self.on_default_clicked)
        action_bar.append(self.ui.default_btn)

        # Bouton Sauvegarder et Appliquer (visible pour Général, Apparence, Menu)
        self.ui.save_btn = Gtk.Button(label="Sauvegarder et Appliquer")
        self.ui.save_btn.set_tooltip_text("Sauvegarder la configuration et mettre à jour GRUB")
        self.ui.save_btn.add_css_class("suggested-action")
        self.ui.save_btn.connect("clicked", self.on_save_clicked)
        action_bar.append(self.ui.save_btn)

        # Bouton Restaurer (visible pour Backup)
        self.ui.restore_btn = Gtk.Button(label="Restaurer")
        self.ui.restore_btn.set_tooltip_text("Restaurer la sauvegarde sélectionnée")
        self.ui.restore_btn.connect("clicked", self.on_restore_clicked)
        self.ui.restore_btn.set_visible(False)
        action_bar.append(self.ui.restore_btn)

        # Bouton Supprimer (visible pour Backup)
        self.ui.delete_btn = Gtk.Button(label="Supprimer")
        self.ui.delete_btn.set_tooltip_text("Supprimer la sauvegarde sélectionnée")
        self.ui.delete_btn.add_css_class("destructive-action")
        self.ui.delete_btn.connect("clicked", self.on_delete_clicked)
        self.ui.delete_btn.set_visible(False)
        action_bar.append(self.ui.delete_btn)

        # Spacer droit pour centrer
        spacer_r = Gtk.Box()
        spacer_r.set_hexpand(True)
        action_bar.append(spacer_r)

    def _get_current_tab(self):
        """Récupère l'onglet actuellement visible."""
        if not self.ui.overlay:
            return None

        box = self.ui.overlay.get_child()
        if not box:
            return None

        stack = box.get_last_child()
        if not isinstance(stack, Gtk.Stack):
            return None

        visible_name = stack.get_visible_child_name()
        return self.ui.tabs.get(visible_name)

    def _on_stack_switch(self, stack, _param):  # pylint: disable=unused-argument
        """Gère le changement d'onglet pour afficher/masquer les boutons appropriés."""
        # Cette méthode est conservée pour compatibilité mais redirige vers _on_tab_changed
        # qui est connectée directement au signal notify::visible-child-name
        self._on_tab_changed(stack, _param)

    def _on_tab_changed(self, stack, _param):
        """Gère le changement d'onglet pour afficher/masquer les boutons appropriés."""
        # Récupérer le nom de l'enfant visible directement depuis le stack passé en argument
        visible_name = stack.get_visible_child_name()
        current_tab = self.ui.tabs.get(visible_name)

        if current_tab:
            actions = current_tab.get_available_actions()

            assert self.ui.save_btn is not None
            assert self.ui.restore_btn is not None
            assert self.ui.delete_btn is not None
            assert self.ui.preview_btn is not None
            assert self.ui.default_btn is not None

            self.ui.save_btn.set_visible(ActionType.SAVE in actions)
            self.ui.restore_btn.set_visible(ActionType.RESTORE in actions)
            self.ui.delete_btn.set_visible(ActionType.DELETE in actions)
            self.ui.preview_btn.set_visible(ActionType.PREVIEW in actions)
            self.ui.default_btn.set_visible(ActionType.DEFAULT in actions)

        # Reset common properties
        assert self.ui.preview_btn is not None
        assert self.ui.save_btn is not None

        self.ui.preview_btn.set_label("Aperçu")
        self.ui.preview_btn.set_tooltip_text("Voir l'aperçu de la configuration GRUB")
        self.ui.preview_btn.remove_css_class("destructive-action")
        self.ui.preview_btn.set_sensitive(True)

        self.ui.save_btn.set_label("Sauvegarder et Appliquer")
        self.ui.save_btn.set_tooltip_text("Sauvegarder la configuration et mettre à jour GRUB")
        self.ui.save_btn.set_sensitive(True)

        self.update_action_buttons_state()

    def update_action_buttons_state(self) -> None:
        """Met à jour l'état (activé/désactivé) des boutons d'action."""
        current_tab = self._get_current_tab()
        if not current_tab:
            return

        assert self.ui.save_btn is not None
        assert self.ui.restore_btn is not None
        assert self.ui.delete_btn is not None
        assert self.ui.preview_btn is not None
        assert self.ui.default_btn is not None

        # Mettre à jour la sensibilité des boutons en fonction de l'onglet
        self.ui.save_btn.set_sensitive(current_tab.can_perform_action(ActionType.SAVE))
        self.ui.restore_btn.set_sensitive(current_tab.can_perform_action(ActionType.RESTORE))
        self.ui.delete_btn.set_sensitive(current_tab.can_perform_action(ActionType.DELETE))
        self.ui.preview_btn.set_sensitive(current_tab.can_perform_action(ActionType.PREVIEW))
        self.ui.default_btn.set_sensitive(current_tab.can_perform_action(ActionType.DEFAULT))

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
                self.ui.win,
                "Aperçu de la configuration",
                config_dto,
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Erreur lors de l'aperçu: %s", e)
            ErrorDialog(
                self.ui.win,
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
            self.ui.win,
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
        dialog.open(self.ui.win, None, self._on_file_dialog_response, entry)

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
        logger.debug("[UI] Collecte configuration depuis les onglets")
        config = self.facade.entries.copy()

        # Collecter la configuration de chaque onglet
        for tab_name, tab in self.ui.tabs.items():
            if hasattr(tab, "get_config"):
                logger.debug("[UI] Collecte config depuis onglet '%s'", tab_name)
                tab_config = tab.get_config()
                logger.debug("[UI] Onglet '%s' retourne %d entrées", tab_name, len(tab_config))
                config.update(tab_config)

        # Appliquer la logique métier (effets de bord)

        # Gérer savedefault
        if config.get("GRUB_DEFAULT") == "saved":
            config["GRUB_SAVEDEFAULT"] = "true"
        else:
            config.pop("GRUB_SAVEDEFAULT", None)

        # Gérer gfxterm si background ou theme est défini
        bg = config.get("GRUB_BACKGROUND", "")
        theme = config.get("GRUB_THEME", "")

        logger.debug("GRUB_BACKGROUND avant nettoyage: '%s'", bg)

        # Nettoyer les valeurs vides
        # IMPORTANT: On ne supprime PAS la clé, on la garde avec valeur vide
        # pour que le générateur sache qu'il doit supprimer la ligne
        if not bg:
            config["GRUB_BACKGROUND"] = ""
        if not theme:
            config["GRUB_THEME"] = ""

        # Force gfxterm if background, theme, or custom colors are used
        if bg or theme or config.get("GRUB_COLOR_NORMAL") or config.get("GRUB_COLOR_HIGHLIGHT"):
            config["GRUB_TERMINAL_OUTPUT"] = "gfxterm"

        return config

    def _update_manager_from_ui(self):
        """Met à jour le manager avec les données de l'UI."""
        logger.debug("[UI] Mise à jour du gestionnaire depuis l'interface")
        # Récupérer la configuration complète depuis l'UI
        new_config = self._collect_ui_configuration()

        logger.debug("[UI] Configuration collectée: %d entrées", len(new_config))

        # Mettre à jour la façade
        self.facade.entries = new_config
        logger.debug("[UI] Façade mise à jour")

        # Mettre à jour les entrées cachées
        if "menu" in self.ui.tabs:
            self.facade.hidden_entries = self.ui.tabs["menu"].get_hidden_entries()
            logger.debug("[UI] %d entrées de menu cachées", len(self.facade.hidden_entries))

    def _apply_configuration(self):
        """Applique la configuration GRUB."""
        try:
            result = self.facade.apply_changes()
            if result.success:
                # Recharger les entrées de menu depuis grub.cfg après update-grub
                logger.debug("[UI] Rechargement des entrées de menu après apply_changes")
                self.facade.grub_service.menu_entries = self.facade.grub_service.parser.parse_menu_entries()
                logger.debug("[UI] %d entrées de menu rechargées", len(self.facade.menu_entries))

                # Mettre à jour l'onglet menu avec les nouvelles entrées
                if "menu" in self.ui.tabs:
                    self.ui.tabs["menu"].reload_menu_entries()
                    logger.debug("[UI] Onglet Menu mis à jour avec les nouvelles entrées")

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
        if self.ui.toast_revealer:
            self.ui.toast_revealer.set_reveal_child(False)
        return False

    def _show_error(self, title: str, message: str, details: str | None = None) -> None:
        """Affiche un dialog d'erreur."""
        ErrorDialog(
            self.ui.win,
            ErrorOptions(title=title, message=message, details=details),
        )

    def _refresh_ui(self):
        """Recharge les données et rafraîchit l'interface utilisateur."""
        result = self.facade.load_configuration()
        if not result.success:
            logger.error("Failed to load: %s", result.error_details)
        if self.ui.win:
            self._build_ui()

    def reload_config(self) -> None:
        """Recharge la configuration après une restauration de backup.

        Alias pour _refresh_ui() exposé publiquement pour les onglets.
        """
        self._refresh_ui()
