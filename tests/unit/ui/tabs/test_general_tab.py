import pytest
from unittest.mock import MagicMock, patch
from src.ui.tabs.general import GeneralTab
from src.ui.gtk_init import Gtk

class TestGeneralTab:
    def test_init(self):
        app = MagicMock()
        app.facade.entries = {
            "GRUB_DEFAULT": "0",
            "GRUB_TIMEOUT": "5",
            "GRUB_CMDLINE_LINUX_DEFAULT": "quiet splash"
        }
        app.facade.get_menu_entries.return_value = [
            {"id": "entry1", "title": "Entry 1"},
            {"id": "entry2", "title": "Entry 2"}
        ]
        
        # Mock Gtk.DropDown.new_from_strings
        with patch("src.ui.gtk_init.Gtk.DropDown.new_from_strings") as mock_new_dropdown:
            mock_dropdown = MagicMock()
            # Configure get_selected to return an int
            mock_dropdown.get_selected.return_value = 0
            mock_new_dropdown.return_value = mock_dropdown
            
            tab = GeneralTab(app)
            
            assert tab is not None
            assert tab.default_dropdown is not None
            assert tab.timeout_entry is not None
            assert tab.kernel_dropdown is not None
            
    def test_get_flat_menu_entries(self):
        app = MagicMock()
        app.facade.entries = {}
        # Mock the property menu_entries
        app.facade.menu_entries = [
            {"id": "entry1", "title": "Entry 1"},
            {"id": "entry2", "title": "Entry 2"}
        ]
        
        with patch("src.ui.gtk_init.Gtk.DropDown.new_from_strings") as mock_new_dropdown:
            mock_dropdown = MagicMock()
            mock_dropdown.get_selected.return_value = 0
            mock_new_dropdown.return_value = mock_dropdown
            
            tab = GeneralTab(app)
            
            # Check entry_labels
            expected = [
                "Première entrée (0)",
                "Dernière utilisée (saved)",
                "Entry 1",
                "Entry 2"
            ]
            assert tab.entry_labels == expected

    def test_init_custom_kernel_param(self):
        app = MagicMock()
        app.facade.entries = {
            "GRUB_CMDLINE_LINUX_DEFAULT": "custom param"
        }
        app.facade.get_menu_entries.return_value = []
        
        with patch("src.ui.gtk_init.Gtk.DropDown.new_from_strings") as mock_new_dropdown:
            mock_dropdown = MagicMock()
            mock_dropdown.get_selected.return_value = 0
            mock_new_dropdown.return_value = mock_dropdown
            
            tab = GeneralTab(app)
            
            # Check if custom param was added to options
            assert "custom param" in tab.kernel_options
