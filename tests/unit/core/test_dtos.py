"""Unit tests for Data Transfer Objects."""

import pytest

from src.core.dtos import BackupInfoDTO, OperationResultDTO


@pytest.mark.unit
class TestBackupInfoDTO:
    """Test suite for BackupInfoDTO."""

    def test_create_backup_info(self):
        """Test creating backup info DTO."""
        import time

        timestamp = time.time()
        backup = BackupInfoDTO(
            path="/home/user/.local/share/grub_manager/backups/grub.bak.123456",
            timestamp=timestamp,
            size_bytes=1024,
            is_valid=True,
        )

        assert backup.path.endswith("grub.bak.123456")
        assert backup.timestamp == timestamp
        assert backup.size_bytes == 1024
        assert backup.is_valid is True


@pytest.mark.unit
class TestOperationResultDTO:
    """Test suite for OperationResultDTO."""

    def test_successful_operation(self):
        """Test creating a successful operation result."""
        result = OperationResultDTO(success=True, message="Configuration applied")

        assert result.success is True
        assert result.message == "Configuration applied"
        assert result.error_details is None

    def test_failed_operation_with_details(self):
        """Test creating a failed operation result with error details."""
        result = OperationResultDTO(
            success=False,
            message="Validation failed",
            error_details="Timeout value must be between 0 and 300",
        )

        assert result.success is False
        assert result.message == "Validation failed"
        assert "Timeout value" in result.error_details
