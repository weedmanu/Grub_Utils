"""Processors pour les lignes de configuration GRUB."""

# pylint: disable=too-few-public-methods
# Les classes de ce module sont des utilitaires spécialisés avec une seule responsabilité

from dataclasses import dataclass

from src.utils.logger import get_logger


@dataclass
class ParsedKey:
    """Résultat du parsing d'une clé de configuration."""

    clean_key: str
    is_exported: bool
    is_commented: bool


class KeyNormalizer:
    """Normalise les clés de configuration GRUB."""

    @staticmethod
    def normalize(key_part: str) -> ParsedKey:
        """Normalise une clé en enlevant les préfixes.

        Args:
            key_part: Partie clé d'une ligne (avant le =)

        Returns:
            ParsedKey avec clé normalisée et flags

        """
        clean_key = key_part.strip()
        is_commented = False
        is_exported = False

        # Enlever le commentaire
        if clean_key.startswith("#"):
            clean_key = clean_key.lstrip("#").strip()
            is_commented = True

        # Enlever export
        if clean_key.startswith("export "):
            clean_key = clean_key[7:].strip()
            is_exported = True

        return ParsedKey(
            clean_key=clean_key,
            is_exported=is_exported,
            is_commented=is_commented,
        )


class ConfigLineBuilder:
    """Construit des lignes de configuration GRUB."""

    def __init__(self, keys_to_export: set[str]):
        """Initialise le builder.

        Args:
            keys_to_export: Ensemble des clés qui doivent être exportées

        """
        self.keys_to_export = keys_to_export

    def build_line(
        self,
        key: str,
        value: str,
        was_exported: bool,
        is_hidden: bool,
    ) -> str:
        """Construit une ligne de configuration.

        Args:
            key: Nom de la clé
            value: Valeur de la clé
            was_exported: Si la clé était exportée dans l'original
            is_hidden: Si la clé doit être cachée (commentée)

        Returns:
            Ligne de configuration formatée

        """
        should_export = was_exported or key in self.keys_to_export
        prefix = "export " if should_export else ""

        line = f'{prefix}{key}="{value}"'

        if is_hidden:
            line = f"#{line}"

        return line


class LineClassifier:
    """Classifie les types de lignes de configuration."""

    @staticmethod
    def is_empty(line: str) -> bool:
        """Vérifie si la ligne est vide."""
        return not line.strip()

    @staticmethod
    def is_pure_comment(line: str) -> bool:
        """Vérifie si c'est un commentaire pur (sans =)."""
        stripped = line.strip()
        return stripped.startswith("#") and "=" not in stripped

    @staticmethod
    def has_key_value(line: str) -> bool:
        """Vérifie si la ligne contient une paire clé=valeur."""
        return "=" in line.strip()

    @staticmethod
    def extract_key_part(line: str) -> str:
        """Extrait la partie clé d'une ligne."""
        stripped = line.strip()
        if "=" in stripped:
            return stripped.split("=")[0].strip()
        return ""


class GrubLineProcessor:
    """Traite les lignes de configuration GRUB."""

    def __init__(self, keys_to_export: set[str], hidden_keys: set[str]):
        """Initialise le processeur.

        Args:
            keys_to_export: Clés qui doivent être exportées
            hidden_keys: Clés qui doivent être cachées

        """
        self.normalizer = KeyNormalizer()
        self.builder = ConfigLineBuilder(keys_to_export)
        self.classifier = LineClassifier()
        self.hidden_keys = hidden_keys

    def process_line(
        self,
        line: str,
        entries: dict[str, str],
    ) -> str | None:
        """Traite une ligne de configuration.

        Args:
            line: Ligne à traiter
            entries: Dictionnaire des entrées de configuration

        Returns:
            Nouvelle ligne ou None si la ligne doit être remplacée

        """
        # Préserver les lignes vides
        if self.classifier.is_empty(line):
            return line.rstrip()

        # Préserver les commentaires purs
        if self.classifier.is_pure_comment(line):
            return line.rstrip()

        # Traiter les lignes clé=valeur
        if self.classifier.has_key_value(line):
            key_part = self.classifier.extract_key_part(line)
            parsed = self.normalizer.normalize(key_part)

            if parsed.clean_key in entries:
                value = entries[parsed.clean_key]

                # Log pour GRUB_BACKGROUND
                if parsed.clean_key == "GRUB_BACKGROUND":
                    logger = get_logger(__name__)
                    logger.debug(
                        "[LINE_PROCESSOR] Traitement GRUB_BACKGROUND: ligne='%s', nouvelle_valeur='%s'",
                        line.strip(),
                        value,
                    )

                # Si la valeur est vide, supprimer la ligne (retourner None)
                if not value:
                    if parsed.clean_key == "GRUB_BACKGROUND":
                        logger = get_logger(__name__)
                        logger.debug("[LINE_PROCESSOR] Suppression de la ligne GRUB_BACKGROUND (valeur vide)")
                    return None

                # Remplacer par la nouvelle valeur
                is_hidden = parsed.clean_key in self.hidden_keys
                return self.builder.build_line(
                    parsed.clean_key,
                    value,
                    parsed.is_exported,
                    is_hidden,
                )

        # Garder la ligne originale
        return line.rstrip()


class NewEntriesAppender:
    """Ajoute les nouvelles entrées non présentes dans le fichier original."""

    def __init__(self, keys_to_export: set[str], hidden_keys: set[str]):
        """Initialise l'appender.

        Args:
            keys_to_export: Clés qui doivent être exportées
            hidden_keys: Clés qui doivent être cachées

        """
        self.builder = ConfigLineBuilder(keys_to_export)
        self.normalizer = KeyNormalizer()
        self.hidden_keys = hidden_keys

    def find_new_entries(
        self,
        entries: dict[str, str],
        original_lines: list[str],
    ) -> list[str]:
        """Trouve les entrées qui n'étaient pas dans le fichier original.

        Args:
            entries: Toutes les entrées de configuration
            original_lines: Lignes originales du fichier

        Returns:
            Liste des nouvelles lignes à ajouter

        """
        existing_keys = self._extract_existing_keys(original_lines)
        new_lines = []

        for key, value in entries.items():
            if key not in existing_keys:
                is_hidden = key in self.hidden_keys
                line = self.builder.build_line(key, value, False, is_hidden)
                new_lines.append(line)

        return new_lines

    def _extract_existing_keys(self, lines: list[str]) -> set[str]:
        """Extrait toutes les clés existantes dans les lignes.

        Args:
            lines: Lignes du fichier original

        Returns:
            Ensemble des clés trouvées

        """
        keys = set()
        classifier = LineClassifier()

        for line in lines:
            if classifier.has_key_value(line):
                key_part = classifier.extract_key_part(line)
                parsed = self.normalizer.normalize(key_part)
                keys.add(parsed.clean_key)

        return keys
