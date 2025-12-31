"""GRUB configuration file loader."""

import os

from src.core.exceptions import GrubConfigError
from src.utils.config import GRUB_CONFIG_PATH
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GrubConfigLoader:
    """Loads GRUB configuration from /etc/default/grub."""

    def __init__(self, config_path: str = GRUB_CONFIG_PATH):
        """Initialize the loader.

        Args:
            config_path: Path to GRUB configuration file

        """
        self.config_path = config_path

    def load(self) -> tuple[dict[str, str], list[str]]:
        """Load configuration from file.

        Returns:
            Tuple of (entries dict, raw lines)

        Raises:
            GrubConfigError: If file cannot be read

        """
        if not os.path.exists(self.config_path):
            raise GrubConfigError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path, encoding="utf-8") as f:
                lines = f.readlines()

            entries = self._parse_entries(lines)
            logger.info(
                "Configuration loaded successfully",
                extra={"path": self.config_path, "entries_count": len(entries)},
            )
            return entries, lines

        except OSError as e:
            raise GrubConfigError(f"Failed to read configuration: {e}") from e

    def _parse_entries(self, lines: list[str]) -> dict[str, str]:
        """Parse configuration entries from lines.

        Args:
            lines: Raw configuration lines

        Returns:
            Dictionary of configuration key-value pairs

        """
        entries = {}

        for line in lines:
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Parse KEY="value" or KEY=value
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                if key.startswith("export "):
                    key = key[7:].strip()
                value = value.strip().strip('"').strip("'")
                entries[key] = value

        return entries

