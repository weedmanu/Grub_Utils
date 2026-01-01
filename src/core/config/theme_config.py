"""Theme configuration manager for GRUB theme settings.

This module manages theme-specific settings in a JSON configuration file,
separate from /etc/default/grub. This allows storing all visual customization
parameters without polluting the main GRUB configuration with non-standard entries.

Configuration file: /boot/grub/themes/custom/theme_config.json
"""

import json
import os
import tempfile
from dataclasses import asdict, dataclass

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class ThemeConfiguration:
    """Theme configuration data structure (immutable)."""

    # Image de fond
    background_image: str = ""
    desktop_color: str = "#000000"

    # Menu boot
    menu_left: str = "10%"
    menu_top: str = "25%"
    menu_width: str = "80%"
    menu_height: str = "50%"
    item_height: str = "32"
    item_spacing: str = "5"
    item_padding: str = "10"

    # Couleurs
    normal_fg: str = "light-gray"
    normal_bg: str = "black"
    highlight_fg: str = "white"
    highlight_bg: str = "dark-gray"

    # Textes
    title_text: str = ""
    label_text: str = "GNU GRUB version %v"
    label_left: str = "5%"
    label_top: str = "2%"
    label_color: str = "light-gray"

    # Barre de progression
    progress_left: str = "5%"
    progress_bottom: str = "90%"
    progress_width: str = "90%"
    progress_height: str = "12"
    progress_fg: str = "light-gray"
    progress_bg: str = "black"
    progress_border: str = "white"

    # Polices (GRUB supporte uniquement "unicode" en .pf2)
    font_normal: str = "unicode"
    font_highlight: str = "unicode"
    font_label: str = "unicode"
    font_normal_size: str = "14"
    font_highlight_size: str = "16"
    font_label_size: str = "12"

    # Activation du thème
    enabled: bool = True


class ThemeConfigManager:
    """Manages theme configuration file."""

    DEFAULT_CONFIG_PATH = "/boot/grub/themes/custom/theme_config.json"

    def __init__(self, config_path: str | None = None):
        """Initialize theme config manager.

        Args:
            config_path: Path to theme_config.json (default: /boot/grub/themes/custom/theme_config.json)

        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config_dir = os.path.dirname(self.config_path)
        logger.debug("Theme config manager initialized: %s", self.config_path)

    def load(self) -> ThemeConfiguration:
        """Load theme configuration from JSON file.

        Returns:
            ThemeConfiguration object with loaded or default values

        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info("Theme configuration loaded from %s", self.config_path)
                    return ThemeConfiguration(**data)
            else:
                logger.info("No theme config found, using defaults")
                return ThemeConfiguration()
        except Exception as e:
            logger.error("Failed to load theme config: %s", e)
            return ThemeConfiguration()

    def save(self, config: ThemeConfiguration, executor=None) -> tuple[bool, str]:
        """Save theme configuration to JSON file.

        Args:
            config: ThemeConfiguration object to save
            executor: Command executor for privileged operations (required for /boot/grub/)

        Returns:
            Tuple of (success: bool, error_message: str)

        """
        if not executor:
            return False, "No executor provided for privileged operations"

        try:
            # Convert dataclass to dict
            config_dict = asdict(config)

            # Write to temporary file first
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".json") as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
                tmp_path = f.name

            logger.debug("Theme config written to temp file: %s", tmp_path)

            # Create directory if needed
            mkdir_cmd = f"mkdir -p {self.config_dir}"
            success, error = executor.execute_with_pkexec([mkdir_cmd])
            if not success:
                os.unlink(tmp_path)
                return False, f"Failed to create config directory: {error}"

            # Copy to system location
            success, error = executor.copy_file_privileged(tmp_path, self.config_path)
            os.unlink(tmp_path)

            if not success:
                return False, f"Failed to copy config file: {error}"

            logger.info("Theme configuration saved to %s", self.config_path)
            return True, ""

        except Exception as e:
            error_msg = f"Failed to save theme config: {e}"
            logger.error(error_msg)
            return False, error_msg

    def load_from_grub_config(self, grub_entries: dict[str, str]) -> ThemeConfiguration:
        """Load theme configuration from old GRUB config format.

        This is used for migration from the old system where theme settings
        were stored in /etc/default/grub.

        Args:
            grub_entries: Dictionary of GRUB configuration entries

        Returns:
            ThemeConfiguration object populated from GRUB entries

        """
        # Construct dictionary first for frozen dataclass
        normal_colors = grub_entries.get("GRUB_COLOR_NORMAL", "light-gray/black").split("/")
        normal_fg = normal_colors[0].strip() if len(normal_colors) == 2 else "light-gray"
        normal_bg = normal_colors[1].strip() if len(normal_colors) == 2 else "black"

        highlight_colors = grub_entries.get("GRUB_COLOR_HIGHLIGHT", "white/dark-gray").split("/")
        highlight_fg = highlight_colors[0].strip() if len(highlight_colors) == 2 else "white"
        highlight_bg = highlight_colors[1].strip() if len(highlight_colors) == 2 else "dark-gray"

        logger.info("Theme configuration migrated from GRUB config")
        return ThemeConfiguration(
            background_image=grub_entries.get("GRUB_BACKGROUND", ""),
            normal_fg=normal_fg,
            normal_bg=normal_bg,
            highlight_fg=highlight_fg,
            highlight_bg=highlight_bg,
            menu_left=grub_entries.get("GRUB_MENU_LEFT", "10%"),
            menu_top=grub_entries.get("GRUB_MENU_TOP", "25%"),
            menu_width=grub_entries.get("GRUB_MENU_WIDTH", "80%"),
            menu_height=grub_entries.get("GRUB_MENU_HEIGHT", "50%"),
            item_height=grub_entries.get("GRUB_ITEM_HEIGHT", "32"),
            item_spacing=grub_entries.get("GRUB_ITEM_SPACING", "5"),
            item_padding=grub_entries.get("GRUB_ITEM_PADDING", "10"),
            title_text=grub_entries.get("GRUB_TITLE_TEXT", ""),
            label_text=grub_entries.get("GRUB_LABEL_TEXT", "GNU GRUB version %v"),
            label_left=grub_entries.get("GRUB_LABEL_LEFT", "5%"),
            label_top=grub_entries.get("GRUB_LABEL_TOP", "2%"),
            label_color=grub_entries.get("GRUB_LABEL_COLOR", "light-gray"),
            progress_left=grub_entries.get("GRUB_PROGRESS_LEFT", "5%"),
            progress_bottom=grub_entries.get("GRUB_PROGRESS_BOTTOM", "90%"),
            progress_width=grub_entries.get("GRUB_PROGRESS_WIDTH", "90%"),
            progress_height=grub_entries.get("GRUB_PROGRESS_HEIGHT", "12"),
            progress_fg=grub_entries.get("GRUB_PROGRESS_FG", "light-gray"),
            progress_bg=grub_entries.get("GRUB_PROGRESS_BG", "black"),
            progress_border=grub_entries.get("GRUB_PROGRESS_BORDER", "white"),
            enabled=grub_entries.get("GRUB_USE_THEME", "true").lower() == "true",
        )
