"""Tests for the configuration loader module."""

import os
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from src.core.config.loader import GrubConfigLoader
from src.core.exceptions import GrubConfigError


@pytest.mark.unit
class TestGrubConfigLoader:
    """Tests for GrubConfigLoader class."""

    @pytest.fixture
    def temp_config(self, tmp_path):
        """Create a temporary config file."""
        config_file = tmp_path / "grub"
        config_file.write_text(
            'GRUB_DEFAULT="0"\n'
            'GRUB_TIMEOUT="5"\n'
            '# Comment line\n'
            'GRUB_CMDLINE_LINUX="quiet splash"\n'
            '\n'
            '#GRUB_DISABLED_LINUX_UUID="true"\n'
        )
        return str(config_file)

    @pytest.fixture
    def loader(self, temp_config):
        """Fixture providing a GrubConfigLoader instance."""
        return GrubConfigLoader(temp_config)

    def test_init_default_path(self):
        """Test initialization with default path."""
        loader = GrubConfigLoader()
        assert loader.config_path == "/etc/default/grub"

    def test_init_custom_path(self, temp_config):
        """Test initialization with custom path."""
        loader = GrubConfigLoader(temp_config)
        assert loader.config_path == temp_config

    def test_load_success(self, loader):
        """Test successful configuration loading."""
        entries, lines = loader.load()

        # Verify entries
        assert entries["GRUB_DEFAULT"] == "0"
        assert entries["GRUB_TIMEOUT"] == "5"
        assert entries["GRUB_CMDLINE_LINUX"] == "quiet splash"
        
        # Commented lines should not be in entries
        assert "GRUB_DISABLED_LINUX_UUID" not in entries

        # Verify raw lines
        assert len(lines) == 6
        assert any("GRUB_DEFAULT" in line for line in lines)

    def test_load_file_not_found(self):
        """Test loading when file doesn't exist."""
        loader = GrubConfigLoader("/nonexistent/grub")
        
        with pytest.raises(GrubConfigError, match="Configuration file not found"):
            loader.load()

    def test_load_read_error(self, tmp_path, monkeypatch):
        """Test handling of read errors."""
        config_file = tmp_path / "grub"
        config_file.write_text("GRUB_DEFAULT=0")
        loader = GrubConfigLoader(str(config_file))

        # Mock open to raise OSError
        def mock_open_error(*args, **kwargs):
            raise OSError("Permission denied")

        monkeypatch.setattr("builtins.open", mock_open_error)

        with pytest.raises(GrubConfigError, match="Failed to read configuration"):
            loader.load()

    def test_parse_entries_various_formats(self, loader):
        """Test parsing entries with various formats."""
        lines = [
            'KEY1="value1"',
            "KEY2='value2'",
            "KEY3=value3",
            'KEY4="value with spaces"',
            "# COMMENTED_KEY=value",
            "",
            "INVALID LINE WITHOUT EQUALS",
        ]

        entries = loader._parse_entries(lines)

        assert entries["KEY1"] == "value1"
        assert entries["KEY2"] == "value2"
        assert entries["KEY3"] == "value3"
        assert entries["KEY4"] == "value with spaces"
        assert "COMMENTED_KEY" not in entries
        assert "INVALID" not in entries

    def test_parse_entries_empty_lines(self, loader):
        """Test parsing with only empty lines and comments."""
        lines = [
            "",
            "# Comment 1",
            "   ",
            "# Comment 2",
        ]

        entries = loader._parse_entries(lines)
        assert len(entries) == 0

    def test_parse_entries_complex_values(self, loader):
        """Test parsing entries with complex values."""
        lines = [
            'GRUB_CMDLINE_LINUX="quiet splash acpi_osi=Linux"',
            'GRUB_DISTRIBUTOR=`lsb_release -i -s 2> /dev/null || echo Debian`',
            'GRUB_TERMINAL="console serial"',
        ]

        entries = loader._parse_entries(lines)

        assert entries["GRUB_CMDLINE_LINUX"] == "quiet splash acpi_osi=Linux"
        assert "lsb_release" in entries["GRUB_DISTRIBUTOR"]
        assert entries["GRUB_TERMINAL"] == "console serial"




    def test_load_empty_file(self, tmp_path):
        """Test loading an empty configuration file."""
        config_file = tmp_path / "grub"
        config_file.write_text("")
        
        loader = GrubConfigLoader(str(config_file))
        entries, lines = loader.load()

        assert len(entries) == 0
        assert len(lines) == 0

    def test_load_preserves_line_order(self, loader):
        """Test that loading preserves original line order."""
        entries, lines = loader.load()

        # Verify lines are in original order
        line_texts = [line.strip() for line in lines]
        assert line_texts[0].startswith('GRUB_DEFAULT')
        assert line_texts[1].startswith('GRUB_TIMEOUT')
        assert line_texts[2].startswith('#')
