"""Module pour l'onglet de gestion des sauvegardes."""

import os
from datetime import datetime

from src.core.dtos import PreviewConfigDTO
from src.core.exceptions import GrubBackupError
from src.ui.dialogs.confirm_dialog import ConfirmDialog, ConfirmOptions
from src.ui.dialogs.preview_dialog import PreviewDialog
from src.ui.enums import ActionType
from src.ui.gtk_init import Gtk
from src.ui.tabs.base import BaseTab


class BackupTab(BaseTab):
    """Classe pour l'onglet de gestion des sauvegardes."""

    def get_available_actions(self) -> set[ActionType]:
        """Retourne les actions spécifiques à l'onglet Backup."""
        return {ActionType.RESTORE, ActionType.DELETE, ActionType.PREVIEW, ActionType.DEFAULT}

    def can_perform_action(self, action: ActionType) -> bool:
        """Vérifie si l'action est possible (sélection requise pour certaines)."""
        if action in {ActionType.RESTORE, ActionType.DELETE, ActionType.PREVIEW}:
            return self.has_selection()
        return True

    def on_action(self, action: ActionType) -> bool:
        """Gère les actions spécifiques."""
        if action == ActionType.RESTORE:
            self.restore_selected_backup()
            return True
        if action == ActionType.DELETE:
            self.delete_selected_backup()
            return True
        if action == ActionType.DEFAULT:
            self.restore_defaults()
            return True
        if action == ActionType.PREVIEW:
            self.preview_selected_backup()
            return True
        return False

    def preview_selected_backup(self):
        """Affiche l'aperçu du backup sélectionné."""
        path = self.get_selected_backup_path()
        if path:
            try:
                backup_config = self.app.facade.load_config_from_file(path)
                config_dto = PreviewConfigDTO(
                    old_config=backup_config,
                    new_config=backup_config,
                    menu_entries=self.app.facade.menu_entries,
                    hidden_entries=self.app.facade.hidden_entries,
                )
                PreviewDialog(
                    self.app.win,
                    f"Aperçu : {os.path.basename(path)}",
                    config_dto,
                ).present()
            except Exception as e:  # pylint: disable=broad-exception-caught
                self.app.show_toast(f"Erreur : {e}")
        else:
            self.app.show_toast("Veuillez sélectionner une sauvegarde")

    def __init__(self, app):
        """Initialise l'onglet avec une référence à l'application."""
        super().__init__(app)

        # Label
        self.grid.attach(Gtk.Label(label="Sauvegarde :", xalign=0), 0, 0, 1, 1)

        # Dropdown
        self.backup_dropdown = Gtk.DropDown()
        self.backup_dropdown.set_hexpand(True)
        self.grid.attach(self.backup_dropdown, 1, 0, 1, 1)

        # Zone d'info (comme dans GeneralTab)
        info_frame = Gtk.Frame(label="Détails")
        info_frame.set_margin_top(20)

        info_box = self.create_info_box()
        info_frame.set_child(info_box)

        self.details_label = Gtk.Label(xalign=0, wrap=True)
        info_box.append(self.details_label)

        self.append(info_frame)

        self.backup_paths = []
        self.backups_info = {}  # path -> info dto

        self.backup_dropdown.connect("notify::selected", self._on_selection_changed)

        self._load_backups()

    def _load_backups(self):
        backups = self.app.facade.list_backups()
        self.backup_paths = []
        self.backups_info = {b.path: b for b in backups}
        display_names = []

        # Find original
        original = next(
            (b for b in backups if b.path.endswith("grub.prime-backup") or b.path.endswith("grub.bak.original")), None
        )
        others = [b for b in backups if b != original]
        others.sort(key=lambda x: x.timestamp, reverse=True)

        if original:
            self.backup_paths.append(original.path)
            display_names.append("Configuration Originale (Défaut)")

        for b in others:
            self.backup_paths.append(b.path)
            name = os.path.basename(b.path)
            date = datetime.fromtimestamp(b.timestamp).strftime("%d/%m/%Y %H:%M")
            display_names.append(f"{name} ({date})")

        model = Gtk.StringList()
        for name in display_names:
            model.append(name)
        self.backup_dropdown.set_model(model)

        if original:
            self.backup_dropdown.set_selected(0)
        elif self.backup_paths:
            self.backup_dropdown.set_selected(0)

        self._update_details()

    def _on_selection_changed(self, *_args):
        self._update_details()
        if hasattr(self.app, "update_action_buttons_state"):
            self.app.update_action_buttons_state()

    def _update_details(self):
        path = self.get_selected_backup_path()
        if path and path in self.backups_info:
            info = self.backups_info[path]
            size_kb = info.size_bytes / 1024
            date_str = datetime.fromtimestamp(info.timestamp).strftime("%d/%m/%Y à %H:%M:%S")

            is_original = path.endswith("grub.prime-backup") or path.endswith("grub.bak.original")

            text = f"<b>Fichier :</b> {os.path.basename(path)}\n"
            text += f"<b>Date :</b> {date_str}\n"
            text += f"<b>Taille :</b> {size_kb:.1f} Ko"

            if is_original:
                text += "\n\n<i>Ceci est la configuration initiale de GRUB.</i>"

            self.details_label.set_markup(text)
        else:
            self.details_label.set_text("Aucune sauvegarde sélectionnée")

    def get_selected_backup_path(self) -> str | None:
        """Get the path of the currently selected backup."""
        idx = self.backup_dropdown.get_selected()
        if not isinstance(idx, int):
            return None
        if 0 <= idx < len(self.backup_paths):
            return self.backup_paths[idx]
        return None

    def has_selection(self) -> bool:
        """Check if a backup is selected."""
        return self.get_selected_backup_path() is not None

    def delete_selected_backup(self):
        """Delete the currently selected backup."""
        self._on_delete_clicked(None)

    def restore_selected_backup(self):
        """Restore the currently selected backup."""
        self._on_restore_clicked(None)

    def _on_delete_clicked(self, _btn):
        path = self.get_selected_backup_path()
        if not path:
            return

        filename = os.path.basename(path)

        # Demander confirmation

        def on_confirm(confirmed):
            if confirmed:
                try:
                    os.remove(path)
                    self.app.show_toast(f"Sauvegarde '{filename}' supprimée")
                    self._load_backups()
                except (OSError, ValueError) as e:
                    self.app.logger.exception("Erreur lors de la suppression")
                    self.app.show_toast(f"Erreur: {e}")

        ConfirmDialog(
            self.app.win,
            on_confirm,
            ConfirmOptions(
                title="Confirmer la suppression",
                message=(
                    f"Voulez-vous vraiment supprimer la sauvegarde '{filename}' ?\n\n" "Cette action est irréversible."
                ),
            ),
        )

    def _on_restore_clicked(self, _btn):
        path = self.get_selected_backup_path()
        if not path:
            return

        filename = os.path.basename(path)

        # Demander confirmation

        def on_confirm(confirmed):
            if confirmed:
                try:
                    success = self.app.facade.restore_backup(path)
                    if success:
                        self.app.show_toast(f"Configuration restaurée depuis '{filename}'")
                        # Recharger l'application
                        self.app.reload_config()
                    else:
                        self.app.show_toast("Échec de la restauration")
                except (GrubBackupError, OSError, ValueError) as e:
                    self.app.logger.exception("Erreur lors de la restauration")
                    self.app.show_toast(f"Erreur: {e}")

        ConfirmDialog(
            self.app.win,
            on_confirm,
            ConfirmOptions(
                title="Confirmer la restauration",
                message=f"Voulez-vous restaurer la configuration depuis '{filename}' ?\n\n"
                f"La configuration actuelle sera sauvegardée avant la restauration.",
            ),
        )

    def restore_defaults(self):
        """Sélectionne le backup original dans la liste (position par défaut)."""
        if self.backup_paths:
            self.backup_dropdown.set_selected(0)
            self.app.show_toast("Sélection réinitialisée")

    def get_config(self) -> dict[str, str]:
        """Récupère la configuration (vide pour cet onglet).

        Returns:
            dict[str, str]: Configuration vide (lecture seule)

        """
        return {}
