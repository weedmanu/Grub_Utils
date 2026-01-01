import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime
import sys

# Define Mock Gtk structure
class MockWidget:
    def __init__(self, *args, **kwargs):
        self.children = []
        self.css_classes = []
    
    def append(self, widget): self.children.append(widget)
    def remove(self, widget): 
        if widget in self.children: self.children.remove(widget)
    def set_margin_start(self, *args): pass
    def set_margin_end(self, *args): pass
    def set_margin_top(self, *args): pass
    def set_margin_bottom(self, *args): pass
    def set_hexpand(self, *args): pass
    def set_vexpand(self, *args): pass
    def set_sensitive(self, *args): pass
    def connect(self, *args): pass
    def add_css_class(self, name): self.css_classes.append(name)
    def set_child(self, *args): pass
    def set_text(self, *args): pass
    def set_icon_name(self, *args): pass
    def set_pixel_size(self, *args): pass
    def set_min_content_height(self, *args): pass
    def get_row_at_index(self, index): return None
    def get_selected_row(self): return None
    def set_selectable(self, *args): pass

class MockGtk:
    class Box(MockWidget): 
        def __init__(self, orientation=None, spacing=0, **kwargs): super().__init__()
    class Label(MockWidget): 
        def __init__(self, label=None, xalign=0, **kwargs): super().__init__()
    class Button(MockWidget): 
        def __init__(self, label=None, **kwargs): super().__init__()
    class ScrolledWindow(MockWidget): pass
    class ListBox(MockWidget): pass
    class ListBoxRow(MockWidget): pass
    class DropDown(MockWidget):
        def __init__(self, model=None, **kwargs): 
            super().__init__()
            self.model = model
            self.selected = 0
        def get_selected(self): return self.selected
        def set_selected(self, index): self.selected = index
        def set_enable_search(self, enable): pass
        def set_model(self, model): self.model = model
    class Frame(MockWidget):
        def __init__(self, label=None, **kwargs): super().__init__()
    class StringList(MockWidget):
        def __init__(self, strings=None): 
            super().__init__()
            self.strings = strings or []
        def append(self, string): self.strings.append(string)
    class Grid(MockWidget):
        def __init__(self, column_spacing=0, row_spacing=0, **kwargs): super().__init__()
        def attach(self, child, left, top, width, height): self.children.append(child)
        def set_row_spacing(self, *args): pass
        def set_column_spacing(self, *args): pass
    class Image(MockWidget):
        @staticmethod
        def new_from_icon_name(name): return MockWidget()
    class Window(MockWidget):
        def __init__(self, title=None, **kwargs): 
            super().__init__()
            self.title = title
        def set_modal(self, *args): pass
        def set_transient_for(self, *args): pass
        def set_default_size(self, *args): pass
        def close(self): pass
        def present(self): pass
        def set_child(self, *args): pass
    class Orientation:
        VERTICAL = 1
        HORIZONTAL = 2
    class SelectionMode:
        SINGLE = 1
    class Align:
        START = "start"
        CENTER = "center"
        END = "end"
        FILL = "fill"
    class CssProvider:
        def load_from_data(self, *args): pass

# Patch src.ui.gtk_init.Gtk BEFORE importing BackupTab
with patch("src.ui.gtk_init.Gtk", MockGtk):
    from src.ui.tabs.backup import BackupTab

@pytest.mark.unit
class TestBackupTab:
    
    @pytest.fixture
    def app_mock(self):
        app = MagicMock()
        app.facade = MagicMock()
        app.logger = MagicMock()
        return app

    @pytest.fixture
    def backup_tab(self, app_mock):
        # We need to patch Gtk inside the module as well if it was imported differently
        # But since we patched it before import, BackupTab should use MockGtk
        
        # However, we need to ensure list_backups returns something safe for init
        app_mock.facade.list_backups.return_value = []
        
        tab = BackupTab(app_mock)
        
        # Mock widgets for assertions
        tab.backup_dropdown = MagicMock()
        tab.details_label = MagicMock()
        
        return tab

    def test_init(self, backup_tab):
        assert backup_tab.app is not None
        # Verify initial load
        backup_tab.app.facade.list_backups.assert_called_once()

    def test_load_backups_empty(self, backup_tab):
        # Setup
        backup_tab.app.facade.list_backups.return_value = []
        backup_tab.listbox.get_row_at_index.return_value = None
        
        # Execute
        backup_tab._load_backups()
        
        # Verify
        # Should append empty row
        backup_tab.listbox.append.assert_called()
        # Info label should be updated
        backup_tab.info_label.set_text.assert_called_with(
            "Aucune sauvegarde • Les sauvegardes sont créées automatiquement lors de chaque modification"
        )

    def test_load_backups_exception_handling(self, backup_tab):
        # Setup malformed backup to trigger exception in _create_backup_row
        malformed_backup = MagicMock()
        malformed_backup.path = "/path/to/backup"
        # Make accessing size raise an exception
        type(malformed_backup).size = PropertyMock(side_effect=Exception("Test error"))
        
        backup_tab.app.facade.list_backups.return_value = [malformed_backup]
        
        # Execute
        backup_tab._load_backups()
        
        # Verify
        # The row should still be appended, just without some details
        assert backup_tab.listbox.append.called

    def test_load_backups_with_data(self, backup_tab):
        # Setup
        backup1 = MagicMock()
        backup1.path = "/boot/grub/grub.cfg.bak1"
        backup1.date = datetime(2023, 1, 1, 12, 0, 0)
        backup1.size = 1024
        
        backup2 = MagicMock()
        backup2.path = "/boot/grub/grub.prime-backup"
        backup2.date = datetime(2023, 1, 1, 10, 0, 0)
        backup2.size = 2048
        
        backup_tab.app.facade.list_backups.return_value = [backup1, backup2]
        backup_tab.listbox.get_row_at_index.side_effect = [MagicMock(), None] # One row to remove, then empty
        
        # Execute
        backup_tab._load_backups()
        
        # Verify
        assert backup_tab.listbox.append.call_count == 2
        backup_tab.info_label.set_text.assert_called_with("2 sauvegardes disponibles")

    def test_load_backups_error(self, backup_tab):
        # Setup
        backup_tab.app.facade.list_backups.side_effect = Exception("Test error")
        backup_tab.listbox.get_row_at_index.return_value = None
        
        # Execute
        backup_tab._load_backups()
        
        # Verify
        backup_tab.app.logger.exception.assert_called_with("Erreur lors du chargement des sauvegardes")
        backup_tab.info_label.set_text.assert_called_with("Erreur: Test error")

    def test_on_row_selected(self, backup_tab):
        # Setup
        row = MagicMock()
        row.backup_path = "/path/to/backup"
        
        # Execute
        backup_tab._on_row_selected(None, row)
        
        # Verify
        backup_tab.delete_btn.set_sensitive.assert_called_with(True)
        backup_tab.restore_btn.set_sensitive.assert_called_with(True)
        
        # Test with None row
        backup_tab._on_row_selected(None, None)
        backup_tab.delete_btn.set_sensitive.assert_called_with(False)
        backup_tab.restore_btn.set_sensitive.assert_called_with(False)

    def test_on_refresh_clicked(self, backup_tab):
        with patch.object(backup_tab, "_load_backups") as mock_load:
            backup_tab._on_refresh_clicked(None)
            mock_load.assert_called_once()
            backup_tab.app.show_toast.assert_called_with("Liste des sauvegardes actualisée")

    def test_on_delete_clicked_no_selection(self, backup_tab):
        backup_tab.listbox.get_selected_row.return_value = None
        
        with patch("src.ui.dialogs.confirm_dialog.ConfirmDialog") as MockDialog:
            backup_tab._on_delete_clicked(None)
            MockDialog.assert_not_called()

    def test_on_delete_clicked_original_backup(self, backup_tab):
        row = MagicMock()
        row.backup_path = "/boot/grub/grub.prime-backup"
        backup_tab.listbox.get_selected_row.return_value = row
        
        with patch("src.ui.dialogs.error_dialog.ErrorDialog") as MockErrorDialog:
            backup_tab._on_delete_clicked(None)
            MockErrorDialog.assert_called_once()
            args = MockErrorDialog.call_args[0]
            assert args[1] == "Suppression impossible"

    def test_on_delete_clicked_confirm_yes(self, backup_tab):
        row = MagicMock()
        row.backup_path = "/boot/grub/grub.cfg.bak"
        backup_tab.listbox.get_selected_row.return_value = row
        
        with patch("src.ui.dialogs.confirm_dialog.ConfirmDialog") as MockConfirmDialog, \
             patch("os.remove") as mock_remove, \
             patch.object(backup_tab, "_load_backups") as mock_load:
            
            # Setup callback execution
            def side_effect(win, title, msg, callback):
                callback(True)
            MockConfirmDialog.side_effect = side_effect
            
            backup_tab._on_delete_clicked(None)
            
            mock_remove.assert_called_with("/boot/grub/grub.cfg.bak")
            backup_tab.app.show_toast.assert_called()
            mock_load.assert_called_once()

    def test_on_delete_clicked_confirm_no(self, backup_tab):
        row = MagicMock()
        row.backup_path = "/boot/grub/grub.cfg.bak"
        backup_tab.listbox.get_selected_row.return_value = row
        
        with patch("src.ui.dialogs.confirm_dialog.ConfirmDialog") as MockConfirmDialog, \
             patch("os.remove") as mock_remove:
            
            def side_effect(win, title, msg, callback):
                callback(False)
            MockConfirmDialog.side_effect = side_effect
            
            backup_tab._on_delete_clicked(None)
            
            mock_remove.assert_not_called()

    def test_on_delete_clicked_error(self, backup_tab):
        row = MagicMock()
        row.backup_path = "/boot/grub/grub.cfg.bak"
        backup_tab.listbox.get_selected_row.return_value = row
        
        with patch("src.ui.dialogs.confirm_dialog.ConfirmDialog") as MockConfirmDialog, \
             patch("os.remove", side_effect=OSError("Delete failed")):
            
            def side_effect(win, title, msg, callback):
                callback(True)
            MockConfirmDialog.side_effect = side_effect
            
            backup_tab._on_delete_clicked(None)
            
            backup_tab.app.logger.exception.assert_called_with("Erreur lors de la suppression")
            backup_tab.app.show_toast.assert_called_with("Erreur: Delete failed")

    def test_on_restore_clicked_no_selection(self, backup_tab):
        backup_tab.listbox.get_selected_row.return_value = None
        with patch("src.ui.dialogs.confirm_dialog.ConfirmDialog") as MockDialog:
            backup_tab._on_restore_clicked(None)
            MockDialog.assert_not_called()

    def test_on_restore_clicked_success(self, backup_tab):
        row = MagicMock()
        row.backup_path = "/boot/grub/grub.cfg.bak"
        backup_tab.listbox.get_selected_row.return_value = row
        backup_tab.app.facade.restore_backup.return_value = True
        
        with patch("src.ui.dialogs.confirm_dialog.ConfirmDialog") as MockConfirmDialog:
            def side_effect(win, title, msg, callback):
                callback(True)
            MockConfirmDialog.side_effect = side_effect
            
            backup_tab._on_restore_clicked(None)
            
            backup_tab.app.facade.restore_backup.assert_called_with("/boot/grub/grub.cfg.bak")
            backup_tab.app.show_toast.assert_called_with("Configuration restaurée depuis 'grub.cfg.bak'")
            backup_tab.app.reload_config.assert_called_once()

    def test_on_restore_clicked_failure(self, backup_tab):
        row = MagicMock()
        row.backup_path = "/boot/grub/grub.cfg.bak"
        backup_tab.listbox.get_selected_row.return_value = row
        backup_tab.app.facade.restore_backup.return_value = False
        
        with patch("src.ui.dialogs.confirm_dialog.ConfirmDialog") as MockConfirmDialog:
            def side_effect(win, title, msg, callback):
                callback(True)
            MockConfirmDialog.side_effect = side_effect
            
            backup_tab._on_restore_clicked(None)
            
            backup_tab.app.show_toast.assert_called_with("Échec de la restauration")

    def test_on_restore_clicked_exception(self, backup_tab):
        row = MagicMock()
        row.backup_path = "/boot/grub/grub.cfg.bak"
        backup_tab.listbox.get_selected_row.return_value = row
        backup_tab.app.facade.restore_backup.side_effect = Exception("Restore error")
        
        with patch("src.ui.dialogs.confirm_dialog.ConfirmDialog") as MockConfirmDialog:
            def side_effect(win, title, msg, callback):
                callback(True)
            MockConfirmDialog.side_effect = side_effect
            
            backup_tab._on_restore_clicked(None)
            
            backup_tab.app.logger.exception.assert_called_with("Erreur lors de la restauration")
            backup_tab.app.show_toast.assert_called_with("Erreur: Restore error")

    def test_get_config(self, backup_tab):
        assert backup_tab.get_config() == {}
