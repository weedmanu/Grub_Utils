"""Pytest configuration and shared fixtures."""

import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def temp_grub_config() -> Generator[Path, None, None]:
    """Create a temporary GRUB configuration file.

    Yields:
        Path to temporary config file
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
        f.write('GRUB_DEFAULT="0"\n')
        f.write('GRUB_TIMEOUT="5"\n')
        f.write('GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"\n')
        f.write('GRUB_GFXMODE="auto"\n')
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    temp_path.unlink(missing_ok=True)


@pytest.fixture
def sample_grub_entries() -> dict[str, str]:
    """Sample GRUB configuration entries.

    Returns:
        Dictionary of GRUB configuration key-value pairs
    """
    return {
        "GRUB_DEFAULT": "0",
        "GRUB_TIMEOUT": "5",
        "GRUB_CMDLINE_LINUX_DEFAULT": "quiet splash",
        "GRUB_GFXMODE": "1024x768",
        "GRUB_BACKGROUND": "/boot/grub/background.png",
        "GRUB_THEME": "/boot/grub/themes/default",
    }


@pytest.fixture
def sample_menu_entries() -> list[dict]:
    """Sample menu entries.

    Returns:
        List of menu entry dictionaries
    """
    return [
        {"title": "Ubuntu", "linux": "/vmlinuz-5.15.0", "submenu": False},
        {"title": "Ubuntu (recovery)", "linux": "/vmlinuz-5.15.0", "submenu": False},
        {"title": "Windows Boot Manager", "linux": "", "submenu": False},
    ]


@pytest.fixture
def temp_backup_dir() -> Generator[Path, None, None]:
    """Create a temporary backup directory.

    Yields:
        Path to temporary backup directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_grub_service(mocker):
    """Mock GrubService for UI tests.

    Args:
        mocker: Pytest-mock fixture

    Returns:
        Mocked GrubService instance
    """
    from src.core.services.grub_service import GrubService

    service = mocker.Mock(spec=GrubService)
    service.entries = {
        "GRUB_DEFAULT": "0",
        "GRUB_TIMEOUT": "5",
        "GRUB_CMDLINE_LINUX_DEFAULT": "quiet splash",
    }
    service.menu_entries = []
    service.hidden_entries = []
    return service


@pytest.fixture(autouse=True)
def mock_sudo_commands():
    """Mock all sudo/pkexec commands automatically for all tests.

    This prevents password prompts during test execution.
    Tests can override this fixture if they need real command execution.
    """
    with patch('subprocess.run') as mock_run, \
         patch('subprocess.Popen') as mock_popen, \
         patch('os.geteuid', return_value=0):  # Simulate root user
        
        # Configure mock to return success by default
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Mock output",
            stderr=""
        )
        
        mock_process = Mock()
        mock_process.communicate.return_value = (b"Mock output", b"")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        yield {
            'run': mock_run,
            'popen': mock_popen
        }
