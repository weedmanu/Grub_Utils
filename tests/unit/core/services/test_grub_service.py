"""Tests for the GRUB service module."""

import os
from unittest.mock import MagicMock, patch

import pytest
from src.core.exceptions import GrubConfigError, GrubServiceError
from src.core.services.grub_service import GrubService


class TestGrubService:
    """Tests for GrubService class."""

    @pytest.fixture
    def mock_components(self):
        """Fixture providing mocked components."""
        with patch("src.core.services.grub_service.GrubConfigLoader") as mock_loader, \
             patch("src.core.services.grub_service.GrubMenuParser") as mock_parser, \
             patch("src.core.services.grub_service.GrubConfigGenerator") as mock_generator, \
             patch("src.core.services.grub_service.GrubValidator") as mock_validator, \
             patch("src.core.services.grub_service.BackupManager") as mock_backup, \
             patch("src.core.services.grub_service.SecureCommandExecutor") as mock_executor:
            
            yield {
                "loader": mock_loader,
                "parser": mock_parser,
                "generator": mock_generator,
                "validator": mock_validator,
                "backup": mock_backup,
                "executor": mock_executor
            }

    @pytest.fixture
    def service(self, mock_components):
        """Fixture providing a GrubService instance with mocked components."""
        return GrubService()

    def test_load_success(self, service, mock_components):
        """Test successful loading of configuration."""
        # Setup mocks
        mock_components["loader"].return_value.load.return_value = ({"GRUB_TIMEOUT": "5"}, ["GRUB_TIMEOUT=5"])
        mock_components["parser"].return_value.parse_menu_entries.return_value = [{"title": "Ubuntu"}]

        # Execute
        service.load()

        # Verify
        assert service._loaded is True
        assert service.entries == {"GRUB_TIMEOUT": "5"}
        assert len(service.menu_entries) == 1

    def test_load_failure(self, service, mock_components):
        """Test loading failure."""
        mock_components["loader"].return_value.load.side_effect = OSError("Read error")

        with pytest.raises(GrubServiceError, match="Load failed"):
            service.load()

    def test_save_and_apply_not_loaded(self, service):
        """Test save_and_apply when not loaded."""
        success, error = service.save_and_apply()
        assert success is False
        assert error == "Configuration not loaded"

    def test_save_and_apply_success(self, service, mock_components):
        """Test successful save and apply."""
        # Setup state
        service._loaded = True
        service.entries = {"GRUB_TIMEOUT": "5"}
        
        # Setup mocks
        mock_components["backup"].return_value.create_backup.return_value = "/backup/path"
        mock_components["generator"].return_value.generate.return_value = "GRUB_TIMEOUT=5"
        mock_components["executor"].return_value.copy_file_privileged.return_value = (True, "")
        mock_components["executor"].return_value.update_grub.return_value = (True, "")

        with patch("src.core.services.grub_service.tempfile.NamedTemporaryFile") as mock_temp, \
             patch("src.core.services.grub_service.os.unlink"):
            mock_temp.return_value.__enter__.return_value.name = "/tmp/file"
            
            success, error = service.save_and_apply()

        assert success is True
        assert error == ""
        mock_components["validator"].return_value.validate_all.assert_called_once()
        mock_components["backup"].return_value.create_backup.assert_called_once()
        mock_components["executor"].return_value.update_grub.assert_called_once()

    def test_save_and_apply_validation_error(self, service, mock_components):
        """Test save_and_apply with validation error."""
        service._loaded = True
        mock_components["validator"].return_value.validate_all.side_effect = GrubConfigError("Invalid config")

        success, error = service.save_and_apply()

        assert success is False
        assert "Invalid config" in error

    def test_save_and_apply_write_error(self, service, mock_components):
        """Test save_and_apply with write error."""
        service._loaded = True
        mock_components["executor"].return_value.copy_file_privileged.return_value = (False, "Permission denied")

        with patch("src.core.services.grub_service.tempfile.NamedTemporaryFile") as mock_temp, \
             patch("src.core.services.grub_service.os.unlink"):
            mock_temp.return_value.__enter__.return_value.name = "/tmp/file"
            
            success, error = service.save_and_apply()

        assert success is False
        assert "Failed to write config" in error

    def test_save_and_apply_update_error_rollback(self, service, mock_components):
        """Test save_and_apply with update-grub error triggering rollback."""
        service._loaded = True
        mock_components["backup"].return_value.create_backup.return_value = "/backup/path"
        mock_components["executor"].return_value.copy_file_privileged.return_value = (True, "")
        mock_components["executor"].return_value.update_grub.return_value = (False, "Update failed")

        with patch("src.core.services.grub_service.tempfile.NamedTemporaryFile") as mock_temp, \
             patch("src.core.services.grub_service.os.unlink"):
            mock_temp.return_value.__enter__.return_value.name = "/tmp/file"
            
            success, error = service.save_and_apply()

        assert success is False
        assert "Update failed" in error
        mock_components["backup"].return_value.restore_backup.assert_called_with("/backup/path")

    def test_restore_backup_success(self, service, mock_components):
        """Test successful backup restoration."""
        mock_components["backup"].return_value.restore_backup.return_value = "/restored/path"
        mock_components["executor"].return_value.update_grub.return_value = (True, "")
        
        # Mock load to avoid actual file reading
        service.load = MagicMock()

        success = service.restore_backup()

        assert success is True
        service.load.assert_called_once()
        mock_components["executor"].return_value.update_grub.assert_called_once()

    def test_restore_backup_failure(self, service, mock_components):
        """Test backup restoration failure."""
        mock_components["backup"].return_value.restore_backup.side_effect = OSError("Restore failed")

        success = service.restore_backup()

        assert success is False

    def test_update_grub_runtime_error(self, service, mock_components):
        """Test _update_grub with RuntimeError exception."""
        mock_components["executor"].return_value.update_grub.side_effect = RuntimeError("Runtime error")

        success, error = service._update_grub()

        assert success is False
        assert "Runtime error" in error

    def test_update_grub_os_error(self, service, mock_components):
        """Test _update_grub with OSError exception."""
        mock_components["executor"].return_value.update_grub.side_effect = OSError("OS error")

        success, error = service._update_grub()

        assert success is False
        assert "OS error" in error

    def test_restore_backup_update_fails(self, service, mock_components):
        """Test restore_backup when update-grub fails."""
        mock_components["backup"].return_value.restore_backup.return_value = "/restored/path"
        mock_components["executor"].return_value.update_grub.return_value = (False, "Update failed")
        
        # Mock load to avoid actual file reading
        service.load = MagicMock()

        success = service.restore_backup()

        assert success is False

    def test_write_config_os_error(self, service, mock_components):
        """Test _write_config with OSError during temp file creation."""
        with patch("src.core.services.grub_service.tempfile.NamedTemporaryFile") as mock_temp:
            mock_temp.side_effect = OSError("Cannot create temp file")
            
            success, error = service._write_config("GRUB_TIMEOUT=5")

        assert success is False
        assert "Cannot create temp file" in error

    def test_load_value_error(self, service, mock_components):
        """Test load with ValueError exception."""
        mock_components["loader"].return_value.load.side_effect = ValueError("Invalid value")

        with pytest.raises(GrubServiceError, match="Load failed"):
            service.load()

    def test_restore_backup_grub_config_error(self, service, mock_components):
        """Test restore_backup with GrubConfigError."""
        mock_components["backup"].return_value.restore_backup.side_effect = GrubConfigError("Config error")

        success = service.restore_backup()

        assert success is False