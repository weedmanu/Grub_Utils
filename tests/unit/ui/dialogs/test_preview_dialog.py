from unittest.mock import MagicMock, patch

import pytest

from src.core.dtos import PreviewConfigDTO
from src.ui.dialogs.preview_dialog import PreviewDialog


def _fake_widget():
    """Return a lightweight widget mock with a style context."""
    widget = MagicMock()
    widget.get_style_context.return_value = MagicMock()
    return widget


class TestPreviewDialog:
    def test_init(self):
        parent = MagicMock()
        old_config = {"KEY": "old"}
        new_config = {"KEY": "new"}
        config = PreviewConfigDTO(old_config=old_config, new_config=new_config)

        dialog = PreviewDialog(parent, "Title", config)

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
            "GRUB_CMDLINE_LINUX": "quiet",
        }
        config = PreviewConfigDTO(old_config=old_config, new_config=new_config)

        dialog = PreviewDialog(parent, "Title", config)

        # _create_boot_screen is called in init.
        # We can verify the content if we can inspect the widget tree.
        # But with mocks, it's hard.

        # Let's call it directly to verify it runs without error
        frame = dialog._create_boot_screen(new_config)
        assert frame is not None

    def test_create_boot_screen_invalid_default(self):
        parent = MagicMock()
        old_config = {}
        new_config = {"GRUB_DEFAULT": "invalid"}
        config = PreviewConfigDTO(old_config=old_config, new_config=new_config)

        dialog = PreviewDialog(parent, "Title", config)
        frame = dialog._create_boot_screen(new_config)
        assert frame is not None

    def test_create_summary_frame(self):
        parent = MagicMock()
        old_config = {"MODIFIED": "old_val", "REMOVED": "val", "UNCHANGED": "val"}
        new_config = {"MODIFIED": "new_val", "ADDED": "val", "UNCHANGED": "val"}
        config = PreviewConfigDTO(old_config=old_config, new_config=new_config)

        dialog = PreviewDialog(parent, "Title", config)

        frame = dialog._create_summary_frame(old_config, new_config)
        assert frame is not None

        # We can't easily verify the content of the frame with mocks
        # unless we mock Gtk.Label and check calls.

    def test_close_button(self):
        parent = MagicMock()
        old_config = {}
        new_config = {}
        config = PreviewConfigDTO(old_config=old_config, new_config=new_config)

        with patch("src.ui.gtk_init.Gtk.Button") as mock_button_cls:
            mock_btn = MagicMock()
            mock_button_cls.return_value = mock_btn

            dialog = PreviewDialog(parent, "Title", config)

            # Find close button connect
            assert mock_btn.connect.called
            assert dialog is not None


class TestPreviewDialogCoverage:
    """Additional coverage scenarios for PreviewDialog."""

    @pytest.fixture
    def parent(self):
        return MagicMock()

    def test_init_no_changes(self, parent):
        """Init should handle identical configs without summary."""
        config_dict = {"KEY": "VALUE"}
        config = PreviewConfigDTO(old_config=config_dict, new_config=config_dict)
        with patch("src.ui.dialogs.preview_dialog.Gtk.Window"):
            PreviewDialog(parent, "Title", config)

    def test_color_fallbacks_without_slash(self, parent):
        """Color parsing should fall back when missing slash."""
        config_dict = {"GRUB_COLOR_NORMAL": "strange", "GRUB_COLOR_HIGHLIGHT": "odd"}
        config = PreviewConfigDTO(old_config={}, new_config=config_dict)

        with (
            patch("src.ui.dialogs.preview_dialog.grub_color_to_hex") as mock_hex,
            patch("src.ui.dialogs.preview_dialog.Gtk") as mock_gtk,
        ):
            mock_gtk.CssProvider.return_value = MagicMock()
            mock_gtk.Box.side_effect = lambda *a, **k: _fake_widget()
            mock_gtk.Frame.side_effect = lambda *a, **k: _fake_widget()
            mock_gtk.Label.side_effect = lambda *a, **k: _fake_widget()
            mock_gtk.Align = MagicMock(CENTER="CENTER", FILL="FILL", START="START")
            mock_gtk.Orientation = MagicMock(VERTICAL="VERTICAL", HORIZONTAL="HORIZONTAL")
            mock_gtk.STYLE_PROVIDER_PRIORITY_APPLICATION = 1

            dialog = PreviewDialog.__new__(PreviewDialog)
            dialog._add_status_info = MagicMock()

            dialog._create_boot_screen(config_dict, [], [])

            called_colors = [call.args[0] for call in mock_hex.call_args_list]
            assert "light-gray" in called_colors
            assert "black" in called_colors

    def test_create_boot_screen_no_bg(self, parent):
        """_create_boot_screen handles empty background value."""
        config_dict = {"GRUB_BACKGROUND": ""}
        config = PreviewConfigDTO(old_config={}, new_config=config_dict)
        with patch("src.ui.dialogs.preview_dialog.Gtk.Window"):
            PreviewDialog(parent, "Title", config)

    def test_create_boot_screen_no_theme(self, parent):
        """_create_boot_screen handles empty theme value."""
        config_dict = {"GRUB_THEME": ""}
        config = PreviewConfigDTO(old_config={}, new_config=config_dict)
        with patch("src.ui.dialogs.preview_dialog.Gtk.Window"):
            PreviewDialog(parent, "Title", config)

    def test_add_menu_entries_styles_more_label(self, parent):
        """Ensure extra entries label receives CSS provider."""
        labels = []

        def label_factory(*_args, **_kwargs):
            widget = _fake_widget()
            labels.append(widget)
            return widget

        css_provider = MagicMock()
        with patch("src.ui.dialogs.preview_dialog.Gtk") as mock_gtk:
            mock_gtk.Label.side_effect = label_factory
            mock_gtk.Align = MagicMock(FILL="FILL", START="START", CENTER="CENTER")
            mock_gtk.STYLE_PROVIDER_PRIORITY_APPLICATION = 1

            box = MagicMock()
            entries = [{"title": f"Entry {i}"} for i in range(10)]

            PreviewDialog._add_menu_entries(box, {"GRUB_DEFAULT": "0"}, entries, [], css_provider)

            more_label = labels[-1]
            more_label.get_style_context.return_value.add_provider.assert_called_with(css_provider, 1)

    def test_add_status_info_value_error_branch(self, parent):
        """_add_status_info should handle non-integer timeout."""
        labels = []

        def label_factory(*_args, **_kwargs):
            widget = _fake_widget()
            labels.append(widget)
            return widget

        css_provider = MagicMock()
        with patch("src.ui.dialogs.preview_dialog.Gtk") as mock_gtk:
            mock_gtk.Label.side_effect = label_factory
            mock_gtk.Box.return_value = _fake_widget()
            mock_gtk.Align = MagicMock(CENTER="CENTER")
            mock_gtk.Orientation = MagicMock(HORIZONTAL="HORIZONTAL")
            mock_gtk.STYLE_PROVIDER_PRIORITY_APPLICATION = 1

            box = MagicMock()
            PreviewDialog._add_status_info(box, "not-an-int", "auto", css_provider)

            timeout_label = labels[0]
            timeout_label.get_style_context.return_value.add_provider.assert_called_with(css_provider, 1)


class TestPreviewDialogCoverageV2:
    """Static-method coverage for PreviewDialog helpers."""

    def test_create_summary_frame_removed_entry(self):
        """_create_summary_frame should handle removed entries."""
        with patch("src.ui.dialogs.preview_dialog.Gtk"):
            box = PreviewDialog._create_summary_frame(old_config={"KEY": "Value"}, new_config={})
            assert box is not None

    def test_add_status_info_timeout_variants(self):
        """_add_status_info handles special timeout values."""
        with patch("src.ui.dialogs.preview_dialog.Gtk"):
            dialog = PreviewDialog.__new__(PreviewDialog)
            grid = MagicMock()
            dialog._add_status_info(grid, "-1", "auto")
            dialog._add_status_info(grid, "0", "auto")

    def test_create_boot_screen_invocation(self):
        """_create_boot_screen returns a frame with minimal config."""
        with patch("src.ui.dialogs.preview_dialog.Gtk") as mock_gtk:
            mock_gtk.CssProvider.return_value = MagicMock()
            frame = PreviewDialog._create_boot_screen(
                PreviewDialog.__new__(PreviewDialog),
                config={"GRUB_TIMEOUT": "3", "GRUB_GFXMODE": "auto"},
                menu_entries=[{"title": "Ubuntu"}],
                hidden_entries=[],
            )
            assert frame is not None

    def test_add_menu_entries_more_than_max(self):
        """_add_menu_entries handles large menu lists."""
        with patch("src.ui.dialogs.preview_dialog.Gtk"):
            dialog = PreviewDialog.__new__(PreviewDialog)
            box = MagicMock()
            menu_entries = [{"title": f"Entry {i}"} for i in range(20)]
            dialog._add_menu_entries(box, {}, menu_entries)
            assert box.append.call_count > 0
