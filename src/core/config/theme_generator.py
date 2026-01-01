"""GRUB theme.txt file generator for custom themes.

This module orchestrates GRUB2 theme file creation and installation.
It handles file I/O operations with elevated privileges while delegating
content generation to ThemeContentBuilder (Single Responsibility Principle).

References:
    - GNU GRUB Manual: https://www.gnu.org/software/grub/manual/grub/
    - GRUB2 gfxmenu Specification

"""

import os
import tempfile

from src.core.config.theme_config import ThemeConfiguration
from src.core.config.theme_content_builder import ThemeContentBuilder
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GrubThemeGenerator:
    """Orchestrates GRUB theme file creation and installation.

    Responsibilities (following Single Responsibility Principle):
    - Theme directory management with elevated privileges
    - File I/O operations (creating directories, copying files)
    - Background image installation
    - Delegating content generation to ThemeContentBuilder

    Content generation is handled by ThemeContentBuilder for clean separation.

    References:
    - GNU GRUB Manual: https://www.gnu.org/software/grub/manual/grub/
    - GRUB2 Theme Specification: /boot/grub/themes/*/theme.txt

    """

    # Default theme directory for custom themes
    DEFAULT_THEME_DIR = "/boot/grub/themes/custom"

    def __init__(self, theme_dir: str | None = None):
        """Initialize theme generator.

        Args:
            theme_dir: Directory for theme files (default: /boot/grub/themes/custom)
                      Must be an absolute path starting with /boot/grub/

        Raises:
            ValueError: If theme_dir is not in /boot/grub/ hierarchy

        """
        self.theme_dir = theme_dir or self.DEFAULT_THEME_DIR

        # Security: ensure theme directory is in proper location
        if not self.theme_dir.startswith("/boot/grub/"):
            raise ValueError(f"Theme directory must be in /boot/grub/ hierarchy, got: {self.theme_dir}")

        logger.debug("Theme generator initialized with theme_dir: %s", self.theme_dir)

    def remove_theme(self, executor, keep_backup: bool = True) -> tuple[bool, str]:
        """Remove theme.txt file, optionally keeping backup.

        Args:
            executor: Command executor for privileged operations
            keep_backup: If True, keep theme.txt.bak file

        Returns:
            Tuple of (success: bool, error_message: str)

        """
        if not executor:
            return False, "No executor provided for privileged operations"

        try:
            theme_path = os.path.join(self.theme_dir, "theme.txt")
            backup_path = os.path.join(self.theme_dir, "theme.txt.bak")

            # Backup existing theme.txt before removing it
            if os.path.exists(theme_path):
                if keep_backup and not os.path.exists(backup_path):
                    # Create backup first
                    success, error = executor.execute_with_pkexec([f"cp {theme_path} {backup_path}"])
                    if not success:
                        logger.warning("Failed to create backup before removing theme: %s", error)

                # Remove theme.txt
                success, error = executor.execute_with_pkexec([f"rm -f {theme_path}"])
                if not success:
                    error_msg = f"Failed to remove theme.txt: {error}"
                    logger.error(error_msg)
                    return False, error_msg

                logger.info("Theme file removed: %s (backup kept: %s)", theme_path, keep_backup)
                return True, ""

            logger.info("No theme.txt to remove")
            return True, ""

        except Exception as e:
            error_msg = f"Failed to remove theme: {e}"
            logger.error(error_msg)
            return False, error_msg

    def generate_theme_from_config(
        self,
        theme_config: ThemeConfiguration,
        executor=None,
    ) -> tuple[bool, str, str]:
        """Generate complete theme.txt file from ThemeConfiguration object.

        Delegates content generation to ThemeContentBuilder and handles file I/O.

        Args:
            theme_config: ThemeConfiguration object with all theme settings
            executor: Command executor for privileged operations (required for file writes)

        Returns:
            Tuple of (success: bool, theme_path: str, error_message: str)

        """
        try:
            logger.debug("Starting theme generation from ThemeConfiguration")

            # Delegate content generation to ThemeContentBuilder
            theme_content = ThemeContentBuilder.build(theme_config)

            # Create theme directory and write files
            theme_path = os.path.join(self.theme_dir, "theme.txt")
            success, error = self._write_theme_files(
                theme_content,
                theme_config.background_image,
                executor,
            )

            if not success:
                return False, "", error

            logger.info("Theme generated successfully: %s", theme_path)
            return True, theme_path, ""

        except Exception as e:
            error_msg = f"Theme generation failed: {e}"
            logger.exception("Theme generation error")
            return False, "", error_msg

    def _write_theme_files(
        self,
        theme_content: str,
        background_path: str,
        executor,
    ) -> tuple[bool, str]:
        """Write theme files to disk with elevated privileges.

        Creates the necessary directory structure and writes both the theme.txt
        configuration and background image to the designated theme directory.
        Operations require root privileges via pkexec/sudo.

        Args:
            theme_content: Content of theme.txt file
            background_path: Path to background image file
            executor: Command executor for privileged operations

        Returns:
            Tuple of (success: bool, error_message: str)

        Raises:
            OSError: If file operations fail
            IOError: If I/O operations fail

        """
        if not executor:
            error_msg = "No executor provided for privileged operations"
            logger.error(error_msg)
            return False, error_msg

        try:
            # Create temporary directory for theme files
            with tempfile.TemporaryDirectory() as tmp_dir:
                logger.debug("Using temporary directory: %s", tmp_dir)

                # Write theme.txt to temporary location first
                tmp_theme_path = os.path.join(tmp_dir, "theme.txt")
                with open(tmp_theme_path, "w", encoding="utf-8") as f:
                    f.write(theme_content)

                theme_file_size = len(theme_content.encode("utf-8"))
                logger.debug("Theme file written to temp: %s (%d bytes)", tmp_theme_path, theme_file_size)

                # Create theme directory with proper permissions
                mkdir_cmd = f"mkdir -p {self.theme_dir}"
                success, error = executor.execute_with_pkexec([mkdir_cmd])
                if not success:
                    error_msg = f"Failed to create theme directory '{self.theme_dir}': {error}"
                    logger.error(error_msg)
                    return False, error_msg

                logger.info("Theme directory created: %s", self.theme_dir)

                # Copy theme.txt to system location
                theme_dest = os.path.join(self.theme_dir, "theme.txt")
                success, error = executor.copy_file_privileged(tmp_theme_path, theme_dest)
                if not success:
                    error_msg = f"Failed to copy theme.txt to {theme_dest}: {error}"
                    logger.error(error_msg)
                    return False, error_msg

                logger.info("Theme file installed: %s", theme_dest)

                # Copy background image if provided
                if background_path:
                    if not os.path.exists(background_path):
                        logger.warning("Background image not found: %s (theme will use default)", background_path)
                    else:
                        bg_filename = os.path.basename(background_path)
                        bg_dest = os.path.join(self.theme_dir, bg_filename)

                        # Validate image file
                        file_size = os.path.getsize(background_path)
                        logger.debug("Copying background image: %s (%d bytes)", background_path, file_size)

                        success, error = executor.copy_file_privileged(background_path, bg_dest)
                        if not success:
                            logger.warning(
                                "Failed to copy background image '%s' to %s: %s. "
                                "Theme will work without background.",
                                background_path,
                                bg_dest,
                                error,
                            )
                            # Don't fail the whole operation - theme works without background
                        else:
                            logger.info("Background image installed: %s", bg_dest)

                logger.info("Theme files successfully written to: %s", self.theme_dir)
                return True, ""

        except OSError as e:
            error_msg = f"File I/O error while writing theme files: {e}"
            logger.exception(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error while writing theme files: {e}"
            logger.exception(error_msg)
            return False, error_msg
