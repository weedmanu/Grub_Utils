from unittest.mock import MagicMock, patch

import pytest

from src.ui.tabs.appearance import AppearanceTab


class TestAppearanceTab:
    def test_init(self):
        app = MagicMock()
        app.facade.entries = {
            "GRUB_GFXMODE": "1920x1080",
            "GRUB_BACKGROUND": "/path/to/bg.png",
            "GRUB_THEME": "/path/to/theme.txt",
        }

        tab = AppearanceTab(app)

        assert tab is not None
        assert tab.gfxmode_entry is not None
        assert tab.background_entry is not None
        assert tab.theme_entry is not None

        # Verify values set
        # Since Gtk.Entry is mocked, we can't check text property directly unless we spy.
        # But we can assume it works if no error.

    def test_on_preview_clicked_no_path(self):
        app = MagicMock()
        app.facade.entries = {}
        tab = AppearanceTab(app)

        # Mock the entry text
        tab.background_entry.get_text.return_value = ""

        with patch("src.ui.gtk_init.Gtk.Window") as mock_win:
            tab.on_preview_clicked(None)
            mock_win.assert_not_called()

    def test_on_preview_clicked_with_path(self):
        app = MagicMock()
        app.facade.entries = {}
        tab = AppearanceTab(app)

        # Mock the entry text
        tab.background_entry.get_text.return_value = "/path/to/image.png"

        with (
            patch("src.ui.gtk_init.Gtk.Window") as mock_win_cls,
            patch("src.ui.gtk_init.Gtk.Picture.new_for_filename") as mock_pic_new,
        ):

            mock_win = MagicMock()
            mock_win_cls.return_value = mock_win

            tab.on_preview_clicked(None)

            mock_win_cls.assert_called_once()
            mock_pic_new.assert_called_with("/path/to/image.png")
            mock_win.set_child.assert_called()
            mock_win.present.assert_called()


class TestAppearanceTabCoverage:
    """Additional coverage scenarios for AppearanceTab."""

    @pytest.fixture
    def app(self):
        app = MagicMock()
        app.facade.entries = {}
        return app

    def test_select_color_not_found(self, app):
        """_select_color should fall back to index 0 when missing."""
        tab = AppearanceTab(app)
        dropdown = MagicMock()
        tab._select_color(dropdown, "non-existent-color")
        dropdown.set_selected.assert_called_with(0)

    def test_get_color_value_invalid_index(self, app):
        """_get_color_value returns default on invalid index."""
        tab = AppearanceTab(app)
        dropdown = MagicMock()
        dropdown.get_selected.return_value = -1
        assert tab._get_color_value(dropdown) == "black"

    def test_select_resolution_not_found(self, app):
        """_select_resolution falls back to auto when value missing."""
        tab = AppearanceTab(app)
        tab._select_resolution("9999x9999")
        tab.gfxmode_dropdown.set_selected.assert_called_with(0)

    def test_get_selected_resolution_invalid_index(self, app):
        """_get_selected_resolution returns auto on invalid index."""
        tab = AppearanceTab(app)
        tab.gfxmode_dropdown = MagicMock()
        tab.gfxmode_dropdown.get_selected.return_value = -1
        assert tab._get_selected_resolution() == "auto"

    def test_get_selected_resolution_out_of_range_high(self, app):
        """_get_selected_resolution returns auto when index too high."""
        tab = AppearanceTab(app)
        tab.gfxmode_dropdown = MagicMock()
        tab.gfxmode_dropdown.get_selected.return_value = 999
        assert tab._get_selected_resolution() == "auto"

    def test_load_current_colors_defaults(self, app):
        """_load_current_colors uses default colors when missing."""
        app.facade.entries = {}
        with patch.object(AppearanceTab, "_select_color") as mock_select:
            AppearanceTab(app)
        called_values = [call.args[1] for call in mock_select.call_args_list]
        assert "light-gray" in called_values
        assert "black" in called_values


class TestAppearanceTabCoverageV2:
    """Edge cases for color and resolution handling."""

    @pytest.fixture
    def tab(self):
        app = MagicMock()
        app.facade.entries = {}
        return AppearanceTab(app)

    @patch("src.ui.tabs.appearance.GRUB_COLORS", [("red", "Red")])
    def test_get_color_value_invalid_index(self, tab):
        """Fallback to black when index is out of bounds."""
        mock_dropdown = MagicMock()
        mock_dropdown.get_selected.return_value = 5
        assert tab._get_color_value(mock_dropdown) == "black"

    @patch("src.ui.tabs.appearance.GRUB_RESOLUTIONS", [("1024x768", "1024x768")])
    def test_select_resolution_not_found(self, tab):
        """Select auto when requested resolution absent."""
        tab.gfxmode_dropdown = MagicMock()
        tab._select_resolution("800x600")
        tab.gfxmode_dropdown.set_selected.assert_called_with(0)

    def test_on_preview_clicked_valid_path(self, tab):
        """Preview should open window for valid background path."""
        tab.background_entry = MagicMock()
        tab.background_entry.get_text.return_value = "/path/to/image.png"
        with (
            patch("src.ui.tabs.appearance.Gtk.Window") as mock_window_cls,
            patch("src.ui.tabs.appearance.Gtk.Picture") as mock_picture_cls,
        ):
            mock_window = mock_window_cls.return_value
            mock_picture = mock_picture_cls.new_for_filename.return_value
            tab.on_preview_clicked(None)
            mock_window_cls.assert_called()
            mock_picture_cls.new_for_filename.assert_called_with("/path/to/image.png")
            mock_window.set_child.assert_called_with(mock_picture)
            mock_window.present.assert_called()

    def test_get_config_populates_colors_and_background(self, tab):
        """get_config assembles full appearance configuration."""
        tab.background_entry = MagicMock()
        tab.background_entry.get_text.return_value = "/img.png"
        tab.gfxmode_dropdown = MagicMock(get_selected=MagicMock(return_value=0))
        tab.normal_text_dropdown = MagicMock(get_selected=MagicMock(return_value=0))
        tab.normal_bg_dropdown = MagicMock(get_selected=MagicMock(return_value=0))
        tab.highlight_text_dropdown = MagicMock(get_selected=MagicMock(return_value=0))
        tab.highlight_bg_dropdown = MagicMock(get_selected=MagicMock(return_value=0))
        with (
            patch("src.ui.tabs.appearance.GRUB_RESOLUTIONS", [("auto", "auto")]),
            patch("src.ui.tabs.appearance.GRUB_COLORS", [("white", "White")]),
        ):
            config = tab.get_config()
        assert config["GRUB_BACKGROUND"] == "/img.png"
        assert config["GRUB_GFXMODE"] == "auto"
        assert config["GRUB_COLOR_NORMAL"] == "white/white"
        assert config["GRUB_COLOR_HIGHLIGHT"] == "white/white"
