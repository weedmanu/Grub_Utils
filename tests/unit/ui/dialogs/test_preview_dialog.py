import pytest
from unittest.mock import MagicMock, patch
from src.ui.dialogs.preview_dialog import PreviewDialog
from src.ui.gtk_init import Gtk

class TestPreviewDialog:
    def test_init(self):
        parent = MagicMock()
        old_config = {"KEY": "old"}
        new_config = {"KEY": "new"}
        
        dialog = PreviewDialog(parent, "Title", old_config, new_config)
        
        assert dialog is not None
        # Verify structure
        # We can check if _create_boot_screen and _create_summary_frame were called
        # by spying or just trusting the init logic.
        
    def test_create_boot_screen(self):
        parent = MagicMock()
        old_config = {}
        new_config = {
            "GRUB_TIMEOUT": "10",
            "GRUB_GFXMODE": "1920x1080",
            "GRUB_DEFAULT": "0",
            "GRUB_CMDLINE_LINUX": "quiet"
        }
        
        dialog = PreviewDialog(parent, "Title", old_config, new_config)
        
        # _create_boot_screen is called in init.
        # We can verify the content if we can inspect the widget tree.
        # But with mocks, it's hard.
        
        # Let's call it directly to verify it runs without error
        frame = dialog._create_boot_screen(new_config)
        assert frame is not None

    def test_create_boot_screen_invalid_default(self):
        parent = MagicMock()
        old_config = {}
        new_config = {
            "GRUB_DEFAULT": "invalid"
        }
        
        dialog = PreviewDialog(parent, "Title", old_config, new_config)
        frame = dialog._create_boot_screen(new_config)
        assert frame is not None

    def test_create_summary_frame(self):
        parent = MagicMock()
        old_config = {
            "MODIFIED": "old_val",
            "REMOVED": "val",
            "UNCHANGED": "val"
        }
        new_config = {
            "MODIFIED": "new_val",
            "ADDED": "val",
            "UNCHANGED": "val"
        }
        
        dialog = PreviewDialog(parent, "Title", old_config, new_config)
        
        frame = dialog._create_summary_frame(old_config, new_config)
        assert frame is not None
        
        # We can't easily verify the content of the frame with mocks
        # unless we mock Gtk.Label and check calls.
        
    def test_close_button(self):
        parent = MagicMock()
        old_config = {}
        new_config = {}
        
        with patch("src.ui.gtk_init.Gtk.Button") as mock_button_cls:
            mock_btn = MagicMock()
            mock_button_cls.return_value = mock_btn
            
            dialog = PreviewDialog(parent, "Title", old_config, new_config)
            
            # Find close button connect
            assert mock_btn.connect.called
