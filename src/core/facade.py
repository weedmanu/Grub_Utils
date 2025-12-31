"""Facade for GRUB configuration management."""

import os

from src.core.dtos import BackupInfoDTO, OperationResultDTO
from src.core.exceptions import GrubConfigError, GrubServiceError
from src.core.services.grub_service import GrubService
from src.utils.config import GRUB_CONFIG_PATH
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GrubFacade:
    """Facade providing simplified API for GRUB management."""

    def __init__(self, config_path: str = GRUB_CONFIG_PATH):
        """Initialize the facade.

        Args:
            config_path: Path to GRUB configuration file

        """
        self._service = GrubService(config_path)
        self._loaded = False

    def load_configuration(self) -> OperationResultDTO:
        """Load GRUB configuration from disk.

        Returns:
            Result of the operation

        """
        try:
            self._service.load()
            self._loaded = True
            return OperationResultDTO(success=True, message="Configuration loaded successfully")
        except (GrubServiceError, GrubConfigError) as e:
            logger.exception("Failed to load configuration")
            return OperationResultDTO(success=False, message="Failed to load configuration", error_details=str(e))

    def apply_changes(self) -> OperationResultDTO:
        """Apply configuration changes to the system.

        Returns:
            Result of the operation

        """
        if not self._loaded:
            return OperationResultDTO(
                success=False, message="Configuration not loaded. Call load_configuration() first."
            )

        try:
            success, error = self._service.save_and_apply()

            if success:
                return OperationResultDTO(success=True, message="Configuration applied successfully")
            return OperationResultDTO(success=False, message="Failed to apply configuration", error_details=error)

        except (GrubServiceError, GrubConfigError) as e:
            logger.exception("Failed to apply changes")
            return OperationResultDTO(success=False, message="Failed to apply changes", error_details=str(e))

    def list_backups(self) -> list[BackupInfoDTO]:
        """List available backups.

        Returns:
            List of backup information DTOs

        """
        backups = self._service.backup_manager.list_backups()

        return [
            BackupInfoDTO(
                path=backup_path,
                timestamp=os.path.getmtime(backup_path),
                size_bytes=os.path.getsize(backup_path),
                is_valid=os.path.exists(backup_path) and os.path.getsize(backup_path) > 0,
            )
            for backup_path in backups
        ]

    def restore_backup(self, backup_path: str | None = None) -> OperationResultDTO:
        """Restore configuration from a backup.

        Args:
            backup_path: Path to specific backup (uses latest if None)

        Returns:
            Result of the operation

        """
        try:
            success = self._service.restore_backup(backup_path)

            if success:
                self._loaded = True
                return OperationResultDTO(success=True, message="Backup restored successfully")
            return OperationResultDTO(success=False, message="Failed to restore backup")

        except (GrubServiceError, GrubConfigError, OSError) as e:
            logger.exception("Failed to restore backup")
            return OperationResultDTO(success=False, message="Failed to restore backup", error_details=str(e))

    # Public accessors pour éviter protected-access dans UI
    @property
    def entries(self) -> dict[str, str]:
        """Get current configuration entries."""
        return self._service.entries

    @entries.setter
    def entries(self, value: dict[str, str]) -> None:
        """Set configuration entries."""
        self._service.entries = value

    @property
    def menu_entries(self) -> list[dict]:
        """Get menu entries."""
        return self._service.menu_entries

    @property
    def hidden_entries(self) -> list[str]:
        """Get hidden menu entries."""
        return self._service.hidden_entries

    @hidden_entries.setter
    def hidden_entries(self, value: list[str]) -> None:
        """Set hidden menu entries."""
        self._service.hidden_entries = value

    def has_backups(self) -> bool:
        """Check if backups are available."""
        return bool(self._service.backup_manager.get_latest_backup())
