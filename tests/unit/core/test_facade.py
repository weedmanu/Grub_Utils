"""Unit tests for GrubFacade."""

from unittest.mock import Mock, patch

import pytest

from src.core.facade import GrubFacade


@pytest.mark.unit
class TestGrubFacade:
    """Test suite for GrubFacade."""

    @pytest.fixture
    def facade(self):
        """Create a GrubFacade instance with mocked service.

        Returns:
            GrubFacade instance

        """
        with patch("src.core.facade.GrubService") as mock_service_class:
            mock_service = Mock()
            mock_service.entries = {
                "GRUB_DEFAULT": "0",
                "GRUB_TIMEOUT": "5",
                "GRUB_CMDLINE_LINUX_DEFAULT": "quiet splash",
                "GRUB_GFXMODE": "auto",
            }
            mock_service.menu_entries = []
            mock_service_class.return_value = mock_service

            facade = GrubFacade()
            facade._service = mock_service
            return facade

    def test_load_configuration_success(self, facade):
        """Test successful configuration loading."""
        facade._service.load = Mock()

        result = facade.load_configuration()

        assert result.success is True
        assert "successfully" in result.message.lower()
        facade._service.load.assert_called_once()

    def test_load_configuration_failure(self, facade):
        """Test configuration loading failure."""
        from src.core.exceptions import GrubServiceError

        facade._service.load = Mock(side_effect=GrubServiceError("File not found"))

        result = facade.load_configuration()

        assert result.success is False
        assert result.error_details == "File not found"

    def test_apply_changes_success(self, facade):
        """Test successful changes application."""
        facade._loaded = True
        facade._service.save_and_apply = Mock(return_value=(True, ""))

        result = facade.apply_changes()

        assert result.success is True
        facade._service.save_and_apply.assert_called_once()

    def test_apply_changes_failure(self, facade):
        """Test failed changes application."""
        facade._loaded = True
        facade._service.save_and_apply = Mock(return_value=(False, "Permission denied"))

        result = facade.apply_changes()

        assert result.success is False
        assert result.error_details == "Permission denied"

    def test_list_backups(self, facade, tmp_path):
        """Test listing backups."""
        # Create fake backup files
        backup1 = tmp_path / "grub.bak.001"
        backup2 = tmp_path / "grub.bak.002"
        backup1.write_text("config1")
        backup2.write_text("config2")

        facade._service.backup_manager.list_backups = Mock(return_value=[str(backup1), str(backup2)])

        backups = facade.list_backups()

        assert len(backups) == 2
        assert all(b.is_valid for b in backups)
        assert all(b.size_bytes > 0 for b in backups)

    def test_restore_backup_success(self, facade):
        """Test successful backup restoration."""
        facade._service.restore_backup = Mock(return_value=True)

        result = facade.restore_backup("/path/to/backup")

        assert result.success is True
        facade._service.restore_backup.assert_called_once_with("/path/to/backup")

    def test_restore_backup_failure(self, facade):
        """Test failed backup restoration."""
        facade._service.restore_backup = Mock(return_value=False)

        result = facade.restore_backup()

        assert result.success is False

    def test_restore_backup_exception(self, facade):
        """Test backup restoration with exception."""
        from src.core.exceptions import GrubServiceError

        facade._service.restore_backup = Mock(side_effect=GrubServiceError("Backup error"))

        result = facade.restore_backup("/path/to/backup")

        assert result.success is False
        assert "Backup error" in result.error_details

    def test_restore_backup_os_error(self, facade):
        """Test backup restoration with OSError."""
        facade._service.restore_backup = Mock(side_effect=OSError("File not found"))

        result = facade.restore_backup()

        assert result.success is False
        assert "File not found" in result.error_details

    def test_apply_changes_not_loaded(self, facade):
        """Test applying changes before loading configuration."""
        facade._loaded = False

        result = facade.apply_changes()

        assert result.success is False
        assert "not loaded" in result.message.lower()

    def test_apply_changes_exception(self, facade):
        """Test apply changes with exception."""
        from src.core.exceptions import GrubConfigError

        facade._loaded = True
        facade._service.save_and_apply = Mock(side_effect=GrubConfigError("Write error"))

        result = facade.apply_changes()

        assert result.success is False
        assert "Write error" in result.error_details

    def test_properties_access(self, facade):
        """Test public property accessors."""
        facade._loaded = True
        facade._service.entries = {"KEY": "value"}
        facade._service.menu_entries = [{"title": "Test"}]
        facade._service.hidden_entries = ["entry1"]

        # Test getters
        assert facade.entries == {"KEY": "value"}
        assert facade.menu_entries == [{"title": "Test"}]
        assert facade.hidden_entries == ["entry1"]

        # Test setter
        facade.hidden_entries = ["entry2", "entry3"]
        assert facade._service.hidden_entries == ["entry2", "entry3"]

    def test_entries_setter(self, facade):
        """Test assigning entries propagates to the service."""
        new_entries = {"KEY": "VALUE"}
        facade.entries = new_entries
        assert facade._service.entries == new_entries

    def test_has_backups_true(self, facade):
        """Test has_backups when backups exist."""
        facade._service.backup_manager.get_latest_backup = Mock(return_value="/path/to/backup")

        assert facade.has_backups() is True

    def test_has_backups_false(self, facade):
        """Test has_backups when no backups exist."""
        facade._service.backup_manager.get_latest_backup = Mock(return_value=None)

        assert facade.has_backups() is False
