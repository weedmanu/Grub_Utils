"""Tests for the command executor module."""

import os
import subprocess
from unittest.mock import MagicMock, patch

import pytest
from src.core.command_executor import SecureCommandExecutor


class TestSecureCommandExecutor:
    """Tests for SecureCommandExecutor class."""

    @pytest.fixture
    def executor(self):
        """Fixture providing a SecureCommandExecutor instance."""
        return SecureCommandExecutor()

    @patch("src.core.command_executor.subprocess.run")
    @patch("src.core.command_executor.tempfile.NamedTemporaryFile")
    @patch("src.core.command_executor.os.chmod")
    @patch("src.core.command_executor.os.geteuid")
    @patch("src.core.command_executor.os.unlink")
    @patch("src.core.command_executor.os.path.exists")
    def test_execute_with_pkexec_success_non_root(
        self,
        mock_exists,
        mock_unlink,
        mock_geteuid,
        mock_chmod,
        mock_tempfile,
        mock_run,
        executor,
    ):
        """Test successful execution via pkexec (non-root)."""
        # Setup mocks
        mock_exists.return_value = True
        mock_geteuid.return_value = 1000  # Non-root user
        
        mock_file = MagicMock()
        mock_file.name = "/tmp/script.sh"
        mock_tempfile.return_value.__enter__.return_value = mock_file

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # Execute
        commands = ["echo test"]
        success, output = executor.execute_with_pkexec(commands)

        # Verify
        assert success is True
        assert output == ""
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "pkexec"
        assert args[1] == "/tmp/script.sh"
        mock_chmod.assert_called_with("/tmp/script.sh", 0o700)
        mock_unlink.assert_called_with("/tmp/script.sh")

    @patch("src.core.command_executor.subprocess.run")
    @patch("src.core.command_executor.tempfile.NamedTemporaryFile")
    @patch("src.core.command_executor.os.chmod")
    @patch("src.core.command_executor.os.geteuid")
    @patch("src.core.command_executor.os.unlink")
    def test_execute_with_pkexec_success_root(
        self, mock_unlink, mock_geteuid, mock_chmod, mock_tempfile, mock_run, executor
    ):
        """Test successful execution as root."""
        # Setup mocks
        mock_geteuid.return_value = 0  # Root user
        mock_file = MagicMock()
        mock_file.name = "/tmp/script.sh"
        mock_tempfile.return_value.__enter__.return_value = mock_file
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Execute
        commands = ["echo test"]
        success, output = executor.execute_with_pkexec(commands)

        # Verify
        assert success is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "/tmp/script.sh"  # Direct execution

    @patch("src.core.command_executor.subprocess.run")
    @patch("src.core.command_executor.tempfile.NamedTemporaryFile")
    @patch("src.core.command_executor.os.chmod")
    @patch("src.core.command_executor.os.geteuid")
    @patch("src.core.command_executor.os.unlink")
    def test_execute_with_pkexec_failure(
        self, mock_unlink, mock_geteuid, mock_chmod, mock_tempfile, mock_run, executor
    ):
        """Test execution failure."""
        # Setup mocks
        mock_geteuid.return_value = 1000
        mock_file = MagicMock()
        mock_file.name = "/tmp/script.sh"
        mock_tempfile.return_value.__enter__.return_value = mock_file
        
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error message"
        mock_run.return_value = mock_result

        # Execute
        commands = ["invalid_command"]
        success, output = executor.execute_with_pkexec(commands)

        # Verify
        assert success is False
        assert output == "Error message"

    @patch("src.core.command_executor.subprocess.run")
    @patch("src.core.command_executor.tempfile.NamedTemporaryFile")
    @patch("src.core.command_executor.os.chmod")
    @patch("src.core.command_executor.os.geteuid")
    @patch("src.core.command_executor.os.unlink")
    def test_execute_with_pkexec_timeout(
        self, mock_unlink, mock_geteuid, mock_chmod, mock_tempfile, mock_run, executor
    ):
        """Test execution timeout."""
        # Setup mocks
        mock_geteuid.return_value = 1000
        mock_file = MagicMock()
        mock_file.name = "/tmp/script.sh"
        mock_tempfile.return_value.__enter__.return_value = mock_file
        
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["pkexec"], timeout=10)

        # Execute
        commands = ["sleep 100"]
        success, output = executor.execute_with_pkexec(commands)

        # Verify
        assert success is False
        assert "Timeout" in output

    @patch("src.core.command_executor.subprocess.run")
    @patch("src.core.command_executor.tempfile.NamedTemporaryFile")
    @patch("src.core.command_executor.os.chmod")
    @patch("src.core.command_executor.os.geteuid")
    @patch("src.core.command_executor.os.unlink")
    def test_execute_with_pkexec_exception(
        self, mock_unlink, mock_geteuid, mock_chmod, mock_tempfile, mock_run, executor
    ):
        """Test execution exception."""
        # Setup mocks
        mock_geteuid.return_value = 1000
        mock_file = MagicMock()
        mock_file.name = "/tmp/script.sh"
        mock_tempfile.return_value.__enter__.return_value = mock_file
        
        mock_run.side_effect = OSError("System error")

        # Execute
        commands = ["echo test"]
        success, output = executor.execute_with_pkexec(commands)

        # Verify
        assert success is False
        assert "Erreur système" in output

    def test_execute_with_pkexec_empty(self, executor):
        """Test execution with empty commands."""
        success, output = executor.execute_with_pkexec([])
        assert success is True
        assert output == ""

    @patch("src.core.command_executor.SecureCommandExecutor.execute_with_pkexec")
    def test_update_grub(self, mock_execute, executor):
        """Test update_grub method."""
        mock_execute.return_value = (True, "")
        
        success, output = executor.update_grub()
        
        assert success is True
        mock_execute.assert_called_once()
        commands = mock_execute.call_args[0][0]
        assert any("update-grub" in cmd for cmd in commands)

    @patch("src.core.command_executor.SecureCommandExecutor.execute_with_pkexec")
    def test_copy_file_privileged(self, mock_execute, executor):
        """Test copy_file_privileged method."""
        mock_execute.return_value = (True, "")
        
        success, output = executor.copy_file_privileged("/src", "/dst")
        
        assert success is True
        mock_execute.assert_called_once()
        commands = mock_execute.call_args[0][0]
        assert "cp '/src' '/dst'" in commands[0]

    @patch("src.core.command_executor.subprocess.run")
    @patch("src.core.command_executor.tempfile.NamedTemporaryFile")
    @patch("src.core.command_executor.os.chmod")
    @patch("src.core.command_executor.os.geteuid")
    @patch("src.core.command_executor.os.unlink")
    @patch("src.core.command_executor.os.path.exists")
    def test_execute_cleanup_fails(
        self,
        mock_exists,
        mock_unlink,
        mock_geteuid,
        mock_chmod,
        mock_tempfile,
        mock_run,
        executor,
    ):
        """Test that cleanup errors are handled gracefully."""
        # Setup mocks
        mock_exists.return_value = True
        mock_geteuid.return_value = 1000
        
        mock_file = MagicMock()
        mock_file.name = "/tmp/script.sh"
        mock_tempfile.return_value.__enter__.return_value = mock_file

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Make unlink fail
        mock_unlink.side_effect = OSError("Permission denied")

        # Execute - should succeed despite cleanup failure
        commands = ["echo test"]
        success, output = executor.execute_with_pkexec(commands)

        assert success is True
        assert output == ""
        mock_unlink.assert_called_once()

    @patch("src.core.command_executor.subprocess.run")
    @patch("src.core.command_executor.tempfile.NamedTemporaryFile")
    @patch("src.core.command_executor.os.chmod")
    @patch("src.core.command_executor.os.geteuid")
    @patch("src.core.command_executor.os.unlink")
    @patch("src.core.command_executor.os.path.exists")
    def test_execute_subprocess_error(
        self,
        mock_exists,
        mock_unlink,
        mock_geteuid,
        mock_chmod,
        mock_tempfile,
        mock_run,
        executor,
    ):
        """Test handling of subprocess.SubprocessError."""
        # Setup mocks
        mock_exists.return_value = True
        mock_geteuid.return_value = 1000
        
        mock_file = MagicMock()
        mock_file.name = "/tmp/script.sh"
        mock_tempfile.return_value.__enter__.return_value = mock_file
        
        # Raise SubprocessError
        mock_run.side_effect = subprocess.SubprocessError("Process error")

        # Execute
        commands = ["echo test"]
        success, output = executor.execute_with_pkexec(commands)

        # Verify
        assert success is False
        assert "Erreur système" in output