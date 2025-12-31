import pytest
from unittest.mock import MagicMock, patch
from src.ui.dialogs.error_dialog import ErrorDialog, ErrorOptions
from src.ui.gtk_init import Gtk

class TestErrorDialog:
    def test_init_simple(self):
        parent = MagicMock()
        options = ErrorOptions(title="Error", message="Something went wrong")
        
        dialog = ErrorDialog(parent, options)
        
        # Verify basic structure
        # Since we can't easily inspect the widget hierarchy with mocks without complex setup,
        # we assume if it runs without error, it's mostly fine.
        # We can check if finalize_dialog was called (inherited from BaseDialog)
        # But finalize_dialog is a method on the instance.
        
        # We can check if set_child was called (via finalize_dialog)
        # dialog.set_child is a mock method from MockWidget (via BaseDialog -> Gtk.Window)
        # Wait, BaseDialog calls super().__init__ which is Gtk.Window.
        # In conftest.py, Gtk.Window is MockWidget.
        
        # Let's just assert it runs.
        assert dialog is not None

    def test_init_with_details(self):
        parent = MagicMock()
        options = ErrorOptions(title="Error", message="Message", details="Stack trace")
        
        with patch("src.ui.dialogs.error_dialog.create_monospace_text_view") as mock_create_tv:
            mock_tv = MagicMock()
            mock_create_tv.return_value = mock_tv
            
            dialog = ErrorDialog(parent, options)
            
            mock_create_tv.assert_called_once()
            mock_tv.get_buffer().set_text.assert_called_with("Stack trace")

    def test_close_button(self):
        parent = MagicMock()
        options = ErrorOptions(title="Error", message="Message")
        dialog = ErrorDialog(parent, options)
        
        # We need to find the close button and click it.
        # Since we don't have easy access to the button instance created inside __init__,
        # we might need to rely on the fact that it's connected.
        
        # However, testing the lambda in connect is hard without capturing the callback.
        # We can mock Gtk.Button and capture the connect call.
        
        with patch("src.ui.gtk_init.Gtk.Button") as mock_button_cls:
            mock_btn = MagicMock()
            mock_button_cls.return_value = mock_btn
            
            dialog = ErrorDialog(parent, options)
            
            # Find the connect call for "clicked"
            # There might be multiple buttons if BaseDialog adds some? No, BaseDialog just provides helpers.
            # ErrorDialog adds one button "Fermer".
            
            # Check calls to connect
            connect_calls = [call for call in mock_btn.connect.call_args_list if call[0][0] == "clicked"]
            assert len(connect_calls) > 0
            
            # Get the callback
            callback = connect_calls[0][0][1]
            
            # Call it
            with patch.object(dialog, "close") as mock_close:
                callback(None)
                mock_close.assert_called_once()
