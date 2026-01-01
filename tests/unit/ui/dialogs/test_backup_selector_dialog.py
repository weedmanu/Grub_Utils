from unittest.mock import MagicMock, patch

import pytest

from src.ui.dialogs.backup_selector_dialog import BackupSelectorDialog


class TestBackupSelectorDialog:
    def test_init(self):
        parent = MagicMock()
        backups = ["/path/to/backup1", "/path/to/backup2"]
        callback = MagicMock()

        # We expect this to fail if the code is broken
        try:
            dialog = BackupSelectorDialog(parent, backups, callback)
        except AttributeError as e:
            pytest.fail(f"Initialization failed: {e}")
        assert dialog is not None

    def test_create_backup_row(self):
        # We need to mock os.path.getmtime and getsize
        with patch("os.path.getmtime") as mock_mtime, patch("os.path.getsize") as mock_size:
            mock_mtime.return_value = 1600000000
            mock_size.return_value = 1024

            # We need an instance. Since init is "broken" but works with mocks, we can use it.
            parent = MagicMock()
            backups = ["/path/to/backup1"]
            callback = MagicMock()
            dialog = BackupSelectorDialog(parent, backups, callback)

            row = dialog._create_backup_row("/path/to/backup1")
            assert row is not None

    def test_create_backup_row_os_error(self):
        with patch("os.path.getmtime", side_effect=OSError):
            parent = MagicMock()
            backups = ["/path/to/backup1"]
            callback = MagicMock()
            dialog = BackupSelectorDialog(parent, backups, callback)

            row = dialog._create_backup_row("/path/to/backup1")
            assert row is not None

    def test_on_row_selected(self):
        parent = MagicMock()
        backups = ["/path/to/backup1", "/path/to/backup2"]
        callback = MagicMock()
        dialog = BackupSelectorDialog(parent, backups, callback)

        mock_row = MagicMock()
        mock_row.get_index.return_value = 1

        dialog._on_row_selected(None, mock_row)

        assert dialog.selected_backup == "/path/to/backup2"

    def test_on_cancel_with_callback(self):
        """Test _on_cancel calls the callback with None."""
        parent = MagicMock()
        backups = ["/path/to/backup1"]
        callback = MagicMock()
        dialog = BackupSelectorDialog(parent, backups, callback)

        with patch.object(dialog, "close"):
            dialog._on_cancel()
            callback.assert_called_with(None)
            dialog.close.assert_called_once()

    def test_on_cancel_without_callback(self):
        """Test _on_cancel handles missing callback gracefully."""
        parent = MagicMock()
        backups = ["/path/to/backup1"]
        dialog = BackupSelectorDialog(parent, backups, None)

        with patch.object(dialog, "close"):
            # Should not raise an error even without callback
            dialog._on_cancel()
            dialog.close.assert_called_once()

    def test_on_restore_with_callback(self):
        """Test _on_restore calls the callback with selected backup."""
        parent = MagicMock()
        backups = ["/path/to/backup1", "/path/to/backup2"]
        callback = MagicMock()
        dialog = BackupSelectorDialog(parent, backups, callback)
        dialog.selected_backup = "/path/to/backup2"

        with patch.object(dialog, "close"):
            dialog._on_restore()
            callback.assert_called_with("/path/to/backup2")
            dialog.close.assert_called_once()

    def test_on_restore_without_callback(self):
        """Test _on_restore handles missing callback gracefully."""
        parent = MagicMock()
        backups = ["/path/to/backup1"]
        dialog = BackupSelectorDialog(parent, backups, None)
        dialog.selected_backup = "/path/to/backup1"

        with patch.object(dialog, "close"):
            # Should not raise an error even without callback
            dialog._on_restore()
            dialog.close.assert_called_once()
