"""Unit tests for GrubValidator."""

import pytest

from src.core.validator import GrubValidationError, GrubValidator


@pytest.mark.unit
class TestGrubValidator:
    """Test suite for GrubValidator."""

    @pytest.fixture
    def validator(self):
        """Create a GrubValidator instance.

        Returns:
            GrubValidator instance
        """
        return GrubValidator()

    def test_validate_timeout_valid(self, validator):
        """Test validating valid timeout values."""
        assert validator.validate_timeout("0") == 0
        assert validator.validate_timeout("5") == 5
        assert validator.validate_timeout("300") == 300

    def test_validate_timeout_invalid_range(self, validator):
        """Test validating timeout out of range."""
        with pytest.raises(GrubValidationError, match="doit être entre 0 et"):
            validator.validate_timeout("301")

        # -1 ne match pas le pattern donc erreur "entier positif"
        with pytest.raises(GrubValidationError):
            validator.validate_timeout("-1")

    def test_validate_timeout_invalid_format(self, validator):
        """Test validating non-numeric timeout."""
        with pytest.raises(GrubValidationError, match="doit être un entier"):
            validator.validate_timeout("abc")

        with pytest.raises(GrubValidationError, match="doit être un entier"):
            validator.validate_timeout("5.5")

    def test_validate_gfxmode_auto(self, validator):
        """Test validating 'auto' gfxmode."""
        assert validator.validate_gfxmode("auto") == "auto"

    def test_validate_gfxmode_resolution(self, validator):
        """Test validating resolution format."""
        assert validator.validate_gfxmode("1920x1080") == "1920x1080"
        assert validator.validate_gfxmode("1024x768") == "1024x768"
        assert validator.validate_gfxmode("800x600") == "800x600"

    def test_validate_gfxmode_invalid(self, validator):
        """Test validating invalid gfxmode."""
        with pytest.raises(GrubValidationError, match="résolution invalide"):
            validator.validate_gfxmode("invalid")

        with pytest.raises(GrubValidationError, match="résolution invalide"):
            validator.validate_gfxmode("1920x")

    def test_validate_kernel_params_valid(self, validator):
        """Test validating valid kernel parameters."""
        params = "quiet splash nomodeset"
        assert validator.validate_kernel_params(params) == params

    def test_validate_kernel_params_dangerous(self, validator):
        """Test validating dangerous kernel parameters."""
        with pytest.raises(GrubValidationError, match="invalide"):
            validator.validate_kernel_params("quiet && rm -rf /")

        with pytest.raises(GrubValidationError, match="invalide"):
            validator.validate_kernel_params("quiet; reboot")

    def test_validate_all_valid(self, validator):
        """Test validating complete valid configuration."""
        entries = {
            "GRUB_TIMEOUT": "5",
            "GRUB_GFXMODE": "1920x1080",
            "GRUB_CMDLINE_LINUX_DEFAULT": "quiet splash",
        }

        # Should not raise
        validator.validate_all(entries)

    def test_validate_all_invalid_timeout(self, validator):
        """Test validating configuration with invalid timeout."""
        entries = {
            "GRUB_TIMEOUT": "999",  # Invalid
            "GRUB_GFXMODE": "auto",
        }

        with pytest.raises(GrubValidationError):
            validator.validate_all(entries)

    def test_validate_timeout_empty_string(self, validator):
        """Test validating empty timeout returns default."""
        assert validator.validate_timeout("") == 5

    def test_validate_gfxmode_empty_string(self, validator):
        """Test validating empty gfxmode returns auto."""
        assert validator.validate_gfxmode("") == "auto"
        assert validator.validate_gfxmode("AUTO") == "auto"

    def test_validate_file_path_empty(self, validator):
        """Test validating empty file path."""
        result = validator.validate_file_path("", {".png"})
        assert result is None

    def test_validate_file_path_not_exists(self, validator):
        """Test validating non-existent file."""
        with pytest.raises(GrubValidationError, match="n'existe pas"):
            validator.validate_file_path("/boot/nonexistent.png", {".png"})

    def test_validate_file_path_is_directory(self, validator, tmp_path):
        """Test validating directory instead of file."""
        directory = tmp_path / "testdir"
        directory.mkdir()

        with pytest.raises(GrubValidationError, match="n'est pas un fichier"):
            validator.validate_file_path(str(directory), {".png"})

    def test_validate_file_path_wrong_extension(self, validator, tmp_path):
        """Test validating file with wrong extension."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("test")

        with pytest.raises(GrubValidationError, match="Extension non autorisée"):
            validator.validate_file_path(str(file_path), {".png", ".jpg"})

    def test_validate_file_path_no_read_permission(self, validator, tmp_path):
        """Test validating file without read permissions."""
        file_path = tmp_path / "test.png"
        file_path.write_text("test")
        file_path.chmod(0o000)  # Remove all permissions

        try:
            with pytest.raises(GrubValidationError, match="Impossible de lire"):
                validator.validate_file_path(str(file_path), {".png"})
        finally:
            file_path.chmod(0o644)  # Restore for cleanup

    def test_validate_file_path_success(self, validator, tmp_path):
        """Test successful file path validation."""
        file_path = tmp_path / "background.png"
        file_path.write_text("fake image data")

        result = validator.validate_file_path(str(file_path), {".png", ".jpg"})
        assert result == str(file_path)

    def test_validate_kernel_params_empty(self, validator):
        """Test validating empty kernel parameters."""
        assert validator.validate_kernel_params("") == ""

    def test_validate_kernel_params_with_values(self, validator):
        """Test kernel params with key=value format."""
        params = "quiet splash root=/dev/sda1 ro"
        result = validator.validate_kernel_params(params)
        assert result == params

    def test_validate_kernel_params_non_standard(self, validator):
        """Test kernel params with non-standard but valid parameters."""
        params = "custom_param=value"
        # Should not raise, just warn
        result = validator.validate_kernel_params(params)
        assert result == params

    def test_validate_kernel_params_invalid_chars(self, validator):
        """Test kernel params with invalid characters."""
        with pytest.raises(GrubValidationError, match="invalide"):
            validator.validate_kernel_params("param*invalid")

    def test_validate_all_with_background(self, validator, tmp_path):
        """Test validate_all with background image."""
        bg_file = tmp_path / "bg.png"
        bg_file.write_text("image")

        entries = {
            "GRUB_TIMEOUT": "5",
            "GRUB_BACKGROUND": str(bg_file),
        }

        validator.validate_all(entries)
        assert entries["GRUB_BACKGROUND"] == str(bg_file)

    def test_validate_all_remove_empty_background(self, validator):
        """Test validate_all removes empty background."""
        entries = {
            "GRUB_TIMEOUT": "5",
            "GRUB_BACKGROUND": "",
        }

        validator.validate_all(entries)
        assert "GRUB_BACKGROUND" not in entries

    def test_validate_all_with_theme(self, validator, tmp_path):
        """Test validate_all with theme file."""
        theme_file = tmp_path / "theme.txt"
        theme_file.write_text("theme data")

        entries = {
            "GRUB_TIMEOUT": "5",
            "GRUB_THEME": str(theme_file),
        }

        validator.validate_all(entries)
        assert entries["GRUB_THEME"] == str(theme_file)

    def test_validate_all_remove_empty_theme(self, validator):
        """Test validate_all removes empty theme."""
        entries = {
            "GRUB_TIMEOUT": "5",
            "GRUB_THEME": "",
        }

        validator.validate_all(entries)
        assert "GRUB_THEME" not in entries

    def test_validate_all_with_cmdline(self, validator):
        """Test validate_all with kernel cmdline."""
        entries = {
            "GRUB_TIMEOUT": "5",
            "GRUB_CMDLINE_LINUX_DEFAULT": "quiet splash nomodeset",
        }

        validator.validate_all(entries)
        assert entries["GRUB_CMDLINE_LINUX_DEFAULT"] == "quiet splash nomodeset"

    def test_validate_all_unexpected_error(self, validator):
        """Test validate_all handles unexpected errors."""
        # Create an entries dict that will cause a KeyError during validation
        entries = {
            "GRUB_TIMEOUT": "5",
        }
        
        # Patch validate_timeout to raise an unexpected exception
        import unittest.mock as mock
        with mock.patch.object(GrubValidator, 'validate_timeout', side_effect=KeyError("unexpected")):
            with pytest.raises(GrubValidationError, match="Validation error"):
                validator.validate_all(entries)
    def test_validate_all_re_raises_validation_error(self, validator):
        """Test validate_all re-raises GrubValidationError."""
        entries = {
            "GRUB_TIMEOUT": "invalid",
        }
        with pytest.raises(GrubValidationError, match="Le timeout doit être un entier positif"):
            validator.validate_all(entries)

    def test_validate_all_remove_empty_background(self, validator):
        """Test validate_all removes empty background."""
        entries = {
            "GRUB_BACKGROUND": "",
        }
        validator.validate_all(entries)
        assert "GRUB_BACKGROUND" not in entries

    def test_validate_kernel_params_invalid_key(self, validator):
        """Test kernel params with invalid characters."""
        with pytest.raises(GrubValidationError, match="Paramètre noyau invalide"):
            validator.validate_kernel_params("!!!")

    def test_validate_kernel_params_non_standard_warning(self, validator, caplog):
        """Test kernel params with non-standard parameter triggers warning."""
        import logging
        with caplog.at_level(logging.WARNING):
            validator.validate_kernel_params("nonstandardparam")
            assert "Paramètre noyau non standard" in caplog.text

    def test_validate_kernel_params_with_equals_allowed(self, validator):
        """Test kernel params with equals sign are allowed even if not in whitelist."""
        # Whitelist check is skipped if '=' is present
        params = "custom_param=value"
        result = validator.validate_kernel_params(params)
        assert result == params
