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


class TestGeneralTabCoverage:
    """Additional coverage scenarios for GeneralTab."""

    @pytest.fixture
    def app(self):
        app = MagicMock()
        app.facade.entries = {}
        return app

    def test_select_timeout_not_found(self, app):
        """_select_timeout should choose default when value missing."""
        tab = GeneralTab(app)
        tab._select_timeout("999")
        tab.timeout_dropdown.set_selected.assert_called_with(2)

    def test_get_selected_timeout_invalid_index(self, app):
        """_get_selected_timeout should return default on invalid index."""
        tab = GeneralTab(app)
        tab.timeout_dropdown = MagicMock()
        tab.timeout_dropdown.get_selected.return_value = -1
        assert tab._get_selected_timeout() == "5"


class TestGeneralTabCoverageV2:
    """Dropdown binding and config edge cases."""

    @pytest.fixture
    def tab(self):
        app = MagicMock()
        app.facade.entries = {}
        app.facade.menu_entries = []
        return GeneralTab(app)

    def test_get_selected_timeout_invalid_index(self, tab):
        """Return default timeout when index out of range."""
        tab.timeout_dropdown = MagicMock()
        tab.timeout_dropdown.get_selected.return_value = 999
        assert tab._get_selected_timeout() == "5"

    def test_dropdown_callbacks(self, tab):
        """Dropdown setup/bind should configure labels and tooltips."""
        tab.kernel_descriptions = {"quiet": "Quiet mode"}
        mock_factory = MagicMock()
        mock_list_item = MagicMock()
        tab.on_dropdown_setup(mock_factory, mock_list_item)
        mock_list_item.set_child.assert_called()
        mock_string_obj = MagicMock()
        mock_string_obj.get_string.return_value = "quiet"
        mock_list_item.get_item.return_value = mock_string_obj
        mock_list_item.get_child.return_value = MagicMock()
        tab.on_dropdown_bind(mock_factory, mock_list_item)
        mock_label = mock_list_item.get_child.return_value
        mock_label.set_text.assert_called_with("quiet")
        mock_label.set_tooltip_text.assert_called_with("Quiet mode")

    def test_get_config_collects_defaults(self, tab):
        """get_config should assemble defaults and kernel params."""
        tab.default_dropdown = MagicMock(get_selected=MagicMock(return_value=0))
        tab.entry_ids = ["0"]
        tab.timeout_dropdown = MagicMock(get_selected=MagicMock(return_value=2))
        tab.kernel_dropdown = MagicMock(get_selected=MagicMock(return_value=0))
        tab.kernel_options = ["quiet"]
        config = tab.get_config()
        assert config["GRUB_DEFAULT"] == "0"
        assert config["GRUB_TIMEOUT"] == "5"
        assert config["GRUB_CMDLINE_LINUX_DEFAULT"] == "quiet"
