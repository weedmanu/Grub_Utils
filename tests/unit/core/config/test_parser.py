"""Tests for the menu parser module."""

from unittest.mock import mock_open, patch

import pytest

from src.core.config.parser import GrubMenuParser


class TestGrubMenuParser:
    """Tests for GrubMenuParser class."""

    @patch("src.core.config.parser.os.path.exists")
    def test_init_auto_detect(self, mock_exists):
        """Test initialization with auto-detection."""
        mock_exists.side_effect = [False, True]  # First path fails, second succeeds

        parser = GrubMenuParser()

        assert parser.grub_cfg_path == "/boot/grub2/grub.cfg"

    @patch("src.core.config.parser.os.path.exists")
    def test_init_not_found(self, mock_exists):
        """Test initialization when no file found."""
        mock_exists.return_value = False

        with pytest.raises(FileNotFoundError):
            GrubMenuParser()

    def test_init_explicit_path(self):
        """Test initialization with explicit path."""
        path = "/custom/grub.cfg"
        parser = GrubMenuParser(path)
        assert parser.grub_cfg_path == path

    @patch("src.core.config.parser.os.path.exists")
    def test_parse_menu_entries_simple(self, mock_exists):
        """Test parsing simple menu entries."""
        content = """
        menuentry 'Ubuntu' --class ubuntu {
            linux /boot/vmlinuz-5.15.0-generic root=UUID=xxx ro
        }
        menuentry 'Windows 10' {
            chainloader +1
        }
        """
        mock_exists.return_value = True

        with patch("builtins.open", mock_open(read_data=content)):
            parser = GrubMenuParser("/boot/grub/grub.cfg")
            entries = parser.parse_menu_entries()

        assert len(entries) == 2
        assert entries[0]["title"] == "Ubuntu"
        assert entries[0]["linux"] == "/boot/vmlinuz-5.15.0-generic"
        assert entries[0]["submenu"] is False

        assert entries[1]["title"] == "Windows 10"
        assert entries[1]["linux"] == ""
        assert entries[1]["submenu"] is False

    @patch("src.core.config.parser.os.path.exists")
    def test_parse_menu_entries_submenu(self, mock_exists):
        """Test parsing entries with submenu."""
        content = """
        submenu 'Advanced options for Ubuntu' {
            menuentry 'Ubuntu, with Linux 5.15.0-generic' {
                linux /boot/vmlinuz-5.15.0-generic root=UUID=xxx ro
            }
            menuentry 'Ubuntu, with Linux 5.15.0-generic (recovery mode)' {
                linux /boot/vmlinuz-5.15.0-generic root=UUID=xxx ro recovery nomodeset
            }
        }
        """
        mock_exists.return_value = True

        with patch("builtins.open", mock_open(read_data=content)):
            parser = GrubMenuParser("/boot/grub/grub.cfg")
            entries = parser.parse_menu_entries()

        assert len(entries) == 3

        # Submenu entry
        assert entries[0]["title"] == "Advanced options for Ubuntu"
        assert entries[0]["submenu"] is True

        # Nested entries
        assert entries[1]["title"] == "Ubuntu, with Linux 5.15.0-generic"
        assert entries[1]["submenu"] is True  # Currently parser marks nested as submenu=True based on flag

        assert entries[2]["title"] == "Ubuntu, with Linux 5.15.0-generic (recovery mode)"
        assert entries[2]["submenu"] is True

    @patch("src.core.config.parser.os.path.exists")
    def test_parse_menu_entries_file_not_found(self, mock_exists):
        """Test parsing when file doesn't exist."""
        mock_exists.return_value = False

        parser = GrubMenuParser("/boot/grub/grub.cfg")
        entries = parser.parse_menu_entries()

        assert entries == []

    @patch("src.core.config.parser.os.path.exists")
    def test_parse_menu_entries_read_error(self, mock_exists):
        """Test parsing with read error."""
        mock_exists.return_value = True

        with patch("builtins.open", side_effect=OSError("Read error")):
            parser = GrubMenuParser("/boot/grub/grub.cfg")
            with pytest.raises(OSError):
                parser.parse_menu_entries()

    def test_extract_linux_path_no_match(self):
        """Test linux path extraction with no match."""
        parser = GrubMenuParser("/boot/grub/grub.cfg")
        path = parser._extract_linux_path("content", "title")
        assert path == ""

    @patch("src.core.config.parser.os.path.exists")
    def test_parse_empty_file(self, mock_exists):
        """Test parsing empty grub.cfg."""
        content = ""
        mock_exists.return_value = True

        with patch("builtins.open", mock_open(read_data=content)):
            parser = GrubMenuParser("/boot/grub/grub.cfg")
            entries = parser.parse_menu_entries()

        assert entries == []

    @patch("src.core.config.parser.os.path.exists")
    def test_parse_complex_menuentry(self, mock_exists):
        """Test parsing complex menu entry with special characters."""
        content = """menuentry 'Ubuntu 5.15.0-76' --class ubuntu {
    linux /boot/vmlinuz-5.15.0-76-generic root=UUID=12345
}"""
        mock_exists.return_value = True

        with patch("builtins.open", mock_open(read_data=content)):
            parser = GrubMenuParser("/boot/grub/grub.cfg")
            entries = parser.parse_menu_entries()

        assert len(entries) == 1
        assert entries[0]["title"] == "Ubuntu 5.15.0-76"
        assert "/boot/vmlinuz-5.15.0-76-generic" in entries[0]["linux"]

    @patch("src.core.config.parser.os.path.exists")
    def test_parse_nested_braces(self, mock_exists):
        """Test parsing with nested braces."""
        content = """
        submenu 'Advanced' {
            menuentry 'Entry 1' {
                if [ condition ]; then
                    linux /boot/vmlinuz
                fi
            }
        }
        """
        mock_exists.return_value = True

        with patch("builtins.open", mock_open(read_data=content)):
            parser = GrubMenuParser("/boot/grub/grub.cfg")
            entries = parser.parse_menu_entries()

        assert len(entries) == 2
        assert entries[0]["submenu"] is True
        assert entries[1]["submenu"] is True

    @patch("src.core.config.parser.os.path.exists")
    def test_find_grub_cfg_prefers_newest(self, mock_exists):
        """Prefer the first existing grub.cfg path (GRUB_CFG_PATHS order)."""
        mock_exists.side_effect = [True, True]
        parser = GrubMenuParser()
        assert parser.grub_cfg_path == "/boot/grub/grub.cfg"

    @patch("src.core.config.parser.os.path.exists")
    def test_parse_menu_entries_double_quotes(self, mock_exists):
        """Parse menu entries when titles are double-quoted (common with os-prober)."""
        content = r'''
        menuentry "Ubuntu" --class ubuntu {
            linuxefi /boot/vmlinuz-5.15.0-generic root=UUID=xxx ro
        }
        menuentry "Windows Boot Manager (on /dev/nvme0n1p1)" --class windows --class os $menuentry_id_option 'osprober-efi-AAAA-BBBB' {
            chainloader +1
        }
        '''
        mock_exists.return_value = True

        with patch("builtins.open", mock_open(read_data=content)):
            parser = GrubMenuParser("/boot/grub/grub.cfg")
            entries = parser.parse_menu_entries()

        assert len(entries) == 2
        assert entries[0]["title"] == "Ubuntu"
        assert entries[0]["linux"] == "/boot/vmlinuz-5.15.0-generic"
        assert entries[1]["title"].startswith("Windows Boot Manager")
        assert entries[1]["linux"] == ""

    @patch("src.core.config.parser.os.path.exists")
    def test_extract_linux_path_with_match(self, mock_exists):
        """Test linux path extraction with successful match."""
        parser = GrubMenuParser("/boot/grub/grub.cfg")
        content = """
        menuentry 'Test Entry' {
            linux /boot/vmlinuz-test root=UUID=123
        }
        """

        path = parser._extract_linux_path(content, "Test Entry")
        assert path == "/boot/vmlinuz-test"

    @patch("src.core.config.parser.os.path.exists")
    def test_parse_multiple_submenus(self, mock_exists):
        """Test parsing multiple submenus."""
        content = """
        submenu 'Submenu 1' {
            menuentry 'Entry 1.1' {
                linux /boot/vmlinuz1
            }
        }
        menuentry 'Main Entry' {
            linux /boot/vmlinuz-main
        }
        submenu 'Submenu 2' {
            menuentry 'Entry 2.1' {
                linux /boot/vmlinuz2
            }
        }
        """
        mock_exists.return_value = True

        with patch("builtins.open", mock_open(read_data=content)):
            parser = GrubMenuParser("/boot/grub/grub.cfg")
            entries = parser.parse_menu_entries()

        # Should have: 2 submenus + 2 nested entries + 1 main entry
        assert len(entries) == 5
        assert entries[0]["title"] == "Submenu 1"
        assert entries[0]["submenu"] is True
        assert entries[1]["submenu"] is True  # Nested in Submenu 1
        assert entries[2]["submenu"] is False  # Main entry
        assert entries[3]["title"] == "Submenu 2"
        assert entries[4]["submenu"] is True  # Nested in Submenu 2
