"""Tests for the GRUB service module."""

import os
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.core.exceptions import GrubConfigError, GrubServiceError
from src.core.services.grub_service import GrubService
from src.utils.config import GRUB_BACKGROUNDS_DIR


class TestGrubService:
    """Tests for GrubService class."""

    @pytest.fixture
    def mock_components(self):
        """Fixture providing mocked components."""
        with (
            patch("src.core.services.grub_service.GrubConfigLoader") as mock_loader,
            patch("src.core.services.grub_service.GrubMenuParser") as mock_parser,
            patch("src.core.services.grub_service.GrubConfigGenerator") as mock_generator,
            patch("src.core.services.grub_service.GrubValidator") as mock_validator,
            patch("src.core.services.grub_service.BackupManager") as mock_backup,
            patch("src.core.services.grub_service.SecureCommandExecutor") as mock_executor,
        ):

            yield {
                "loader": mock_loader,
                "parser": mock_parser,
                "generator": mock_generator,
                "validator": mock_validator,
                "backup": mock_backup,
                "executor": mock_executor,
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

        with (
            patch("src.core.services.grub_service.tempfile.NamedTemporaryFile") as mock_temp,
            patch("src.core.services.grub_service.os.unlink"),
        ):
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

        with (
            patch("src.core.services.grub_service.tempfile.NamedTemporaryFile") as mock_temp,
            patch("src.core.services.grub_service.os.unlink"),
        ):
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

        with (
            patch("src.core.services.grub_service.tempfile.NamedTemporaryFile") as mock_temp,
            patch("src.core.services.grub_service.os.unlink"),
        ):
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


class TestGrubServiceCoverage:
    """Additional coverage scenarios for GrubService."""

    @pytest.fixture
    def service(self):
        """Create a GrubService instance with mocked dependencies."""
        with (
            patch("src.core.services.grub_service.GrubConfigLoader"),
            patch("src.core.services.grub_service.GrubMenuParser"),
            patch("src.core.services.grub_service.GrubConfigGenerator"),
            patch("src.core.services.grub_service.GrubValidator"),
            patch("src.core.services.grub_service.BackupManager"),
            patch("src.core.services.grub_service.SecureCommandExecutor"),
        ):
            service = GrubService("/tmp/grub")
            service.loader.load.return_value = ({}, [])
            service.parser.parse_menu_entries.return_value = []
            return service

    def test_load_os_error(self, service):
        """Test load handles OSError."""
        service.loader.load.side_effect = OSError("Read error")
        with pytest.raises(GrubServiceError, match="Load failed"):
            service.load()

    def test_copy_background_image_no_path(self, service):
        """Test _copy_background_image with no path set."""
        service.entries = {}
        success, error = service._copy_background_image()
        assert success is True
        assert error == ""

    def test_copy_background_image_already_in_boot(self, service):
        """Test _copy_background_image with path already in /boot/grub."""
        service.entries = {"GRUB_BACKGROUND": "/boot/grub/image.png"}
        success, error = service._copy_background_image()
        assert success is True
        assert error == ""

    def test_copy_background_image_not_exists(self, service):
        """Test _copy_background_image with non-existent file."""
        service.entries = {"GRUB_BACKGROUND": "/home/user/image.png"}
        with patch("os.path.exists", return_value=False):
            success, error = service._copy_background_image()
            assert success is True
            assert error == ""

    def test_copy_background_image_mkdir_fail(self, service):
        """Test _copy_background_image fails when mkdir fails."""
        service.entries = {"GRUB_BACKGROUND": "/home/user/image.png"}
        with patch("os.path.exists", return_value=True):
            service.executor.execute_with_pkexec.return_value = (False, "Permission denied")
            success, error = service._copy_background_image()
            assert success is False
            assert "Failed to create backgrounds directory" in error

    def test_copy_background_image_copy_fail(self, service):
        """Test _copy_background_image fails when copy fails."""
        service.entries = {"GRUB_BACKGROUND": "/home/user/image.png"}
        with patch("os.path.exists", return_value=True):
            service.executor.execute_with_pkexec.return_value = (True, "")
            service.executor.copy_file_privileged.return_value = (False, "Copy failed")
            success, error = service._copy_background_image()
            assert success is False
            assert "Failed to copy background image" in error

    def test_copy_background_image_success(self, service):
        """Test _copy_background_image success."""
        service.entries = {"GRUB_BACKGROUND": "/home/user/image.png"}
        with patch("os.path.exists", return_value=True):
            service.executor.execute_with_pkexec.return_value = (True, "")
            service.executor.copy_file_privileged.return_value = (True, "")
            success, error = service._copy_background_image()
            assert success is True
            assert service.entries["GRUB_BACKGROUND"] == os.path.join(GRUB_BACKGROUNDS_DIR, "image.png")

    def test_copy_background_image_exception(self, service):
        """Test _copy_background_image handles exception."""
        service.entries = {"GRUB_BACKGROUND": "/home/user/image.png"}
        with patch("os.path.exists", return_value=True):
            service.executor.execute_with_pkexec.side_effect = OSError("Disk error")
            success, error = service._copy_background_image()
            assert success is False
            assert "Disk error" in error

    def test_apply_hidden_entries_no_entries(self, service):
        """Test _apply_hidden_entries with no hidden entries."""
        service.hidden_entries = []
        success, error = service._apply_hidden_entries()
        assert success is True

    def test_apply_hidden_entries_no_cfg(self, service):
        """Test _apply_hidden_entries when grub.cfg not found."""
        service.hidden_entries = ["Entry 1"]
        with patch("os.path.exists", return_value=False):
            success, error = service._apply_hidden_entries()
            assert success is True

    def test_apply_hidden_entries_success(self, service):
        """Test _apply_hidden_entries success."""
        service.hidden_entries = ["Hidden Entry"]
        grub_cfg_content = """
menuentry 'Visible Entry' {
    set root='hd0,gpt1'
}
menuentry 'Hidden Entry' {
    set root='hd0,gpt2'
}
submenu 'Submenu' {
    menuentry 'Inner' {
    }
}
"""
        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data=grub_cfg_content)),
            patch("tempfile.NamedTemporaryFile") as mock_temp,
            patch("os.unlink"),
        ):
            mock_temp.return_value.__enter__.return_value.name = "/tmp/temp.cfg"
            service.executor.copy_file_privileged.return_value = (True, "")
            success, error = service._apply_hidden_entries()
            assert success is True
            assert service.executor.copy_file_privileged.called

    def test_apply_hidden_entries_copy_fail(self, service):
        """Test _apply_hidden_entries fails when copy fails."""
        service.hidden_entries = ["Hidden Entry"]
        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="menuentry 'Hidden Entry' {}")),
            patch("tempfile.NamedTemporaryFile"),
            patch("os.unlink"),
        ):
            service.executor.copy_file_privileged.return_value = (False, "Copy failed")
            success, error = service._apply_hidden_entries()
            assert success is False
            assert "Failed to apply hidden entries" in error

    def test_apply_hidden_entries_exception(self, service):
        """Test _apply_hidden_entries handles exception."""
        service.hidden_entries = ["Hidden Entry"]
        with patch("os.path.exists", return_value=True), patch("builtins.open", side_effect=OSError("Read error")):
            success, error = service._apply_hidden_entries()
            assert success is False
            assert "Read error" in error

    def test_save_and_apply_hidden_entries_fail(self, service):
        """Test save_and_apply fails when hidden entries application fails."""
        service._loaded = True
        service.entries = {}
        service.hidden_entries = ["Hidden"]
        service._copy_background_image = MagicMock(return_value=(True, ""))
        service.validator.validate_all = MagicMock()
        service.backup_manager.create_backup.return_value = "/backup/path"
        service.generator.generate.return_value = "config"
        service._write_config = MagicMock(return_value=(True, ""))
        service._update_grub = MagicMock(return_value=(True, ""))
        service._apply_hidden_entries = MagicMock(return_value=(False, "Hidden fail"))
        success, error = service.save_and_apply()
        assert success is False
        assert "Hidden fail" in error
        service.backup_manager.restore_backup.assert_called_with("/backup/path")

    def test_save_and_apply_copy_background_short_circuit(self, service):
        """Test save_and_apply stops early when background copy fails."""
        service._loaded = True
        service.entries = {"GRUB_BACKGROUND": "/tmp/img.png"}
        service._copy_background_image = MagicMock(return_value=(False, "bg fail"))

        success, error = service.save_and_apply()

        assert success is False
        assert "bg fail" in error

    def test_save_and_apply_copy_background_fail(self):
        """save_and_apply should surface copy errors raised by helper."""
        with (
            patch("src.core.services.grub_service.GrubConfigLoader"),
            patch("src.core.services.grub_service.GrubMenuParser"),
            patch("src.core.services.grub_service.GrubConfigGenerator"),
            patch("src.core.services.grub_service.GrubValidator"),
            patch("src.core.services.grub_service.BackupManager"),
            patch("src.core.services.grub_service.SecureCommandExecutor"),
        ):
            service = GrubService()
            service._loaded = True
            service.entries = {"GRUB_BACKGROUND": "/path/to/bg.png"}
            with patch.object(service, "_copy_background_image", side_effect=OSError("Copy fail")):
                success, error = service.save_and_apply()
                assert success is False
                assert "Copy fail" in error

    def test_save_and_apply_generate_theme_fail(self):
        """save_and_apply should surface theme generation errors."""
        with (
            patch("src.core.services.grub_service.GrubConfigLoader"),
            patch("src.core.services.grub_service.GrubMenuParser"),
            patch("src.core.services.grub_service.GrubConfigGenerator"),
            patch("src.core.services.grub_service.GrubValidator"),
            patch("src.core.services.grub_service.BackupManager"),
            patch("src.core.services.grub_service.SecureCommandExecutor"),
        ):
            service = GrubService()
            service._loaded = True
            service.entries = {"GRUB_BACKGROUND": "/path/to/bg.png"}
            with patch.object(service, "_copy_background_image", return_value=(True, "")):
                with patch.object(service, "_generate_theme_if_needed", return_value=(False, "Theme generation failed")):
                    success, error = service.save_and_apply()
                    assert success is False
                    assert "Theme generation failed" in error

    def test_generate_theme_if_needed_exception(self):
        """_generate_theme_if_needed should handle exceptions."""
        with (
            patch("src.core.services.grub_service.GrubConfigLoader"),
            patch("src.core.services.grub_service.GrubMenuParser"),
            patch("src.core.services.grub_service.GrubConfigGenerator"),
            patch("src.core.services.grub_service.GrubThemeGenerator") as mock_generator,
            patch("src.core.services.grub_service.GrubValidator"),
            patch("src.core.services.grub_service.BackupManager"),
            patch("src.core.services.grub_service.SecureCommandExecutor"),
        ):
            service = GrubService()
            service.entries = {"GRUB_BACKGROUND": "/path/bg.png"}
            
            # Make theme_generator raise an exception
            service.theme_generator.should_generate_theme.return_value = True
            service.theme_generator.generate_theme_from_config.side_effect = Exception("Theme error")
            
            success, error = service._generate_theme_if_needed()
            assert success is False
            assert "Theme error" in error

    def test_generate_theme_if_needed_success(self):
        """_generate_theme_if_needed should return True when generation succeeds."""
        with (
            patch("src.core.services.grub_service.GrubConfigLoader"),
            patch("src.core.services.grub_service.GrubMenuParser"),
            patch("src.core.services.grub_service.GrubConfigGenerator"),
            patch("src.core.services.grub_service.GrubThemeGenerator"),
            patch("src.core.services.grub_service.GrubValidator"),
            patch("src.core.services.grub_service.BackupManager"),
            patch("src.core.services.grub_service.SecureCommandExecutor"),
        ):
            service = GrubService()
            service.entries = {"GRUB_BACKGROUND": "/path/bg.png"}
            
            # Mock successful generation
            service.theme_generator.should_generate_theme.return_value = True
            service.theme_generator.generate_theme_from_config.return_value = (True, "/boot/grub/themes/custom/theme.txt", "")
            
            success, error = service._generate_theme_if_needed()
            
            assert success is True
            assert error == ""
            assert service.entries["GRUB_THEME"] == "/boot/grub/themes/custom/theme.txt"

    def test_generate_theme_if_needed_failure(self):
        """_generate_theme_if_needed should return False when generation fails."""
        with (
            patch("src.core.services.grub_service.GrubConfigLoader"),
            patch("src.core.services.grub_service.GrubMenuParser"),
            patch("src.core.services.grub_service.GrubConfigGenerator"),
            patch("src.core.services.grub_service.GrubThemeGenerator"),
            patch("src.core.services.grub_service.GrubValidator"),
            patch("src.core.services.grub_service.BackupManager"),
            patch("src.core.services.grub_service.SecureCommandExecutor"),
        ):
            service = GrubService()
            service.entries = {"GRUB_BACKGROUND": "/path/bg.png"}
            
            # Mock failed generation
            service.theme_generator.should_generate_theme.return_value = True
            service.theme_generator.generate_theme_from_config.return_value = (False, "", "Generation error")
            
            success, error = service._generate_theme_if_needed()
            
            assert success is False
            assert "Generation error" in error
