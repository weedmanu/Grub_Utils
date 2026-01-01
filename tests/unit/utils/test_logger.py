"""Tests for the logger module."""

import logging
import os
from unittest.mock import MagicMock, mock_open, patch

from src.utils.logger import get_log_path, get_logger, setup_logging


class TestLogger:
    """Tests for logger configuration."""

    @patch("src.utils.logger.os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_get_log_path_system(self, mock_file, mock_makedirs):
        """Test getting log path when system path is writable."""
        path = get_log_path()
        assert path == "/var/log/grub-manager/app.log"
        mock_makedirs.assert_called_with("/var/log/grub-manager", exist_ok=True)

    @patch("src.utils.logger.os.makedirs")
    @patch("builtins.open")
    def test_get_log_path_user_fallback(self, mock_file, mock_makedirs):
        """Test fallback to user path when system path is not writable."""
        # Simulate permission error on system path
        mock_file.side_effect = PermissionError("Permission denied")

        path = get_log_path()

        expected_path = os.path.expanduser("~/.local/share/grub-manager/app.log")
        assert path == expected_path
        # Should have tried system path first, then user path
        assert mock_makedirs.call_count == 2

    def test_get_logger(self):
        """Test getting a logger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "grub_manager.test_module"

    @patch("src.utils.logger.get_log_path")
    @patch("src.utils.logger.logging.getLogger")
    @patch("src.utils.logger.logging.handlers.RotatingFileHandler")
    def test_setup_logging(self, mock_handler, mock_get_logger, mock_get_path):
        """Test logging setup."""
        mock_get_path.return_value = "/tmp/test.log"
        mock_root = MagicMock()
        mock_get_logger.return_value = mock_root

        setup_logging(debug=True)

        mock_get_logger.assert_called_with("grub_manager")
        mock_root.setLevel.assert_called_with(logging.DEBUG)
        mock_handler.assert_called_with("/tmp/test.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
        assert mock_root.addHandler.call_count == 2  # File + Console
