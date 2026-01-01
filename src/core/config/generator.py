"""GRUB configuration file generator."""

# GrubConfigGenerator pourrait avoir plus de méthodes, mais respecte SRP
# pylint: disable=too-few-public-methods

from src.core.config.line_processor import GrubLineProcessor, NewEntriesAppender
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GrubConfigGenerator:
    """Generates new GRUB configuration content."""

    def __init__(self):
        """Initialise le générateur avec les clés à exporter."""
        self.keys_to_export = {"GRUB_COLOR_NORMAL", "GRUB_COLOR_HIGHLIGHT"}

    def generate(
        self,
        entries: dict[str, str],
        original_lines: list[str],
        hidden_entries: list[str] | None = None,
    ) -> str:
        """Generate new configuration content.

        Args:
            entries: Configuration key-value pairs
            original_lines: Original file lines to preserve comments/structure
            hidden_entries: List of entries to hide (prefix with #)

        Returns:
            New configuration content as string

        """
        hidden_set = set(hidden_entries or [])

        logger.debug(
            "[GENERATOR] Génération - GRUB_BACKGROUND présent: %s, valeur: '%s'",
            "GRUB_BACKGROUND" in entries,
            entries.get("GRUB_BACKGROUND", "N/A"),
        )
        logger.debug("[GENERATOR] Toutes les entrées: %s", list(entries.keys()))

        # Traiter les lignes existantes
        processor = GrubLineProcessor(self.keys_to_export, hidden_set)
        new_lines = [processor.process_line(line, entries) for line in original_lines]

        # Compter les lignes supprimées
        removed_count = sum(1 for line in new_lines if line is None)
        logger.debug("[GENERATOR] Lignes supprimées: %d", removed_count)

        # Filtrer les None (lignes supprimées)
        filtered_lines: list[str] = [line for line in new_lines if line is not None]

        # Ajouter les nouvelles entrées
        appender = NewEntriesAppender(self.keys_to_export, hidden_set)
        new_entries = appender.find_new_entries(entries, original_lines)
        logger.debug("[GENERATOR] Nouvelles entrées ajoutées: %d", len(new_entries))
        filtered_lines.extend(new_entries)

        logger.debug(
            "[GENERATOR] Configuration générée",
            extra={"entries_count": len(entries), "lines_count": len(filtered_lines)},
        )

        result = "\n".join(filtered_lines) + "\n"

        # Vérifier la présence de GRUB_BACKGROUND dans le résultat
        has_bg_in_result = "GRUB_BACKGROUND" in result
        logger.debug("[GENERATOR] GRUB_BACKGROUND dans le résultat final: %s", has_bg_in_result)
        if has_bg_in_result:
            # Trouver et afficher la ligne
            for line in result.split("\n"):
                if "GRUB_BACKGROUND" in line:
                    logger.debug("[GENERATOR] Ligne GRUB_BACKGROUND trouvée: '%s'", line)

        return result
