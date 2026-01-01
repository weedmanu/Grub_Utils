"""Integration tests for GrubFacade with real components."""

import tempfile
from pathlib import Path

import pytest

from src.core.facade import GrubFacade


@pytest.mark.integration
class TestGrubFacadeIntegration:
    """Integration tests for GrubFacade."""

    @pytest.fixture
    def temp_grub_file(self):
        """Create a temporary GRUB configuration file.

        Yields:
            Path to temporary file

        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            f.write('GRUB_DEFAULT="0"\n')
            f.write('GRUB_TIMEOUT="5"\n')
            f.write('GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"\n')
            f.write('GRUB_GFXMODE="auto"\n')
            path = Path(f.name)

        yield path

        # Cleanup
        path.unlink(missing_ok=True)

    @pytest.fixture
    def facade(self, temp_grub_file, mocker):
        """Create a GrubFacade with real file.

        Args:
            temp_grub_file: Temporary GRUB config file
            mocker: Pytest mocker fixture

        Returns:
            GrubFacade instance

        """
        facade = GrubFacade(str(temp_grub_file))
        # Mock le parser pour éviter accès à /boot/grub/grub.cfg
        mocker.patch.object(
            facade._service.parser,
            "parse_menu_entries",
            return_value=[{"title": "Ubuntu", "linux": "/vmlinuz", "submenu": False}],
        )
        return facade

    def test_load_and_get_configuration(self, facade):
        """Test loading and retrieving configuration."""
        # Load
        result = facade.load_configuration()
        assert result.success is True

        # Get
        assert facade.entries["GRUB_DEFAULT"] == "0"
        assert facade.entries["GRUB_TIMEOUT"] == "5"
        assert facade.entries["GRUB_CMDLINE_LINUX_DEFAULT"] == "quiet splash"

    def test_update_and_retrieve_configuration(self, facade):
        """Test updating configuration and retrieving it back."""
        # Load first
        facade.load_configuration()

        # Update
        facade.entries["GRUB_DEFAULT"] = "saved"
        facade.entries["GRUB_TIMEOUT"] = "10"
        facade.entries["GRUB_CMDLINE_LINUX_DEFAULT"] = "quiet splash nomodeset"
        facade.entries["GRUB_GFXMODE"] = "1920x1080"
        facade.entries["GRUB_BACKGROUND"] = "/boot/grub/bg.png"

        # Retrieve
        assert facade.entries["GRUB_DEFAULT"] == "saved"
        assert facade.entries["GRUB_TIMEOUT"] == "10"
        assert facade.entries["GRUB_BACKGROUND"] == "/boot/grub/bg.png"

    def test_full_workflow_load_update_apply(self, facade, mocker):
        """Test complete workflow: load -> update -> apply."""
        # Mock save_and_apply to avoid system changes
        mocker.patch.object(facade._service, "save_and_apply", return_value=(True, ""))

        # Load
        load_result = facade.load_configuration()
        assert load_result.success is True

        # Update
        facade.entries["GRUB_DEFAULT"] = "0"
        facade.entries["GRUB_TIMEOUT"] = "15"
        facade.entries["GRUB_CMDLINE_LINUX_DEFAULT"] = "quiet"
        facade.entries["GRUB_GFXMODE"] = "auto"

        # Apply
        apply_result = facade.apply_changes()
        assert apply_result.success is True
