"""GRUB Configuration preview dialog with realistic visual representation."""

from src.ui.gtk_init import Gtk
from src.utils.config import (
    PREVIEW_WINDOW_HEIGHT,
    PREVIEW_WINDOW_WIDTH,
    grub_color_to_hex,
)


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

        # Store configs for comparison
        self._old_config = old_config
        self._new_config = new_config
        self._has_changes = old_config != new_config

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_top(12)
        main_box.set_margin_bottom(12)
        main_box.set_margin_start(12)
        main_box.set_margin_end(12)

        # Header with status indicator
        header_box = self._create_header(title)
        main_box.append(header_box)

        # Main preview area - the boot screen simulation
        preview_frame = self._create_boot_screen(new_config, menu_entries, hidden_entries)
        preview_frame.set_vexpand(True)
        main_box.append(preview_frame)

        # Changes summary (only if there are changes)
        if self._has_changes:
            summary_frame = self._create_summary_frame(old_config, new_config)
            main_box.append(summary_frame)
        else:
            info_label = Gtk.Label(label="ℹ️ Aperçu de la configuration actuelle (aucune modification)")
            info_label.set_halign(Gtk.Align.START)
            info_label.get_style_context().add_class("dim-label")
            main_box.append(info_label)

        # Close button
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.END)

        close_btn = Gtk.Button(label="Fermer")
        close_btn.connect("clicked", lambda _: self.close())
        button_box.append(close_btn)

        main_box.append(button_box)
        self.set_child(main_box)
        self.present()

    def _create_header(self, title: str) -> Gtk.Box:
        """Create header with title and status.

        Args:
            title: Dialog title

        Returns:
            Gtk.Box: Header box

        """
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        title_label = Gtk.Label(label=title)
        title_label.set_halign(Gtk.Align.START)
        title_label.get_style_context().add_class("title-2")
        title_label.set_hexpand(True)
        header_box.append(title_label)

        # Status badge
        if self._has_changes:
            status_label = Gtk.Label(label="● Modifications en attente")
            status_label.get_style_context().add_class("warning")
        else:
            status_label = Gtk.Label(label="● Configuration actuelle")
            status_label.get_style_context().add_class("success")
        status_label.set_halign(Gtk.Align.END)
        header_box.append(status_label)

        return header_box

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
        frame.set_label("Simulation de l'écran de démarrage")
        frame.set_label_align(0.0)

        # Outer container for proper styling
        outer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Extraire les couleurs de la configuration GRUB
        normal_colors = config.get("GRUB_COLOR_NORMAL", "light-gray/black")
        highlight_colors = config.get("GRUB_COLOR_HIGHLIGHT", "black/light-gray")
        
        # Parser les couleurs (format: "texte/fond")
        if "/" in normal_colors:
            normal_fg, normal_bg = normal_colors.split("/", 1)
        else:
            normal_fg, normal_bg = "light-gray", "black"
            
        if "/" in highlight_colors:
            highlight_fg, highlight_bg = highlight_colors.split("/", 1)
        else:
            highlight_fg, highlight_bg = "black", "light-gray"
        
        # Convertir en hexadécimal
        normal_fg_hex = grub_color_to_hex(normal_fg)
        normal_bg_hex = grub_color_to_hex(normal_bg)
        highlight_fg_hex = grub_color_to_hex(highlight_fg)
        highlight_bg_hex = grub_color_to_hex(highlight_bg)
        
        # Add comprehensive CSS for realistic GRUB appearance with dynamic colors
        css_provider = Gtk.CssProvider()
        css_content = f"""
            .grub-screen {{
                background-color: {normal_bg_hex};
                padding: 30px 40px;
                border-radius: 0;
            }}
            .grub-menu-border {{
                background-color: {normal_bg_hex};
                border: 2px solid {normal_fg_hex};
                padding: 0;
            }}
            .grub-menu-title {{
                background-color: {normal_fg_hex};
                color: {normal_bg_hex};
                font-family: "DejaVu Sans Mono", "Liberation Mono", monospace;
                font-size: 14px;
                font-weight: bold;
                padding: 4px 10px;
            }}
            .grub-menu-content {{
                background-color: {normal_bg_hex};
                padding: 6px 0;
            }}
            .grub-entry {{
                color: {normal_fg_hex};
                background-color: {normal_bg_hex};
                font-family: "DejaVu Sans Mono", "Liberation Mono", monospace;
                font-size: 14px;
                padding: 2px 10px;
                margin: 0;
            }}
            .grub-entry-selected {{
                background-color: {highlight_bg_hex};
                color: {highlight_fg_hex};
                font-family: "DejaVu Sans Mono", "Liberation Mono", monospace;
                font-size: 14px;
                padding: 2px 10px;
                margin: 0;
            }}
            .grub-footer {{
                color: {normal_fg_hex};
                font-family: "DejaVu Sans Mono", "Liberation Mono", monospace;
                font-size: 12px;
            }}
            .grub-countdown {{
                color: {normal_fg_hex};
                font-family: "DejaVu Sans Mono", "Liberation Mono", monospace;
                font-size: 12px;
            }}
        """
        css_provider.load_from_data(css_content.encode("utf-8"))
        outer_box.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        outer_box.get_style_context().add_class("grub-screen")

        # Create screen content
        screen_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        # Get configuration values
        timeout = config.get("GRUB_TIMEOUT", "5")
        gfxmode = config.get("GRUB_GFXMODE", "auto")

        # Menu border container (simulates the GRUB menu box)
        menu_border = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        menu_border.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        menu_border.get_style_context().add_class("grub-menu-border")
        menu_border.set_halign(Gtk.Align.CENTER)

        # Menu title bar (gray bar at top)
        distro_name = "GNU GRUB"
        title_bar = Gtk.Label(label=f"  {distro_name}  ")
        title_bar.set_halign(Gtk.Align.FILL)
        title_bar.set_hexpand(True)
        title_bar.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        title_bar.get_style_context().add_class("grub-menu-title")
        menu_border.append(title_bar)

        # Menu content area
        menu_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        menu_content.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        menu_content.get_style_context().add_class("grub-menu-content")

        # Menu entries
        self._add_menu_entries(menu_content, config, menu_entries, hidden_entries, css_provider)

        menu_border.append(menu_content)
        screen_box.append(menu_border)

        # Spacer
        screen_box.append(Gtk.Label(label=""))

        # Help text at bottom (centered like real GRUB)
        help_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        help_box.set_halign(Gtk.Align.CENTER)
        
        help1 = Gtk.Label(label="Use the ↑ and ↓ keys to select which entry is highlighted.")
        help1.set_halign(Gtk.Align.CENTER)
        help1.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        help1.get_style_context().add_class("grub-footer")
        help_box.append(help1)

        help2 = Gtk.Label(label="Press enter to boot the selected OS, 'e' to edit the commands")
        help2.set_halign(Gtk.Align.CENTER)
        help2.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        help2.get_style_context().add_class("grub-footer")
        help_box.append(help2)

        help3 = Gtk.Label(label="before booting or 'c' for a command-line.")
        help3.set_halign(Gtk.Align.CENTER)
        help3.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        help3.get_style_context().add_class("grub-footer")
        help_box.append(help3)

        screen_box.append(help_box)

        # Countdown timer info
        self._add_status_info(screen_box, timeout, gfxmode, css_provider)

        outer_box.append(screen_box)
        frame.set_child(outer_box)
        return frame

    @staticmethod
    def _add_menu_entries(
        box: Gtk.Box,
        config: dict[str, str],
        menu_entries: list[dict] | None = None,
        hidden_entries: list[str] | None = None,
        css_provider: Gtk.CssProvider | None = None,
    ) -> None:
        """Add menu entries to boot screen.

        Args:
            box: Container box
            config: GRUB configuration
            menu_entries: List of menu entries
            hidden_entries: List of hidden entries
            css_provider: CSS provider for styling

        """
        default_entry = config.get("GRUB_DEFAULT", "0")
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
                    entries.append(title)
        else:
            entries = [
                "Ubuntu",
                "Advanced options for Ubuntu",
                "Memory test (memtest86+x64.efi)",
                "Memory test (memtest86+x64.efi, serial console)",
            ]

        # Limit display to reasonable number
        max_visible = 8
        visible_entries = entries[:max_visible]
        
        for idx, name in enumerate(visible_entries):
            is_selected = idx == default_idx
            
            # Truncate long names like real GRUB does
            display_name = name if len(name) <= 60 else name[:57] + "..."
            
            # Create entry row with proper GRUB styling
            entry_text = f"  {display_name}  "
            label = Gtk.Label(label=entry_text)
            label.set_halign(Gtk.Align.FILL)
            label.set_xalign(0.0)
            
            if css_provider:
                label.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            
            if is_selected:
                label.get_style_context().add_class("grub-entry-selected")
            else:
                label.get_style_context().add_class("grub-entry")
            
            box.append(label)
        
        # Show indicator if more entries exist
        if len(entries) > max_visible:
            more_label = Gtk.Label(label=f"  ... ({len(entries) - max_visible} more entries)  ")
            more_label.set_halign(Gtk.Align.FILL)
            more_label.set_xalign(0.0)
            if css_provider:
                more_label.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            more_label.get_style_context().add_class("grub-entry")
            box.append(more_label)

    @staticmethod
    def _add_status_info(
        box: Gtk.Box,
        timeout: str,
        gfxmode: str,
        css_provider: Gtk.CssProvider | None = None,
    ) -> None:
        """Add status information at bottom of screen.

        Args:
            box: Container box
            timeout: Timeout value in seconds
            gfxmode: Graphics mode
            css_provider: CSS provider for styling

        """
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        info_box.set_halign(Gtk.Align.CENTER)

        # Timeout countdown (like real GRUB shows)
        try:
            timeout_int = int(timeout)
            if timeout_int > 0:
                timeout_msg = Gtk.Label(
                    label=f"The highlighted entry will be executed automatically in {timeout}s."
                )
            elif timeout_int == 0:
                timeout_msg = Gtk.Label(label="Démarrage instantané configuré (timeout=0)")
            else:
                timeout_msg = Gtk.Label(label="Menu affiché indéfiniment (timeout=-1)")
        except ValueError:
            timeout_msg = Gtk.Label(label=f"Timeout: {timeout}")
        
        timeout_msg.set_halign(Gtk.Align.CENTER)
        if css_provider:
            timeout_msg.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        timeout_msg.get_style_context().add_class("grub-countdown")
        info_box.append(timeout_msg)

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
        frame.set_label("Modifications de la configuration")
        frame.set_label_align(0.0)

        # Scrollable container for long change lists
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_max_content_height(150)
        scrolled.set_propagate_natural_height(True)

        summary_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        summary_box.set_margin_top(10)
        summary_box.set_margin_bottom(10)
        summary_box.set_margin_start(10)
        summary_box.set_margin_end(10)

        all_keys = sorted(set(old_config.keys()) | set(new_config.keys()))
        changes_count = {"added": 0, "removed": 0, "modified": 0}

        for key in all_keys:
            old_value = old_config.get(key)
            new_value = new_config.get(key)

            if old_value is None:
                # Added
                changes_count["added"] += 1
                row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                icon = Gtk.Label(label="➕")
                row.append(icon)
                label = Gtk.Label(label=f"{key} = \"{new_value}\"")
                label.set_halign(Gtk.Align.START)
                label.get_style_context().add_class("success")
                row.append(label)
                summary_box.append(row)

            elif new_value is None:
                # Removed
                changes_count["removed"] += 1
                row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                icon = Gtk.Label(label="➖")
                row.append(icon)
                label = Gtk.Label(label=f"{key} (était: \"{old_value}\")")
                label.set_halign(Gtk.Align.START)
                label.get_style_context().add_class("error")
                row.append(label)
                summary_box.append(row)

            elif old_value != new_value:
                # Modified
                changes_count["modified"] += 1
                row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                
                header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                icon = Gtk.Label(label="✏️")
                header.append(icon)
                key_label = Gtk.Label(label=key)
                key_label.set_halign(Gtk.Align.START)
                key_label.get_style_context().add_class("heading")
                header.append(key_label)
                row.append(header)

                old_label = Gtk.Label(label=f"    ⊖ \"{old_value}\"")
                old_label.set_halign(Gtk.Align.START)
                old_label.get_style_context().add_class("dim-label")
                row.append(old_label)

                new_label = Gtk.Label(label=f"    ⊕ \"{new_value}\"")
                new_label.set_halign(Gtk.Align.START)
                new_label.get_style_context().add_class("accent")
                row.append(new_label)

                summary_box.append(row)

        # Summary header if there are changes
        total = changes_count["added"] + changes_count["removed"] + changes_count["modified"]
        if total > 0:
            summary_text = []
            if changes_count["added"]:
                summary_text.append(f"{changes_count['added']} ajouté(s)")
            if changes_count["modified"]:
                summary_text.append(f"{changes_count['modified']} modifié(s)")
            if changes_count["removed"]:
                summary_text.append(f"{changes_count['removed']} supprimé(s)")
            
            header_label = Gtk.Label(label=f"📋 {total} changement(s): {', '.join(summary_text)}")
            header_label.set_halign(Gtk.Align.START)
            header_label.get_style_context().add_class("caption")
            summary_box.prepend(header_label)
            summary_box.prepend(Gtk.Separator())

        scrolled.set_child(summary_box)
        frame.set_child(scrolled)
        return frame
