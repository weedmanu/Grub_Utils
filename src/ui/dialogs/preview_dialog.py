"""GRUB Configuration preview dialog with realistic visual representation."""

from src.ui.gtk_init import Gtk
from src.utils.config import PREVIEW_WINDOW_HEIGHT, PREVIEW_WINDOW_WIDTH


class PreviewDialog(Gtk.Window):
    """Show realistic visual preview of GRUB boot screen."""

    def __init__(
        self,
        parent: Gtk.Window,
        title: str,
        old_config: dict[str, str],
        new_config: dict[str, str],
        menu_entries: list[dict] | None = None,
        hidden_entries: list[str] | None = None,
    ) -> None:
        """Initialize preview dialog.

        Args:
            parent: Parent window
            title: Dialog title
            old_config: Current GRUB configuration
            new_config: New GRUB configuration after changes
            menu_entries: List of available menu entries
            hidden_entries: List of hidden menu entries

        """
        super().__init__(title=title)
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_default_size(PREVIEW_WINDOW_WIDTH, PREVIEW_WINDOW_HEIGHT)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        main_box.set_margin_top(15)
        main_box.set_margin_bottom(15)
        main_box.set_margin_start(15)
        main_box.set_margin_end(15)

        # Title
        title_label = Gtk.Label(label="GRUB Boot Screen Preview")
        title_label.set_halign(Gtk.Align.START)
        title_label.get_style_context().add_class("title-2")
        main_box.append(title_label)

        # Main preview area
        preview_frame = self._create_boot_screen(new_config, menu_entries, hidden_entries)
        main_box.append(preview_frame)

        # Changes summary
        summary_frame = self._create_summary_frame(old_config, new_config)
        main_box.append(summary_frame)

        # Close button
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.END)

        close_btn = Gtk.Button(label="Fermer")
        close_btn.connect("clicked", lambda _: self.close())
        button_box.append(close_btn)

        main_box.append(button_box)
        self.set_child(main_box)
        self.present()

    def _create_boot_screen(
        self,
        config: dict[str, str],
        menu_entries: list[dict] | None = None,
        hidden_entries: list[str] | None = None,
    ) -> Gtk.Frame:
        """Create realistic GRUB boot screen visualization.

        Args:
            config: GRUB configuration
            menu_entries: List of menu entries
            hidden_entries: List of hidden entries

        Returns:
            Gtk.Frame: Boot screen frame

        """
        frame = Gtk.Frame()
        frame.set_label("Boot Screen Simulation")
        frame.set_label_align(0.0)

        # Create a box with dark background to simulate boot screen
        screen_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        screen_box.set_margin_top(20)
        screen_box.set_margin_bottom(20)
        screen_box.set_margin_start(20)
        screen_box.set_margin_end(20)

        # Add CSS for dark background
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(
            b"""
            .boot-screen {
                background-color: #1a1a1a;
                color: #ffffff;
            }
            """
        )
        screen_box.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        screen_box.get_style_context().add_class("boot-screen")

        # Get configuration values
        timeout = config.get("GRUB_TIMEOUT", "5")
        gfxmode = config.get("GRUB_GFXMODE", "1024x768")

        # GRUB header
        header_label = Gtk.Label(label="GNU GRUB version 2.x.x")
        header_label.set_halign(Gtk.Align.START)
        screen_box.append(header_label)

        # Empty line
        empty1 = Gtk.Label(label="")
        screen_box.append(empty1)

        # Menu title
        menu_title = Gtk.Label(label="┌─ Boot Menu ─────────────────────────────────┐")
        menu_title.set_halign(Gtk.Align.START)
        menu_title.get_style_context().add_class("monospace")
        screen_box.append(menu_title)

        # Menu entries
        self._add_menu_entries(screen_box, config, menu_entries, hidden_entries)

        menu_footer = Gtk.Label(label="└────────────────────────────────────────────┘")
        menu_footer.set_halign(Gtk.Align.START)
        menu_footer.get_style_context().add_class("monospace")
        screen_box.append(menu_footer)

        # Empty line
        empty2 = Gtk.Label(label="")
        screen_box.append(empty2)

        # Status info
        self._add_status_info(screen_box, timeout, gfxmode)

        frame.set_child(screen_box)
        return frame

    @staticmethod
    def _add_menu_entries(
        box: Gtk.Box,
        config: dict[str, str],
        menu_entries: list[dict] | None = None,
        hidden_entries: list[str] | None = None,
    ) -> None:
        """Add menu entries to boot screen.

        Args:
            box: Container box
            config: GRUB configuration
            menu_entries: List of menu entries
            hidden_entries: List of hidden entries

        """
        default_entry = config.get("GRUB_DEFAULT", "0")
        cmdline = config.get("GRUB_CMDLINE_LINUX", "quiet splash")
        hidden_set = set(hidden_entries or [])

        # Parse default entry
        try:
            default_idx = int(default_entry)
        except ValueError:
            default_idx = 0

        # Use provided entries or fallback to default
        if menu_entries:
            entries = []
            for entry in menu_entries:
                title = entry.get("title", "Unknown")
                if title not in hidden_set:
                    entries.append((title, entry.get("linux", "")))
        else:
            entries = [
                ("Ubuntu", f"Linux kernel with {cmdline}"),
                ("Ubuntu (recovery mode)", "Linux kernel (recovery mode)"),
                ("Windows Boot Manager", "Windows Boot Manager"),
                ("BIOS Setup", "Enter BIOS setup"),
                ("Memory test (memtest86+)", "Memory test"),
            ]

        for idx, (name, description) in enumerate(entries):
            is_selected = idx == default_idx
            prefix = "▶ " if is_selected else "  "
            label = Gtk.Label(label=f"{prefix}{name}")
            label.set_halign(Gtk.Align.START)
            label.get_style_context().add_class("monospace")

            if is_selected:
                label.get_style_context().add_class("success")

            box.append(label)

            # Truncate description if too long
            if len(description) > 50:
                description = description[:47] + "..."
            
            desc_label = Gtk.Label(label=f"    {description}")
            desc_label.set_halign(Gtk.Align.START)
            desc_label.get_style_context().add_class("monospace")
            box.append(desc_label)

    @staticmethod
    def _add_status_info(box: Gtk.Box, timeout: str, gfxmode: str) -> None:
        """Add status information at bottom of screen.

        Args:
            box: Container box
            timeout: Timeout value in seconds
            gfxmode: Graphics mode

        """
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

        timeout_msg = Gtk.Label(label=f"Use ↑↓ to select, Enter to boot (auto-boot in {timeout}s)")
        timeout_msg.set_halign(Gtk.Align.START)
        timeout_msg.get_style_context().add_class("monospace")
        info_box.append(timeout_msg)

        res_msg = Gtk.Label(label=f"Resolution: {gfxmode}")
        res_msg.set_halign(Gtk.Align.START)
        res_msg.get_style_context().add_class("monospace")
        info_box.append(res_msg)

        box.append(info_box)

    @staticmethod
    def _create_summary_frame(old_config: dict[str, str], new_config: dict[str, str]) -> Gtk.Frame:
        """Create summary of configuration changes.

        Args:
            old_config: Current configuration
            new_config: New configuration

        Returns:
            Gtk.Frame: Summary frame

        """
        frame = Gtk.Frame()
        frame.set_label("Configuration Changes")
        frame.set_label_align(0.0)

        summary_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        summary_box.set_margin_top(10)
        summary_box.set_margin_bottom(10)
        summary_box.set_margin_start(10)
        summary_box.set_margin_end(10)

        all_keys = sorted(set(old_config.keys()) | set(new_config.keys()))

        for key in all_keys:
            old_value = old_config.get(key)
            new_value = new_config.get(key)

            if old_value is None:
                # Added
                label = Gtk.Label(label=f"✅ [{key}] = {new_value}")
                label.set_halign(Gtk.Align.START)
                label.get_style_context().add_class("success")
                summary_box.append(label)
            elif new_value is None:
                # Removed
                label = Gtk.Label(label=f"❌ [{key}] removed (was: {old_value})")
                label.set_halign(Gtk.Align.START)
                label.get_style_context().add_class("error")
                summary_box.append(label)
            elif old_value != new_value:
                # Modified
                label = Gtk.Label(label=f"⚙️ [{key}]")
                label.set_halign(Gtk.Align.START)
                label.get_style_context().add_class("warning")
                summary_box.append(label)

                old_label = Gtk.Label(label=f"    Avant : {old_value}")
                old_label.set_halign(Gtk.Align.START)
                summary_box.append(old_label)

                new_label = Gtk.Label(label=f"    Après : {new_value}")
                new_label.set_halign(Gtk.Align.START)
                summary_box.append(new_label)

        frame.set_child(summary_box)
        return frame
