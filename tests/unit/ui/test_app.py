import pytest
from unittest.mock import MagicMock, patch
from src.core.exceptions import GrubConfigError

# The mocks in conftest.py should handle the imports
from src.ui.app import GrubApp

class TestGrubApp:
    @patch("src.ui.app.GrubFacade")
    def test_init(self, mock_facade_cls):
        """Test that GrubApp initializes with facade and tabs."""
        app = GrubApp()
        assert app.facade is not None
        assert app.tabs == {}

    @patch("src.ui.app.GrubFacade")
    def test_build_ui_creates_components(self, mock_facade_cls):
        """Test that _build_ui creates the main UI components."""
        app = GrubApp()
        
        # Mock tab classes to avoid full initialization
        with patch("src.ui.app.GeneralTab"),              patch("src.ui.app.AppearanceTab"),              patch("src.ui.app.MenuTab"):
            app._build_ui()
        
        # Verify that main UI components were created
        assert app.win is not None
        assert app.overlay is not None
        assert app.toast_revealer is not None
        assert "general" in app.tabs
        assert "appearance" in app.tabs
        assert "menu" in app.tabs

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
        app.toast_label = MagicMock()
        app.toast_revealer = MagicMock()
        
        from src.ui.gtk_init import GLib
        with patch.object(GLib, "timeout_add") as mock_timeout:
            app.show_toast("Test message")
            app.toast_label.set_text.assert_called_with("Test message")
            app.toast_revealer.set_reveal_child.assert_called_with(True)
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
    def test_on_reset_clicked_no_backups(self, mock_facade_cls):
        """Test reset when no backups are available."""
        app = GrubApp()
        app.facade.has_backups.return_value = False
        
        with patch.object(app, "show_toast") as mock_toast:
            app.on_reset_clicked(None)
            mock_toast.assert_called_with("Aucune sauvegarde disponible à restaurer.")

    @patch("src.ui.app.GrubFacade")
    def test_on_preview_clicked_no_changes(self, mock_facade_cls):
        """Test preview when no changes were made."""
        app = GrubApp()
        app.facade.entries = {"KEY": "VALUE"}
        
        with patch.object(app, "_collect_ui_configuration", return_value={"KEY": "VALUE"}):
            with patch.object(app, "show_toast") as mock_toast:
                app.on_preview_clicked(None)
                mock_toast.assert_called_with("Aucun changement à prévisualiser.")

    @patch("src.ui.app.GrubFacade")
    def test_on_preview_clicked_with_changes(self, mock_facade_cls):
        """Test preview when changes are available."""
        app = GrubApp()
        app.facade.entries = {"KEY": "OLD"}
        
        with patch.object(app, "_collect_ui_configuration", return_value={"KEY": "NEW"}):
            with patch("src.ui.app.PreviewDialog") as mock_dialog:
                app.on_preview_clicked(None)
                mock_dialog.assert_called_once()

    @patch("src.ui.app.GrubFacade")
    def test_on_reset_clicked_with_backups(self, mock_facade_cls):
        """Test reset when backups are available."""
        app = GrubApp()
        app.facade.has_backups.return_value = True
        app.facade.list_backups.return_value = [MagicMock(path="/path/to/backup")]
        
        with patch("src.ui.app.BackupSelectorDialog") as mock_dialog:
            app.on_reset_clicked(None)
            mock_dialog.assert_called_once()

    @patch("src.ui.app.GrubFacade")
    def test_on_backup_selected(self, mock_facade_cls):
        """Test backup selection handler."""
        app = GrubApp()
        
        with patch.object(app, "_restore_backup") as mock_restore:
            app._on_backup_selected("/path/to/backup")
            mock_restore.assert_called_with("/path/to/backup")

    @patch("src.ui.app.GrubFacade")
    def test_restore_backup_success(self, mock_facade_cls):
        """Test successful backup restoration."""
        app = GrubApp()
        app.facade.restore_backup.return_value = MagicMock(success=True)
        
        with patch.object(app, "show_toast") as mock_toast:
            with patch.object(app, "_refresh_ui"):
                app._restore_backup("/path/to/backup")
                mock_toast.assert_called_with("Configuration restaurée avec succès.")

    @patch("src.ui.app.GrubFacade")
    def test_on_file_clicked(self, mock_facade_cls):
        """Test file selection button click."""
        app = GrubApp()
        app.win = MagicMock()
        
        mock_entry = MagicMock()
        with patch("src.ui.app.Gtk.FileDialog") as mock_file_dialog:
            app.on_file_clicked(None, mock_entry, "Select File")
            mock_file_dialog.assert_called_once()

    @patch("src.ui.app.GrubFacade")
    def test_on_save_clicked(self, mock_facade_cls):
        """Test save button click shows confirmation."""
        app = GrubApp()
        app.win = MagicMock()
        
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
        mock_general.get_config.return_value = {
            "GRUB_DEFAULT": "id1",
            "GRUB_TIMEOUT": "10"
        }
        
        mock_appearance = MagicMock()
        mock_appearance.get_config.return_value = {
            "GRUB_GFXMODE": "1024x768",
            "GRUB_BACKGROUND": "/path/bg",
            "GRUB_THEME": "/path/theme"
        }
        
        mock_menu = MagicMock()
        mock_menu.get_hidden_entries.return_value = ["entry1"]
        
        app.tabs = {
            "general": mock_general,
            "appearance": mock_appearance,
            "menu": mock_menu
        }
        
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
        app.win = MagicMock()
        
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
        app.tabs = {"general": mock_general}
        
        config = app._collect_ui_configuration()
        
        assert config["EXISTING"] == "value"
        assert config["GRUB_DEFAULT"] == "0"
