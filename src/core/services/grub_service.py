"""GRUB service for orchestrating configuration operations."""

import os
import tempfile

from src.core.backup_manager import BackupManager
from src.core.command_executor import SecureCommandExecutor
from src.core.config.generator import GrubConfigGenerator
from src.core.config.loader import GrubConfigLoader
from src.core.config.parser import GrubMenuParser
from src.core.exceptions import (
    GrubApplyError,
    GrubConfigError,
    GrubServiceError,
)
from src.core.validator import GrubValidator
from src.utils.config import GRUB_CFG_PATHS, GRUB_CONFIG_PATH
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GrubService:  # pylint: disable=too-many-instance-attributes
    """Main service for GRUB configuration management."""

    def __init__(self, config_path: str = GRUB_CONFIG_PATH):
        """Initialize the GRUB service.

        Args:
            config_path: Path to GRUB configuration file

        """
        self.config_path = config_path

        # Initialize components
        self.loader = GrubConfigLoader(config_path)
        self.parser = GrubMenuParser()
        self.generator = GrubConfigGenerator()
        self.validator = GrubValidator()
        self.backup_manager = BackupManager(config_path)
        self.executor = SecureCommandExecutor()

        # State
        self.entries: dict[str, str] = {}
        self.original_lines: list[str] = []
        self.menu_entries: list[dict] = []
        self.hidden_entries: list[str] = []
        self._loaded = False

    def load(self) -> None:
        """Load GRUB configuration.

        Raises:
            GrubConfigError: If configuration cannot be loaded

        """
        try:
            self.entries, self.original_lines = self.loader.load()
            self.menu_entries = self.parser.parse_menu_entries()
            self._loaded = True

            logger.info(
                "GRUB configuration loaded",
                extra={
                    "config_entries": len(self.entries),
                    "menu_entries": len(self.menu_entries),
                },
            )
        except (OSError, ValueError) as e:
            logger.error("Failed to load configuration: %s", e)
            raise GrubServiceError(f"Load failed: {e}") from e

    def save_and_apply(self) -> tuple[bool, str]:
        """Save configuration and apply changes.

        Returns:
            Tuple of (success, error_message)

        """
        if not self._loaded:
            return False, "Configuration not loaded"

        try:
            # Validate configuration
            self.validator.validate_all(self.entries)

            # Create backup
            backup_path = self.backup_manager.create_backup()
            logger.info("Backup created: %s", backup_path)

            # Generate new configuration
            new_content = self.generator.generate(self.entries, self.original_lines, self.hidden_entries)

            # Write to file
            success, error = self._write_config(new_content)
            if not success:
                return False, error

            # Update GRUB
            success, error = self._update_grub()
            if not success:
                # Try to restore backup on failure
                self.backup_manager.restore_backup(backup_path)
                return False, error

            # Apply hidden entries
            success, error = self._apply_hidden_entries()
            if not success:
                logger.error("Failed to apply hidden entries: %s", error)
                # We don't fail the whole operation, but we log it.
                # Or should we fail? The user expects entries to be hidden.
                # Let's fail.
                self.backup_manager.restore_backup(backup_path)
                return False, error

            logger.info("GRUB configuration applied successfully")
            return True, ""

        except (GrubConfigError, GrubApplyError, OSError) as e:
            logger.exception("Failed to apply configuration")
            return False, str(e)

    def _write_config(self, content: str) -> tuple[bool, str]:
        """Write configuration to file.

        Args:
            content: New configuration content

        Returns:
            Tuple of (success, error_message)

        """
        try:
            # Write to temp file first
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".grub") as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            # Copy with elevated privileges
            success, output = self.executor.copy_file_privileged(tmp_path, self.config_path)

            # Cleanup temp file
            os.unlink(tmp_path)

            if not success:
                return False, f"Failed to write config: {output}"

            return True, ""

        except OSError as e:
            logger.exception("Failed to write configuration")
            return False, str(e)

    def _update_grub(self) -> tuple[bool, str]:
        """Update GRUB bootloader.

        Returns:
            Tuple of (success, error_message)

        """
        try:
            success, output = self.executor.update_grub()
            if not success:
                return False, f"update-grub failed: {output}"
            return True, ""
        except (OSError, RuntimeError) as e:
            return False, str(e)

    def restore_backup(self, backup_path: str | None = None) -> bool:
        """Restore from backup.

        Args:
            backup_path: Specific backup to restore (latest if None)

        Returns:
            True if successful

        """
        try:
            restored_path = self.backup_manager.restore_backup(backup_path)
            logger.info("Restored backup: %s", restored_path)

            # Reload configuration
            self.load()

            # Update GRUB
            success, _ = self._update_grub()
            return success

        except (GrubConfigError, OSError) as e:
            logger.exception("Failed to restore backup: %s", e)
            return False

    def _apply_hidden_entries(self) -> tuple[bool, str]:
        """Apply hidden entries to grub.cfg by removing them.

        Returns:
            Tuple of (success, error_message)

        """
        if not self.hidden_entries:
            return True, ""

        # Find grub.cfg
        grub_cfg_path = None
        for path in GRUB_CFG_PATHS:
            if os.path.exists(path):
                grub_cfg_path = path
                break
        
        if not grub_cfg_path:
            logger.warning("grub.cfg not found, cannot hide entries")
            return True, ""

        try:
            with open(grub_cfg_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            new_lines = []
            skipping = False
            skip_level = 0
            current_level = 0

            for line in lines:
                stripped = line.strip()
                
                is_entry_start = stripped.startswith("menuentry ") or stripped.startswith("submenu ")
                
                if not skipping and is_entry_start:
                    parts = stripped.split("'")
                    if len(parts) >= 2:
                        title = parts[1]
                        if title in self.hidden_entries:
                            skipping = True
                            skip_level = current_level

                open_braces = line.count("{")
                close_braces = line.count("}")
                
                if skipping:
                    current_level += open_braces
                    current_level -= close_braces
                    
                    if current_level <= skip_level:
                        skipping = False
                    
                    continue

                new_lines.append(line)
                current_level += open_braces
                current_level -= close_braces

            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".cfg") as tmp:
                tmp.writelines(new_lines)
                tmp_path = tmp.name

            success, output = self.executor.copy_file_privileged(tmp_path, grub_cfg_path)
            os.unlink(tmp_path)

            if not success:
                return False, f"Failed to apply hidden entries: {output}"

            return True, ""

        except (OSError, IOError) as e:
            logger.exception("Failed to apply hidden entries")
            return False, str(e)
