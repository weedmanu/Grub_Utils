"""Dialogue de sélection de sauvegarde."""

import os
from datetime import datetime

from src.ui.dialogs.base_dialog import BaseDialog
from src.ui.gtk_init import Gtk


class BackupSelectorDialog(BaseDialog):
    """Dialogue pour sélectionner une sauvegarde à restaurer."""

    def __init__(self, parent, backups: list[str], on_select_callback):
        """Initialize backup selector dialog.

        Args:
            parent: Parent window
            backups: List of backup paths
            on_select_callback: Callback function(backup_path or None)

        """
        super().__init__(parent, "Sélectionner une sauvegarde", (500, 400))
        self.backups = backups
        self.on_select_callback = on_select_callback
        self.selected_backup: str | None = None

        self._build_content()
        self.present()

    def _build_content(self):
        """Build dialog content with backup list."""
        main_box = self.create_main_box()

        # Info label
        info_label = Gtk.Label(
            label="Choisissez la sauvegarde à restaurer :",
            xalign=0,
        )
        main_box.append(info_label)

        # Scrolled window for backup list
        scrolled = Gtk.ScrolledWindow(
            vexpand=True,
            hexpand=True,
            min_content_height=200,
            min_content_width=400,
        )
        main_box.append(scrolled)

        # List box
        self.listbox = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        self.listbox.add_css_class("boxed-list")
        scrolled.set_child(self.listbox)

        # Add backups to list
        for backup_path in self.backups:
            row = self._create_backup_row(backup_path)
            self.listbox.append(row)

        # Select first item by default
        if self.backups:
            self.listbox.select_row(self.listbox.get_row_at_index(0))
            self.selected_backup = self.backups[0]

        # Connect selection changed
        self.listbox.connect("row-selected", self._on_row_selected)

        # Buttons box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(10)

        cancel_btn = Gtk.Button(label="Annuler")
        cancel_btn.connect("clicked", lambda _btn: self._on_cancel())
        button_box.append(cancel_btn)

        restore_btn = Gtk.Button(label="Restaurer")
        restore_btn.add_css_class("suggested-action")
        restore_btn.connect("clicked", lambda _btn: self._on_restore())
        button_box.append(restore_btn)

        main_box.append(button_box)

        self.set_child(main_box)

    def _on_row_selected(self, _listbox, row) -> None:
        """Handle row selection."""
        if row:
            index = row.get_index()
            self.selected_backup = self.backups[index]

    def _on_cancel(self):
        """Handle cancel button."""
        if self.on_select_callback:
            self.on_select_callback(None)
        self.close()

    def _on_restore(self):
        """Handle restore button."""
        if self.on_select_callback:
            self.on_select_callback(self.selected_backup)
        self.close()

    def _create_backup_row(self, backup_path: str) -> Gtk.ListBoxRow:
        """Create a row for a backup.

        Args:
            backup_path: Path to backup file

        Returns:
            ListBoxRow widget

        """
        row = Gtk.ListBoxRow()
        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=4,
            margin_top=8,
            margin_bottom=8,
            margin_start=12,
            margin_end=12,
        )

        # Filename
        filename = os.path.basename(backup_path)
        name_label = Gtk.Label(label=filename, xalign=0)
        name_label.add_css_class("heading")
        box.append(name_label)

        # Details (date and size)
        try:
            mtime = os.path.getmtime(backup_path)
            size = os.path.getsize(backup_path)
            date_str = datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M:%S")
            size_kb = size / 1024

            details = f"Date: {date_str} • Taille: {size_kb:.1f} Ko"
            details_label = Gtk.Label(label=details, xalign=0)
            details_label.add_css_class("dim-label")
            details_label.add_css_class("caption")
            box.append(details_label)
        except OSError:
            pass

        row.set_child(box)
        return row
