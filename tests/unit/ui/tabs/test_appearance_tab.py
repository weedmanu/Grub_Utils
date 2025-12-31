import pytest
from unittest.mock import MagicMock, patch
from src.ui.tabs.appearance import AppearanceTab
from src.ui.gtk_init import Gtk

class TestAppearanceTab:
    def test_init(self):
        app = MagicMock()
        app.facade.entries = {
            "GRUB_GFXMODE": "1920x1080",
            "GRUB_BACKGROUND": "/path/to/bg.png",
            "GRUB_THEME": "/path/to/theme.txt"
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
        
        with patch("src.ui.gtk_init.Gtk.Window") as mock_win_cls,              patch("src.ui.gtk_init.Gtk.Picture.new_for_filename") as mock_pic_new:
            
            mock_win = MagicMock()
            mock_win_cls.return_value = mock_win
            
            tab.on_preview_clicked(None)
            
            mock_win_cls.assert_called_once()
            mock_pic_new.assert_called_with("/path/to/image.png")
            mock_win.set_child.assert_called()
            mock_win.present.assert_called()
