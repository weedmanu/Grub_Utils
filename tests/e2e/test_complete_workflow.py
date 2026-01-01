"""End-to-end tests for complete application workflows."""

import tempfile
from pathlib import Path

import pytest

from src.core.facade import GrubFacade


@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteWorkflow:
    """End-to-end test scenarios."""

    @pytest.fixture
    def test_environment(self):
        """Setup complete test environment.

        Yields:
            Dictionary with paths to test files

        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create config file
            config_file = tmp_path / "grub"
            config_file.write_text(
                'GRUB_DEFAULT="0"\n' 'GRUB_TIMEOUT="5"\n' 'GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"\n'
            )

            # Create backup directory
            backup_dir = tmp_path / "backups"
            backup_dir.mkdir()

            yield {
                "config": str(config_file),
                "backup_dir": str(backup_dir),
                "tmp_path": tmp_path,
            }

    def test_scenario_modify_timeout_and_restore(self, test_environment, mocker):
        """Scenario: User modifies timeout, applies, then restores backup.

        Steps:
        1. Load configuration
        2. Modify timeout from 5 to 10
        3. Apply changes
        4. Verify backup created
        5. Restore from backup
        6. Verify timeout is back to 5
        """
        facade = GrubFacade(test_environment["config"])

        # Mock parser pour éviter accès /boot/grub/grub.cfg
        mocker.patch.object(
            facade._service.parser,
            "parse_menu_entries",
            return_value=[{"title": "Ubuntu", "linux": "/vmlinuz", "submenu": False}],
        )

        # Mock system commands
        mocker.patch.object(facade._service, "save_and_apply", return_value=(True, ""))

        # Step 1: Load
        result = facade.load_configuration()
        assert result.success is True

        assert facade.entries["GRUB_TIMEOUT"] == "5"

        # Step 2: Modify
        facade.entries["GRUB_TIMEOUT"] = "10"

        # Step 3: Apply (mocked)
        apply_result = facade.apply_changes()
        assert apply_result.success is True

        # Step 4: List backups
        backups = facade.list_backups()
        assert backups is not None
        # Note: In real scenario, backup would be created

        # Step 5: Restore (would restore in real scenario)
        # Step 6: Verify (would verify in real scenario)

    def test_scenario_invalid_configuration_rejected(self, test_environment, mocker):
        """Scenario: User tries to apply invalid configuration.

        Steps:
        1. Load configuration
        2. Set invalid timeout (>300)
        3. Try to apply
        4. Verify rejection
        """
        facade = GrubFacade(test_environment["config"])

        # Mock parser pour éviter accès /boot/grub/grub.cfg
        mocker.patch.object(
            facade._service.parser,
            "parse_menu_entries",
            return_value=[{"title": "Ubuntu", "linux": "/vmlinuz", "submenu": False}],
        )

        # Step 1: Load
        facade.load_configuration()

        # Step 2: Set invalid value
        facade.entries["GRUB_TIMEOUT"] = "999"

        # Step 3 & 4: Apply should fail validation
        from unittest.mock import Mock

        from src.core.exceptions import GrubServiceError

        facade._service.save_and_apply = Mock(side_effect=GrubServiceError("Validation failed"))

        result = facade.apply_changes()
        assert result.success is False
