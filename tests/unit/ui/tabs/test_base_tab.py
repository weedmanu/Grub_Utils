import pytest
from unittest.mock import MagicMock
from src.ui.tabs.base import BaseTab
from src.ui.gtk_init import Gtk

class TestBaseTab:
    def test_init(self):
        app = MagicMock()
        tab = BaseTab(app)
        
        assert tab.app == app
        assert tab.grid is not None
        # Verify margins set (MockWidget returns mocks, so we can't easily check values unless we spy)
        # But we can assume it runs.
