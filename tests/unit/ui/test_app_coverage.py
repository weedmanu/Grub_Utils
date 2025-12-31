import pytest
from unittest.mock import MagicMock, patch
from src.ui.app import GrubApp

class TestAppCoverage:
    @patch("src.ui.app.GrubFacade")
    def test_do_activate_load_failure(self, mock_facade_cls):
        """Test do_activate when load_configuration fails (Line 37)."""
        app = GrubApp()
        app.facade.load_configuration.return_value = MagicMock(success=False, error_details="Load error")
        
        with patch("src.ui.app.logger") as mock_logger:
            with patch.object(app, "_build_ui") as mock_build:
                app.do_activate()
                mock_logger.error.assert_called_with("Failed to load: %s", "Load error")
                mock_build.assert_called_once()

    @patch("src.ui.app.GrubFacade")
    def test_hide_toast_callback(self, mock_facade_cls):
        """Test the hide_toast callback in show_toast (Lines 117-119)."""
        app = GrubApp()
        app.toast_revealer = MagicMock()
        
        # We need to capture the callback passed to timeout_add
        with patch("src.ui.app.GLib.timeout_add") as mock_timeout:
            app.show_toast("message")
            callback = mock_timeout.call_args[0][1]
            
            # Execute callback
            result = callback()
            
            # Verify behavior
            app.toast_revealer.set_reveal_child.assert_called_with(False)
            assert result is False

    @patch("src.ui.app.GrubFacade")
    def test_refresh_ui_with_win(self, mock_facade_cls):
        """Test _refresh_ui when self.win exists (Line 345)."""
        app = GrubApp()
        app.win = MagicMock()
        app.facade.load_configuration.return_value = MagicMock(success=True)
        
        with patch.object(app, "_build_ui") as mock_build:
            app._refresh_ui()
            mock_build.assert_called_once()

    @patch("src.ui.app.GrubFacade")
    def test_refresh_ui_load_failure(self, mock_facade_cls):
        """Test _refresh_ui when load fails (Line 342-343)."""
        app = GrubApp()
        app.facade.load_configuration.return_value = MagicMock(success=False, error_details="Refresh error")
        
        with patch("src.ui.app.logger") as mock_logger:
            app._refresh_ui()
            mock_logger.error.assert_called_with("Failed to load: %s", "Refresh error")

    @patch("src.ui.app.GrubFacade")
    def test_on_file_dialog_response_success(self, mock_facade_cls):
        """Test _on_file_dialog_response with success (Line 182)."""
        app = GrubApp()
        mock_entry = MagicMock()
        mock_file = MagicMock()
        mock_file.get_path.return_value = "/path/to/file"
        
        mock_dialog = MagicMock()
        mock_dialog.open_finish.return_value = mock_file
        
        app._on_file_dialog_response(mock_dialog, MagicMock(), mock_entry)
        
        mock_entry.set_text.assert_called_with("/path/to/file")
