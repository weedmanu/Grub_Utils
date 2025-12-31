import pytest
from unittest.mock import MagicMock
from src.ui.dialogs.confirm_dialog import ConfirmDialog, ConfirmOptions
from src.ui.gtk_init import Gtk

class TestConfirmDialog:
    def test_init(self):
        parent = MagicMock()
        callback = MagicMock()
        options = ConfirmOptions(title="Title", message="Message")
        
        dialog = ConfirmDialog(parent, callback, options)
        
        assert dialog.callback == callback
        assert dialog.dont_ask_check is not None
        
    def test_init_no_dont_ask(self):
        parent = MagicMock()
        callback = MagicMock()
        options = ConfirmOptions(title="Title", message="Message", allow_dont_ask=False)
        
        dialog = ConfirmDialog(parent, callback, options)
        
        assert dialog.dont_ask_check is None

    def test_on_cancel(self):
        parent = MagicMock()
        callback = MagicMock()
        options = ConfirmOptions(title="Title", message="Message")
        dialog = ConfirmDialog(parent, callback, options)
        
        dialog._on_cancel(None)
        
        callback.assert_called_with(False)
        # Verify close is called (mocked in BaseDialog/Gtk.Window)
        # Since BaseDialog inherits Gtk.Window, and we mock Gtk.Window, we can check close()
        # But wait, MockWidget doesn't have close() by default unless we add it or it's a MagicMock.
        # In conftest.py, MockWidget returns MagicMock for unknown attributes.
        
    def test_on_confirm(self):
        parent = MagicMock()
        callback = MagicMock()
        options = ConfirmOptions(title="Title", message="Message")
        dialog = ConfirmDialog(parent, callback, options)
        
        # Mock checkbox active state
        dialog.dont_ask_check.get_active.return_value = True
        
        dialog._on_confirm(None)
        
        callback.assert_called_with(True)
        assert dialog.dont_ask_again is True

    def test_on_confirm_no_checkbox(self):
        parent = MagicMock()
        callback = MagicMock()
        options = ConfirmOptions(title="Title", message="Message", allow_dont_ask=False)
        dialog = ConfirmDialog(parent, callback, options)
        
        dialog._on_confirm(None)
        
        callback.assert_called_with(True)
        assert dialog.dont_ask_again is False
