"""Tests for the security module."""

import pytest
from src.core.security import InputSecurityValidator, SecurityError


class TestInputSecurityValidator:
    """Tests for InputSecurityValidator class."""

    def test_validate_line_valid(self):
        """Test validation of a valid line."""
        assert InputSecurityValidator.validate_line("GRUB_TIMEOUT=5") == "GRUB_TIMEOUT=5"
        assert InputSecurityValidator.validate_line("  GRUB_TIMEOUT=5  ") == "GRUB_TIMEOUT=5"

    def test_validate_line_invalid_type(self):
        """Test validation with invalid type."""
        with pytest.raises(SecurityError, match="Value must be a string"):
            InputSecurityValidator.validate_line(123)

    def test_validate_line_too_long(self):
        """Test validation with line too long."""
        long_line = "a" * (InputSecurityValidator.MAX_LINE_LENGTH + 1)
        with pytest.raises(SecurityError, match="Line too long"):
            InputSecurityValidator.validate_line(long_line)

    def test_validate_line_with_newlines(self):
        """Test validation with newlines."""
        with pytest.raises(SecurityError, match="Newlines not allowed"):
            InputSecurityValidator.validate_line("GRUB_TIMEOUT=5\n")

    def test_validate_parameter_name_valid(self):
        """Test validation of valid parameter names."""
        assert InputSecurityValidator.validate_parameter_name("GRUB_TIMEOUT") == "GRUB_TIMEOUT"
        assert InputSecurityValidator.validate_parameter_name("GRUB_CMDLINE_LINUX_DEFAULT") == "GRUB_CMDLINE_LINUX_DEFAULT"

    def test_validate_parameter_name_empty(self):
        """Test validation with empty parameter name."""
        with pytest.raises(SecurityError, match="Parameter name cannot be empty"):
            InputSecurityValidator.validate_parameter_name("")

    def test_validate_parameter_name_too_long(self):
        """Test validation with parameter name too long."""
        long_name = "A" * (InputSecurityValidator.MAX_PARAM_NAME_LENGTH + 1)
        with pytest.raises(SecurityError, match="Parameter name too long"):
            InputSecurityValidator.validate_parameter_name(long_name)

    def test_validate_parameter_name_invalid_format(self):
        """Test validation with invalid parameter name format."""
        with pytest.raises(SecurityError, match="Invalid parameter name format"):
            InputSecurityValidator.validate_parameter_name("grub_timeout")  # Lowercase not allowed by regex
        with pytest.raises(SecurityError, match="Invalid parameter name format"):
            InputSecurityValidator.validate_parameter_name("1GRUB_TIMEOUT")  # Cannot start with digit

    def test_validate_kernel_params_valid(self):
        """Test validation of valid kernel parameters."""
        assert InputSecurityValidator.validate_kernel_params("quiet splash") == "quiet splash"
        assert InputSecurityValidator.validate_kernel_params("root=UUID=1234-5678") == "root=UUID=1234-5678"

    def test_validate_kernel_params_dangerous(self):
        """Test validation with dangerous kernel parameters."""
        dangerous_chars = ["|", "<", ">", "$", "`"]
        for char in dangerous_chars:
            with pytest.raises(SecurityError, match="Shell metacharacters not allowed"):
                InputSecurityValidator.validate_kernel_params(f"quiet {char} echo hacked")

    def test_validate_file_path_valid(self):
        """Test validation of valid file paths."""
        assert InputSecurityValidator.validate_file_path("/etc/default/grub") == "/etc/default/grub"
        assert InputSecurityValidator.validate_file_path("/boot/grub/grub.cfg") == "/boot/grub/grub.cfg"

    def test_validate_file_path_empty(self):
        """Test validation with empty path."""
        with pytest.raises(SecurityError, match="Path cannot be empty"):
            InputSecurityValidator.validate_file_path("")

    def test_validate_file_path_traversal(self):
        """Test validation with directory traversal."""
        with pytest.raises(SecurityError, match="Directory traversal not allowed"):
            InputSecurityValidator.validate_file_path("/etc/../shadow")

    def test_validate_file_path_tilde(self):
        """Test validation with tilde expansion."""
        with pytest.raises(SecurityError, match="Tilde expansion not allowed"):
            InputSecurityValidator.validate_file_path("~/file")

    def test_validate_file_path_restricted_dir(self):
        """Test validation with restricted directory."""
        with pytest.raises(SecurityError, match="not in allowed directories"):
            InputSecurityValidator.validate_file_path("/home/user/file")

