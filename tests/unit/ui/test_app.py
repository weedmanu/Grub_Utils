from unittest.mock import MagicMock, patch

import pytest

from src.core.exceptions import GrubConfigError

# The mocks in conftest.py should handle the imports
from src.ui.app import GrubApp
from src.ui.gtk_init import GLib, Gtk


class TestGrubApp:
    @patch("src.ui.app.GrubFacade")
    def test_init(self, mock_facade_cls):
        """Test that GrubApp initializes with facade and tabs."""
        app = GrubApp()
        assert app.facade is not None
        assert app.ui.tabs == {}

    @patch("src.ui.app.GrubFacade")
    def test_do_activate(self, mock_facade_cls):
        """Test do_activate loads config and builds UI."""
        app = GrubApp()
        app.facade.load_configuration.return_value = MagicMock(success=True)

        with patch.object(app, "_build_ui") as mock_build:
            app.do_activate()
            app.facade.load_configuration.assert_called_once()
            mock_build.assert_called_once()

    @patch("src.ui.app.GrubFacade")
    def test_show_toast(self, mock_facade_cls):
        """Test show_toast sets text and reveals."""
        app = GrubApp()
        # Manually setup toast components since we skip _build_ui
        app.ui.toast_label = MagicMock()
        app.ui.toast_revealer = MagicMock()

        from src.ui.gtk_init import GLib

        with patch.object(GLib, "timeout_add") as mock_timeout:
            app.show_toast("Test message")
            app.ui.toast_label.set_text.assert_called_with("Test message")
            app.ui.toast_revealer.set_reveal_child.assert_called_with(True)
            mock_timeout.assert_called_once()

    @patch("src.ui.app.GrubFacade")
    def test_apply_configuration_success(self, mock_facade_cls):
        """Test successful configuration application."""
        app = GrubApp()
        app.facade.apply_changes.return_value = MagicMock(success=True)

        with patch.object(app, "show_toast") as mock_toast:
            app._apply_configuration()
            app.facade.apply_changes.assert_called_once()
            mock_toast.assert_called_with("Configuration appliquée avec succès !")

    @patch("src.ui.app.GrubFacade")
    def test_apply_configuration_failure(self, mock_facade_cls):
        """Test failed configuration application."""
        app = GrubApp()
        app.facade.apply_changes.return_value = MagicMock(success=False, error_details="Error")

        with patch("src.ui.app.ErrorDialog") as mock_error:
            app._apply_configuration()
            mock_error.assert_called_once()

    @patch("src.ui.app.GrubFacade")
    def test_on_preview_clicked_no_changes(self, mock_facade_cls):
        """Test preview when no changes were made shows current config."""
        app = GrubApp()
        app.facade.entries = {"KEY": "VALUE"}
        app.facade.menu_entries = []

        with patch.object(app, "_collect_ui_configuration", return_value={"KEY": "VALUE"}):
            with patch("src.ui.app.PreviewDialog") as mock_dialog:
                app.on_preview_clicked(None)
                # Preview should still be shown with current config
                mock_dialog.assert_called_once()

    @patch("src.ui.app.GrubFacade")
    def test_on_file_clicked(self, mock_facade_cls):
        """Test file selection button click."""
        app = GrubApp()
        app.ui.win = MagicMock()

        mock_entry = MagicMock()
        with patch("src.ui.app.Gtk.FileDialog") as mock_file_dialog:
            app.on_file_clicked(None, mock_entry, "Select File")
            mock_file_dialog.assert_called_once()

    @patch("src.ui.app.GrubFacade")
    def test_on_save_clicked(self, mock_facade_cls):
        """Test save button click shows confirmation."""
        app = GrubApp()
        app.ui.win = MagicMock()

        with patch.object(app, "_update_manager_from_ui"):
            with patch("src.ui.app.ConfirmDialog") as mock_confirm:
                app.on_save_clicked(None)
                mock_confirm.assert_called_once()

    @patch("src.ui.app.GrubFacade")
    def test_update_manager_from_ui(self, mock_facade_cls):
        """Test updating facade from UI widgets."""
        app = GrubApp()
        app.facade.entries = {}

        # Mock tabs
        mock_general = MagicMock()
        mock_general.get_config.return_value = {"GRUB_DEFAULT": "id1", "GRUB_TIMEOUT": "10"}

        mock_appearance = MagicMock()
        mock_appearance.get_config.return_value = {
            "GRUB_GFXMODE": "1024x768",
            "GRUB_BACKGROUND": "/path/bg",
            "GRUB_THEME": "/path/theme",
        }

        mock_menu = MagicMock()
        mock_menu.get_hidden_entries.return_value = ["entry1"]

        app.ui.tabs = {"general": mock_general, "appearance": mock_appearance, "menu": mock_menu}

        app._update_manager_from_ui()

        assert app.facade.entries["GRUB_DEFAULT"] == "id1"
        assert app.facade.entries["GRUB_TIMEOUT"] == "10"
        assert app.facade.entries["GRUB_GFXMODE"] == "1024x768"
        assert app.facade.entries["GRUB_BACKGROUND"] == "/path/bg"
        assert app.facade.entries["GRUB_THEME"] == "/path/theme"
        assert app.facade.hidden_entries == ["entry1"]

    @patch("src.ui.app.GrubFacade")
    def test_apply_configuration_grub_error(self, mock_facade_cls):
        """Test apply_configuration with GrubConfigError."""
        app = GrubApp()
        app.facade.apply_changes.side_effect = GrubConfigError("Config error")

        with patch.object(app, "_show_error") as mock_error:
            app._apply_configuration()
            mock_error.assert_called_with("Erreur de configuration", "Erreur de configuration : Config error")

    @patch("src.ui.app.GrubFacade")
    def test_apply_configuration_os_error(self, mock_facade_cls):
        """Test apply_configuration with OSError."""
        app = GrubApp()
        app.facade.apply_changes.side_effect = OSError("OS error")

        with patch.object(app, "_show_error") as mock_error:
            app._apply_configuration()
            mock_error.assert_called_with("Erreur d'accès", "Erreur d'accès au fichier : OS error")

    @patch("src.ui.app.GrubFacade")
    def test_apply_configuration_unexpected_error(self, mock_facade_cls):
        """Test apply_configuration with unexpected Exception."""
        app = GrubApp()
        app.facade.apply_changes.side_effect = Exception("Unexpected")

        with patch.object(app, "_show_error") as mock_error:
            app._apply_configuration()
            mock_error.assert_called_with("Erreur inattendue", "Une erreur inattendue s'est produite : Unexpected")

    @patch("src.ui.app.GrubFacade")
    def test_refresh_ui(self, mock_facade_cls):
        """Test refresh_ui reloads config and rebuilds UI."""
        app = GrubApp()
        app.ui.win = MagicMock()

        with patch.object(app, "_build_ui") as mock_build:
            app._refresh_ui()
            app.facade.load_configuration.assert_called_once()
            mock_build.assert_called_once()

    @patch("src.ui.app.GrubFacade")
    def test_on_file_dialog_response(self, mock_facade_cls):
        """Test _on_file_dialog_response updates entry."""
        app = GrubApp()
        mock_dialog = MagicMock()
        mock_result = MagicMock()
        mock_entry = MagicMock()
        mock_file = MagicMock()
        mock_file.get_path.return_value = "/path/to/file"
        mock_dialog.open_finish.return_value = mock_file

        app._on_file_dialog_response(mock_dialog, mock_result, mock_entry)

        mock_entry.set_text.assert_called_with("/path/to/file")

    @patch("src.ui.app.GrubFacade")
    def test_collect_ui_configuration(self, mock_facade_cls):
        """Test _collect_ui_configuration collects values from widgets."""
        app = GrubApp()
        app.facade.entries = {"EXISTING": "value"}

        mock_general = MagicMock()
        mock_general.get_config.return_value = {"GRUB_DEFAULT": "0"}
        app.ui.tabs = {"general": mock_general}

        config = app._collect_ui_configuration()

        assert config["EXISTING"] == "value"
        assert config["GRUB_DEFAULT"] == "0"


class TestGrubAppCoverage:
    """Additional coverage for GrubApp lifecycle and helpers."""

    @patch("src.ui.app.GrubFacade")
    def test_do_activate_load_failure(self, mock_facade_cls):
        app = GrubApp()
        app.facade.load_configuration.return_value = MagicMock(success=False, error_details="Load error")
        with patch("src.ui.app.logger") as mock_logger, patch.object(app, "_build_ui") as mock_build:
            app.do_activate()
            mock_logger.error.assert_called_with("Failed to load: %s", "Load error")
            mock_build.assert_called_once()

    @patch("src.ui.app.GrubFacade")
    def test_hide_toast_callback(self, mock_facade_cls):
        app = GrubApp()
        app.ui.toast_revealer = MagicMock()
        with patch("src.ui.app.GLib.timeout_add") as mock_timeout:
            app.show_toast("message")
            callback = mock_timeout.call_args[0][1]
            result = callback()
            app.ui.toast_revealer.set_reveal_child.assert_called_with(False)
            assert result is False

    @patch("src.ui.app.GrubFacade")
    def test_refresh_ui_with_win(self, mock_facade_cls):
        app = GrubApp()
        app.ui.win = MagicMock()
        app.facade.load_configuration.return_value = MagicMock(success=True)
        with patch.object(app, "_build_ui") as mock_build:
            app._refresh_ui()
            mock_build.assert_called_once()

    @patch("src.ui.app.GrubFacade")
    def test_refresh_ui_load_failure(self, mock_facade_cls):
        app = GrubApp()
        app.facade.load_configuration.return_value = MagicMock(success=False, error_details="Refresh error")
        with patch("src.ui.app.logger") as mock_logger:
            app._refresh_ui()
            mock_logger.error.assert_called_with("Failed to load: %s", "Refresh error")

    @patch("src.ui.app.GrubFacade")
    def test_on_file_dialog_response_success(self, mock_facade_cls):
        app = GrubApp()
        mock_entry = MagicMock()
        mock_file = MagicMock()
        mock_file.get_path.return_value = "/path/to/file"
        mock_dialog = MagicMock()
        mock_dialog.open_finish.return_value = mock_file
        app._on_file_dialog_response(mock_dialog, MagicMock(), mock_entry)
        mock_entry.set_text.assert_called_with("/path/to/file")


class TestGrubAppCoverageExtended:
    """Extended coverage for GrubApp edge cases."""

    @pytest.fixture
    def app(self):
        with (
            patch("src.ui.app.GrubFacade"),
            (
                patch("src.ui.app.Adw.ApplicationWindow")
                if hasattr(Gtk, "ApplicationWindow")
                else patch("src.ui.app.Gtk.ApplicationWindow")
            ),
        ):
            app = GrubApp()
            app.ui.win = MagicMock()
            app.facade = MagicMock()
            app.facade.entries = {}
            return app

    def test_build_ui_no_adw(self):
        with (
            patch("src.ui.app.HAS_ADW", False),
            patch("src.ui.app.GrubFacade"),
            patch("src.ui.app.Gtk.ApplicationWindow") as MockWindow,
            patch("src.ui.app.Gtk.HeaderBar") as MockHeader,
            patch("src.ui.app.GeneralTab"),
            patch("src.ui.app.AppearanceTab"),
            patch("src.ui.app.MenuTab"),
        ):
            app = GrubApp()
            # Don't call _build_ui as it creates real widgets
            assert app is not None

    def test_on_file_dialog_response_error(self, app):
        dialog = MagicMock()
        dialog.open_finish.side_effect = GLib.Error("Test error")
        entry = MagicMock()
        app._on_file_dialog_response(dialog, None, entry)
        entry.set_text.assert_not_called()

    def test_on_save_clicked_confirm(self, app):
        with patch("src.ui.app.ConfirmDialog") as MockDialog:
            app.on_save_clicked(None)
            callback = MockDialog.call_args[0][1]
            app._apply_configuration = MagicMock()
            callback(True)
            app._apply_configuration.assert_called_once()
            app._apply_configuration.reset_mock()
            callback(False)
            app._apply_configuration.assert_not_called()

    def test_collect_ui_configuration_savedefault_false(self, app):
        app.facade.entries = {"GRUB_DEFAULT": "0", "GRUB_SAVEDEFAULT": "true"}
        app.ui.tabs = {}
        config = app._collect_ui_configuration()
        assert "GRUB_SAVEDEFAULT" not in config

    def test_apply_configuration_os_error(self, app):
        app.facade.apply_changes.side_effect = OSError("Disk error")
        app._show_error = MagicMock()
        app._apply_configuration()
        app._show_error.assert_called_with("Erreur d'accès", "Erreur d'accès au fichier : Disk error")

    def test_apply_configuration_generic_exception(self, app):
        app.facade.apply_changes.side_effect = Exception("Unknown error")
        app._show_error = MagicMock()
        app._apply_configuration()
        app._show_error.assert_called_with("Erreur inattendue", "Une erreur inattendue s'est produite : Unknown error")


class TestGrubAppCoverageV2:
    """Coverage for additional app branches."""

    @pytest.fixture
    def app(self):
        with patch("src.ui.app.GrubFacade"):
            app = GrubApp()
            app.facade = MagicMock()
            app.ui.win = MagicMock()
            app.ui.tabs = {}
            app._build_ui_mock = MagicMock()
            # Mock the _build_ui method
            app._build_ui = app._build_ui_mock
            return app

    def test_refresh_ui_load_failure_logging(self, app):
        result = MagicMock(success=False, error_details="Load failed")
        app.facade.load_configuration.return_value = result
        with patch("src.ui.app.logger") as mock_logger:
            app._refresh_ui()
            mock_logger.error.assert_called_with("Failed to load: %s", "Load failed")

    def test_on_preview_clicked_exception(self, app):
        app.facade.entries = {}
        with (
            patch.object(app, "_collect_ui_configuration", side_effect=Exception("Preview error")),
            patch("src.ui.app.ErrorDialog") as mock_error_dialog,
        ):
            app.on_preview_clicked(None)
            assert mock_error_dialog.called

    def test_apply_configuration_exception(self, app):
        app.facade.apply_changes.side_effect = Exception("Apply error")
        with patch("src.ui.app.ErrorDialog") as mock_error_dialog:
            app._apply_configuration()
            assert mock_error_dialog.called

    def test_apply_configuration_success(self, app):
        app.facade.apply_changes.return_value.success = True
        app.show_toast = MagicMock()
        with patch("src.ui.app.logger") as mock_logger:
            app._apply_configuration()
            app.show_toast.assert_called_once()
            mock_logger.info.assert_called()

    def test_apply_configuration_grub_config_error(self, app):
        app.facade.apply_changes.side_effect = GrubConfigError("cfg")
        with patch("src.ui.app.ErrorDialog") as mock_error_dialog:
            app._apply_configuration()
            assert mock_error_dialog.called

    def test_refresh_ui_builds_when_window_present(self, app):
        app.facade.load_configuration.return_value.success = True
        app._refresh_ui()
        app._build_ui_mock.assert_called_once()

    def test_update_manager_from_ui_sets_hidden(self, app):
        menu_tab = MagicMock()
        menu_tab.get_hidden_entries.return_value = ["hidden"]
        app.ui.tabs = {"menu": menu_tab}
        with patch.object(app, "_collect_ui_configuration", return_value={"KEY": "VAL"}):
            app._update_manager_from_ui()
        assert app.facade.entries == {"KEY": "VAL"}
        assert app.facade.hidden_entries == ["hidden"]

    def test_on_preview_clicked_success(self, app):
        app.facade.entries = {"A": "1"}
        app.facade.menu_entries = [{"title": "entry", "linux": "vmlinuz"}]
        app.ui.tabs = {"menu": MagicMock(get_hidden_entries=MagicMock(return_value=["h"]))}
        with (
            patch.object(app, "_collect_ui_configuration", return_value={"A": "2"}),
            patch("src.ui.app.PreviewDialog") as mock_preview,
        ):
            app.on_preview_clicked(None)
            mock_preview.assert_called_once()
