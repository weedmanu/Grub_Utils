"""Gestion des sauvegardes pour GRUB Manager."""

import glob
import os
import shutil
from datetime import datetime
from typing import List, Optional

from src.utils.config import BACKUP_MAX_COUNT, GRUB_CONFIG_PATH
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GrubBackupError(Exception):
    """Exception levée lors d'erreurs de sauvegarde."""


class BackupManager:
    """Classe pour gérer les sauvegardes de configuration GRUB."""

    def __init__(self, config_path: str = GRUB_CONFIG_PATH):
        """
        Initialise le gestionnaire de sauvegardes.

        Args:
            config_path: Chemin du fichier de configuration GRUB.
        """
        self.config_path = config_path
        self.backup_dir = os.path.dirname(config_path)
        self.backup_pattern = os.path.join(self.backup_dir, "grub.bak.*")

    def create_backup(self) -> str:
        """
        Crée une sauvegarde horodatée du fichier de configuration.

        Returns:
            str: Chemin de la sauvegarde créée.

        Raises:
            GrubBackupError: Si la sauvegarde échoue.
        """
        if not os.path.exists(self.config_path):
            raise GrubBackupError(f"Fichier de configuration introuvable: {self.config_path}")

        # Générer le nom de sauvegarde avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.config_path}.bak.{timestamp}"

        try:
            # Copier le fichier
            shutil.copy2(self.config_path, backup_path)
            logger.info("Sauvegarde créée: %s", backup_path)

            # Nettoyer les anciennes sauvegardes
            self._cleanup_old_backups()

            # Vérifier l'intégrité
            self._verify_backup(backup_path)

            return backup_path

        except (OSError, IOError) as e:
            logger.error("Échec création sauvegarde: %s", e)
            raise GrubBackupError(f"Impossible de créer la sauvegarde: {e}") from e

    def restore_backup(self, backup_path: Optional[str] = None) -> str:
        """
        Restaure une sauvegarde.

        Args:
            backup_path: Chemin de la sauvegarde. Si None, utilise la plus récente.

        Returns:
            str: Chemin de la sauvegarde restaurée.

        Raises:
            GrubBackupError: Si la restauration échoue.
        """
        if backup_path is None:
            backup_path = self.get_latest_backup()

        if not backup_path or not os.path.exists(backup_path):
            raise GrubBackupError("Aucune sauvegarde valide trouvée")

        try:
            # Vérifier l'intégrité avant restauration
            self._verify_backup(backup_path)

            # Restaurer
            shutil.copy2(backup_path, self.config_path)
            logger.info("Sauvegarde restaurée depuis: %s", backup_path)

            return backup_path

        except (OSError, IOError) as e:
            logger.error("Échec restauration sauvegarde: %s", e)
            raise GrubBackupError(f"Impossible de restaurer la sauvegarde: {e}") from e

    def get_latest_backup(self) -> Optional[str]:
        """
        Obtient le chemin de la sauvegarde la plus récente.

        Returns:
            Optional[str]: Chemin de la sauvegarde la plus récente, ou None.
        """
        backups = self.list_backups()
        return backups[0] if backups else None

    def list_backups(self) -> List[str]:
        """
        List all available backups, sorted by date (most recent first).

        Returns:
            List[str]: Liste des chemins de sauvegarde.
        """
        try:
            backups = glob.glob(self.backup_pattern)
            # Trier par date de modification (plus récente d'abord)
            backups.sort(key=os.path.getmtime, reverse=True)
            return backups
        except OSError:
            return []

    def _cleanup_old_backups(self) -> None:
        """Supprime les sauvegardes les plus anciennes pour respecter la limite."""
        backups = self.list_backups()
        if len(backups) > BACKUP_MAX_COUNT:
            to_remove = backups[BACKUP_MAX_COUNT:]
            for backup in to_remove:
                try:
                    os.remove(backup)
                    logger.info("Ancienne sauvegarde supprimée: %s", backup)
                except OSError as e:
                    logger.warning("Impossible de supprimer %s: %s", backup, e)

    def _verify_backup(self, backup_path: str) -> None:
        """
        Vérifie l'intégrité d'une sauvegarde.

        Args:
            backup_path: Chemin de la sauvegarde à vérifier.

        Raises:
            GrubBackupError: Si la sauvegarde est corrompue.
        """
        try:
            # Vérifier que le fichier existe et est lisible
            if not os.path.exists(backup_path):
                raise GrubBackupError(f"Sauvegarde introuvable: {backup_path}")

            if not os.access(backup_path, os.R_OK):
                raise GrubBackupError(f"Sauvegarde illisible: {backup_path}")

            # Vérifier la taille (doit être > 0)
            if os.path.getsize(backup_path):
                raise GrubBackupError(f"Sauvegarde vide: {backup_path}")

            # Vérifier que c'est un fichier texte basique
            with open(backup_path, "r", encoding="utf-8") as f:
                content = f.read(1024)  # Lire les premiers 1024 caractères
                if not content.strip():
                    raise GrubBackupError(f"Sauvegarde vide ou corrompue: {backup_path}")

        except (OSError, IOError, UnicodeDecodeError) as e:
            raise GrubBackupError(f"Sauvegarde corrompue: {e}") from e
