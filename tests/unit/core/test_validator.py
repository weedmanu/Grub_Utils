"""Unit tests for GrubValidator."""

from unittest.mock import patch

import pytest

from src.core.security import SecurityError
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

    def test_validate_all_invalid_theme_path(self, validator):
        """Test validating configuration with invalid theme path."""
        entries = {
            "GRUB_THEME": "/path/to/theme.txt",
        }
        
        with patch.object(GrubValidator, "validate_file_path", return_value=None):
            validator.validate_all(entries)
            
        assert "GRUB_THEME" not in entries

    def test_validate_all_valid_theme(self, validator):
        """Test validating configuration with valid theme path."""
        entries = {
            "GRUB_THEME": "/boot/grub/themes/mytheme/theme.txt",
        }
        
        with patch.object(GrubValidator, "validate_file_path", return_value="/boot/grub/themes/mytheme/theme.txt"):
            validator.validate_all(entries)
            
        assert entries["GRUB_THEME"] == "/boot/grub/themes/mytheme/theme.txt"

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
        """Test validate_all keeps empty background (handled by generator)."""
        entries = {
            "GRUB_TIMEOUT": "5",
            "GRUB_BACKGROUND": "",
        }

        validator.validate_all(entries)
        assert "GRUB_BACKGROUND" in entries
        assert entries["GRUB_BACKGROUND"] == ""

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
        """Test validate_all preserves empty GRUB_THEME entry."""
        entries = {
            "GRUB_TIMEOUT": "5",
            "GRUB_THEME": "",
        }

        validator.validate_all(entries)
        assert "GRUB_THEME" in entries
        assert entries["GRUB_THEME"] == ""

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

        with mock.patch.object(GrubValidator, "validate_timeout", side_effect=KeyError("unexpected")):
            with pytest.raises(GrubValidationError, match="Validation error"):
                validator.validate_all(entries)

    def test_validate_all_re_raises_validation_error(self, validator):
        """Test validate_all re-raises GrubValidationError."""
        entries = {
            "GRUB_TIMEOUT": "invalid",
        }
        with pytest.raises(GrubValidationError, match="Le timeout doit être un entier positif"):
            validator.validate_all(entries)

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

    def test_validate_kernel_params_non_standard_warning_logger(self):
        """Ensure logger is called for non-standard params when patched."""
        with patch("src.core.validator.logger") as mock_logger:
            GrubValidator.validate_kernel_params("custom_param")
            mock_logger.warning.assert_called_with("Paramètre noyau non standard: %s", "custom_param")

    def test_validate_all_unexpected_error_value(self):
        """validate_all surfaces unexpected exceptions from validators."""
        with patch("src.core.validator.GrubValidator.validate_timeout", side_effect=ValueError("Unexpected")):
            with pytest.raises(GrubValidationError, match="Validation error: Unexpected"):
                GrubValidator.validate_all({"GRUB_TIMEOUT": "5"})

    def test_validate_file_path_security_error(self):
        """SecurityError during file path validation should be wrapped."""
        with patch("src.core.validator.InputSecurityValidator.validate_file_path", side_effect=SecurityError("Unsafe")):
            with pytest.raises(GrubValidationError):
                GrubValidator.validate_file_path("/unsafe/path", {".png"})

    def test_validate_kernel_params_security_error(self):
        """SecurityError during kernel params validation should be wrapped."""
        with patch(
            "src.core.validator.InputSecurityValidator.validate_kernel_params", side_effect=SecurityError("Unsafe")
        ):
            with pytest.raises(GrubValidationError):
                GrubValidator.validate_kernel_params("unsafe param")

    def test_validate_gfxmode_standard_resolution(self):
        """Test gfxmode with standard resolution format."""
        validator = GrubValidator()
        # Format: widthxheight
        result = validator.validate_gfxmode("1024x768")
        assert result == "1024x768"

    def test_validate_gfxmode_auto(self):
        """Test gfxmode with auto value."""
        validator = GrubValidator()
        result = validator.validate_gfxmode("auto")
        assert result == "auto"

    def test_validate_gfxmode_invalid_format(self):
        """Test gfxmode with invalid format."""
        validator = GrubValidator()
        with pytest.raises(GrubValidationError, match="Format de résolution invalide"):
            validator.validate_gfxmode("invalid")

    def test_validate_all_with_gfxmode(self):
        """Test validate_all with gfxmode entry."""
        config = {"GRUB_GFXMODE": "1024x768"}
        result = GrubValidator.validate_all(config)
        assert config["GRUB_GFXMODE"] == "1024x768"

    def test_validate_all_with_theme(self):
        """Test validate_all with GRUB_THEME entry that does not exist."""
        config = {"GRUB_THEME": "/boot/grub/themes/starfield/theme.txt"}
        # Ce chemin n'existe pas, donc validate_file_path lève une erreur
        with pytest.raises(GrubValidationError, match="Le fichier n'existe pas"):
            GrubValidator.validate_all(config)

    def test_validate_all_with_kernel_params(self):
        """Test validate_all with GRUB_CMDLINE_LINUX_DEFAULT entry."""
        config = {"GRUB_CMDLINE_LINUX_DEFAULT": "quiet splash"}
        result = GrubValidator.validate_all(config)
        assert config["GRUB_CMDLINE_LINUX_DEFAULT"] == "quiet splash"

    def test_validate_timeout_empty_string(self):
        """Test timeout validation with empty string returns default."""
        validator = GrubValidator()
        # Une chaîne vide retourne le timeout par défaut (5)
        result = validator.validate_timeout("")
        assert result == 5

    def test_validate_color_pair_valid(self):
        """Test validate_color_pair with valid input."""
        validator = GrubValidator()
        result = validator.validate_color_pair("white/black", "GRUB_COLOR_NORMAL")
        assert result == "white/black"

    def test_validate_color_pair_empty(self):
        """Test validate_color_pair with empty input."""
        validator = GrubValidator()
        with pytest.raises(GrubValidationError, match="ne doit pas être vide"):
            validator.validate_color_pair("", "GRUB_COLOR_NORMAL")

    def test_validate_color_pair_no_slash(self):
        """Test validate_color_pair without slash."""
        validator = GrubValidator()
        with pytest.raises(GrubValidationError, match="doit être au format texte/fond"):
            validator.validate_color_pair("white", "GRUB_COLOR_NORMAL")

    def test_validate_color_pair_invalid_color(self):
        """Test validate_color_pair with invalid color name."""
        validator = GrubValidator()
        with pytest.raises(GrubValidationError, match="Couleur texte invalide"):
            validator.validate_color_pair("invalid/black", "GRUB_COLOR_NORMAL")
        
        with pytest.raises(GrubValidationError, match="Couleur fond invalide"):
            validator.validate_color_pair("white/invalid", "GRUB_COLOR_NORMAL")

    def test_validate_all_with_colors(self):
        """Test validate_all with color entries."""
        config = {
            "GRUB_COLOR_NORMAL": "white/black",
            "GRUB_COLOR_HIGHLIGHT": "black/white"
        }
        GrubValidator.validate_all(config)
        assert config["GRUB_COLOR_NORMAL"] == "white/black"
        assert config["GRUB_COLOR_HIGHLIGHT"] == "black/white"

    def test_validate_all_with_invalid_colors(self):
        """Test validate_all with invalid color entries."""
        config = {"GRUB_COLOR_NORMAL": "invalid"}
        with pytest.raises(GrubValidationError):
            GrubValidator.validate_all(config)

    def test_validate_all_unexpected_error(self):
        """Test validate_all handles unexpected errors."""
        # Mock validate_timeout to raise ValueError (not GrubValidationError)
        with patch.object(GrubValidator, "validate_timeout", side_effect=ValueError("Unexpected")):
            config = {"GRUB_TIMEOUT": "5"}
            # Should raise GrubValidationError wrapping the unexpected error
            with pytest.raises(GrubValidationError, match="Validation error: Unexpected"):
                GrubValidator.validate_all(config)

    def test_validate_all_empty_theme(self):
        """Test validate_all with empty GRUB_THEME entry."""
        config = {"GRUB_THEME": ""}
        # Should keep the empty entry (handled by generator)
        GrubValidator.validate_all(config)
        assert "GRUB_THEME" in config
        assert config["GRUB_THEME"] == ""
