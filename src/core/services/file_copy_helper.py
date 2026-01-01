"""Helper pour la copie de fichiers d'image de fond."""

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from src.core.exceptions import GrubFileError
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class FileCopyResult:
    """Résultat d'une opération de copie de fichier."""

    success: bool
    destination_path: str = ""
    error_message: str = ""


# pylint: disable=too-few-public-methods
class FileCopyHelper:
    """Helper pour copier les fichiers d'image de fond vers le répertoire de thème."""

    @staticmethod
    def copy_background_image(
        source_path: str, theme_dir: str, supported_extensions: tuple[str, ...]
    ) -> FileCopyResult:
        """Copier l'image de fond vers le répertoire de thème.

        Args:
            source_path: Chemin source de l'image
            theme_dir: Répertoire de destination du thème
            supported_extensions: Extensions supportées

        Returns:
            FileCopyResult avec le résultat de l'opération

        """
        if not source_path:
            return FileCopyResult(success=True, destination_path="")

        try:
            # Validation du fichier source
            validation_result = FileCopyHelper._validate_source_file(source_path, supported_extensions)
            if not validation_result.success:
                return validation_result

            # Préparation des chemins
            dest_filename = Path(source_path).name
            dest_path = os.path.join(theme_dir, dest_filename)

            # Copie du fichier
            return FileCopyHelper._perform_copy(source_path, dest_path, dest_filename)

        except (OSError, GrubFileError) as e:
            logger.exception("Failed to copy background image")
            return FileCopyResult(success=False, error_message=f"Erreur lors de la copie: {e}")

    @staticmethod
    def _validate_source_file(source_path: str, supported_extensions: tuple[str, ...]) -> FileCopyResult:
        """Validate the source file.

        Args:
            source_path: Chemin du fichier à valider
            supported_extensions: Extensions autorisées

        Returns:
            FileCopyResult avec le résultat de validation

        """
        if not os.path.exists(source_path):
            return FileCopyResult(success=False, error_message=f"File not found: {source_path}")

        if not os.path.isfile(source_path):
            return FileCopyResult(success=False, error_message=f"Not a file: {source_path}")

        ext = Path(source_path).suffix.lower()
        if ext not in supported_extensions:
            return FileCopyResult(
                success=False,
                error_message=f"Unsupported format: {ext}. Supported: {', '.join(supported_extensions)}",
            )

        return FileCopyResult(success=True)

    @staticmethod
    def _perform_copy(source_path: str, dest_path: str, dest_filename: str) -> FileCopyResult:
        """Effectue la copie du fichier.

        Args:
            source_path: Chemin source
            dest_path: Chemin destination
            dest_filename: Nom du fichier de destination

        Returns:
            FileCopyResult avec le résultat de la copie

        """
        try:
            shutil.copy2(source_path, dest_path)
            logger.info("Background image copied: %s -> %s", source_path, dest_path)
            return FileCopyResult(success=True, destination_path=dest_filename)
        except (OSError, shutil.Error) as e:
            logger.exception("Copy operation failed")
            return FileCopyResult(success=False, error_message=f"Copy failed: {e}")
