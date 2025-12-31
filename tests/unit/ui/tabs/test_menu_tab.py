import pytest
from unittest.mock import MagicMock, call
from src.ui.tabs.menu import MenuTab

class TestMenuTab:
    @pytest.fixture
    def app_mock(self):
        app = MagicMock()
        app.facade = MagicMock()
        # Setup default data
        app.facade.menu_entries = [
            {"title": "Entry 1", "submenu": False},
            {"title": "Entry 2", "submenu": True},
            {"title": "Entry 3", "submenu": False}
        ]
        app.facade.hidden_entries = ["Entry 3"]
        return app

    def test_init(self, app_mock):
        """Test initialization of MenuTab."""
        tab = MenuTab(app_mock)
        
        # Check if widgets are created
        assert tab.menu_list is not None
        
        # Check if check_buttons are populated
        assert "Entry 1" in tab.check_buttons
        assert "Entry 2" in tab.check_buttons
        assert "Entry 3" in tab.check_buttons
        
    def test_render_menu_level_logic(self, app_mock):
        """Test the rendering logic specifically."""
        tab = MenuTab(app_mock)
        
        buttons = tab.check_buttons
        assert len(buttons) == 3
        
        # Verify Entry 2 (submenu) has margin
        btn2 = buttons["Entry 2"]
        btn2.set_margin_start.assert_called_with(20)
        
        # Verify Entry 1 (normal) does not have margin set (or 0)
        btn1 = buttons["Entry 1"]
        btn1.set_margin_start.assert_not_called()


class TestMenuTabCoverage:
    """Additional coverage for MenuTab hidden entries."""

    def test_get_hidden_entries(self):
        app = MagicMock()
        app.facade.menu_entries = []
        app.facade.hidden_entries = ["Hidden"]
        tab = MenuTab(app)
        mock_check = MagicMock()
        mock_check.get_active.return_value = False
        tab.check_buttons = {"New Hidden": mock_check}
        hidden = tab.get_hidden_entries()
        assert hidden == ["New Hidden"]
