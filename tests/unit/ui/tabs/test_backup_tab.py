"""Unit tests for BackupTab (dropdown-based UI)."""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import MagicMock, patch

import pytest

from src.core.dtos import BackupInfoDTO
from src.ui.tabs.backup import BackupTab


@pytest.mark.unit
class TestBackupTab:
    @pytest.fixture
    def app(self) -> MagicMock:
        app = MagicMock()
        app.win = MagicMock()
        app.facade = MagicMock()
        app.facade.menu_entries = []
        app.facade.hidden_entries = []
        app.facade.list_backups.return_value = []
        app.facade.restore_backup.return_value = True
        app.facade.load_config_from_file.return_value = {"GRUB_TIMEOUT": "5"}
        app.show_toast = MagicMock()
        app.reload_config = MagicMock()
        return app

    @pytest.fixture
    def tab(self, app: MagicMock) -> BackupTab:
        return BackupTab(app)

    def test_init_loads_backups(self, app: MagicMock):
        BackupTab(app)
        app.facade.list_backups.assert_called_once()

    def test_load_backups_empty_sets_no_selection_details(self, tab: BackupTab):
        tab.app.facade.list_backups.return_value = []
        tab._load_backups()

        assert tab.backup_paths == []
        tab.details_label.set_text.assert_called_with("Aucune sauvegarde sélectionnée")

    def test_load_backups_puts_original_first(self, tab: BackupTab):
        original = BackupInfoDTO(
            path="/boot/grub/grub.bak.original",
            timestamp=1000.0,
            size_bytes=10,
            is_valid=True,
        )
        recent = BackupInfoDTO(
            path="/tmp/grub.bak.20250101_120000",
            timestamp=2000.0,
            size_bytes=20,
            is_valid=True,
        )
        older = replace(recent, path="/tmp/grub.bak.20240101_120000", timestamp=1500.0)

        tab.app.facade.list_backups.return_value = [older, original, recent]
        tab._load_backups()

        assert tab.backup_paths[0] == original.path
        assert tab.backup_paths[1:] == [recent.path, older.path]
        tab.backup_dropdown.set_selected.assert_called_with(0)

    def test_get_selected_backup_path_non_int_selected_returns_none(self, tab: BackupTab):
        tab.backup_paths = ["/a"]
        tab.backup_dropdown.get_selected = MagicMock(return_value=MagicMock())
        assert tab.get_selected_backup_path() is None

    def test_restore_selected_backup_confirmed_success_reload(self, tab: BackupTab):
        tab.backup_paths = ["/tmp/backup"]
        tab.backup_dropdown.get_selected = MagicMock(return_value=0)

        def confirm_side_effect(*args, **kwargs):
            callback = args[1]
            callback(True)
            return MagicMock()

        with patch("src.ui.tabs.backup.ConfirmDialog", side_effect=confirm_side_effect):
            tab.restore_selected_backup()

        tab.app.facade.restore_backup.assert_called_with("/tmp/backup")
        tab.app.reload_config.assert_called_once()

    def test_restore_selected_backup_confirmed_failure_toast(self, tab: BackupTab):
        tab.backup_paths = ["/tmp/backup"]
        tab.backup_dropdown.get_selected = MagicMock(return_value=0)
        tab.app.facade.restore_backup.return_value = False

        def confirm_side_effect(*args, **kwargs):
            callback = args[1]
            callback(True)
            return MagicMock()

        with patch("src.ui.tabs.backup.ConfirmDialog", side_effect=confirm_side_effect):
            tab.restore_selected_backup()

        tab.app.show_toast.assert_called_with("Échec de la restauration")

    def test_delete_selected_backup_confirmed_removes_file(self, tab: BackupTab):
        tab.backup_paths = ["/tmp/backup"]
        tab.backup_dropdown.get_selected = MagicMock(return_value=0)

        def confirm_side_effect(*args, **kwargs):
            callback = args[1]
            callback(True)
            return MagicMock()

        with (
            patch("src.ui.tabs.backup.ConfirmDialog", side_effect=confirm_side_effect),
            patch("src.ui.tabs.backup.os.remove") as mock_remove,
            patch.object(tab, "_load_backups") as mock_reload,
        ):
            tab.delete_selected_backup()

        mock_remove.assert_called_with("/tmp/backup")
        mock_reload.assert_called_once()

    def test_preview_selected_backup_opens_dialog(self, tab: BackupTab):
        tab.backup_paths = ["/tmp/backup"]
        tab.backup_dropdown.get_selected = MagicMock(return_value=0)

        preview_instance = MagicMock()
        with patch("src.ui.tabs.backup.PreviewDialog", return_value=preview_instance) as mock_preview:
            tab.preview_selected_backup()

        assert mock_preview.called
        preview_instance.present.assert_called_once()

    def test_preview_selected_backup_exception_shows_toast(self, tab: BackupTab):
        tab.backup_paths = ["/tmp/backup"]
        tab.backup_dropdown.get_selected = MagicMock(return_value=0)
        tab.app.facade.load_config_from_file.side_effect = Exception("Boom")

        tab.preview_selected_backup()
        tab.app.show_toast.assert_called()

