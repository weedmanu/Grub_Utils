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

            logger.debug("[LOADER] Lecture de %d lignes depuis %s", len(lines), self.config_path)
            entries = self._parse_entries(lines)
            logger.debug("[LOADER] %d entrées parsées", len(entries))
            logger.info(
                "Configuration loaded successfully",
                extra={"path": self.config_path, "entries_count": len(entries)},
            )
            return entries, lines

        except OSError as e:
            raise GrubConfigError(f"Failed to read configuration: {e}") from e

    def reload(self) -> tuple[dict[str, str], list[str]]:
        """Recharge la configuration depuis le fichier.

        Utile pour rafraîchir la configuration après des modifications externes.

        Returns:
            Tuple of (entries dict, raw lines)

        Raises:
            GrubConfigError: If file cannot be read

        """
        return self.load()

    def get_value(self, key: str, default: str | None = None) -> str | None:
        """Récupère une valeur spécifique de la configuration.

        Args:
            key: Clé de configuration à récupérer
            default: Valeur par défaut si la clé n'existe pas

        Returns:
            Valeur de la clé ou default

        Raises:
            GrubConfigError: Si le fichier ne peut pas être lu

        """
        entries, _ = self.load()
        return entries.get(key, default)

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
