"""Gestion des sauvegardes pour GRUB Manager."""

import glob
import os
import shutil
from datetime import datetime

from src.utils.config import BACKUP_MAX_COUNT, GRUB_CONFIG_PATH
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GrubBackupError(Exception):
    """Exception levée lors d'erreurs de sauvegarde."""


class BackupManager:
    """Classe pour gérer les sauvegardes de configuration GRUB."""

    def __init__(self, config_path: str = GRUB_CONFIG_PATH):
        """Initialise le gestionnaire de sauvegardes.

        Args:
            config_path: Chemin du fichier de configuration GRUB.

        """
        self.config_path = config_path
        # Créer les sauvegardes dans le répertoire utilisateur pour éviter les problèmes de permissions
        self.backup_dir = os.path.expanduser("~/.local/share/grub_manager/backups")
        os.makedirs(self.backup_dir, exist_ok=True)
        self.backup_pattern = os.path.join(self.backup_dir, "grub.bak.*")

    def _legacy_backup_patterns(self) -> list[str]:
        """Retourne les patterns des anciens emplacements de sauvegarde.

        Returns:
            list[str]: Patterns à utiliser pour retrouver d'anciens backups.

        """
        legacy_dir = os.path.dirname(self.config_path)
        return [
            os.path.join(legacy_dir, "grub.bak.*"),
            os.path.join(legacy_dir, "grub.bak"),
            os.path.join(legacy_dir, "grub.prime-backup"),
        ]

    def create_backup(self) -> str:
        """Crée une sauvegarde horodatée du fichier de configuration.

        Returns:
            str: Chemin de la sauvegarde créée.

        Raises:
            GrubBackupError: Si la sauvegarde échoue.

        """
        if not os.path.exists(self.config_path):
            raise GrubBackupError(f"Fichier de configuration introuvable: {self.config_path}")

        # Générer le nom de sauvegarde avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"grub.bak.{timestamp}")

        try:
            # Copier le fichier
            shutil.copy2(self.config_path, backup_path)
            logger.info("Sauvegarde créée: %s", backup_path)

            # Nettoyer les anciennes sauvegardes
            self._cleanup_old_backups()

            # Vérifier l'intégrité
            self._verify_backup(backup_path)

            return backup_path

        except OSError as e:
            logger.error("Échec création sauvegarde: %s", e)
            raise GrubBackupError(f"Impossible de créer la sauvegarde: {e}") from e

    def restore_backup(self, backup_path: str | None = None) -> str:
        """Restaure une sauvegarde.

        Args:
            backup_path: Chemin de la sauvegarde. Si None, utilise la plus récente.

        Returns:
            str: Chemin de la sauvegarde à restaurer.

        Raises:
            GrubBackupError: Si la restauration échoue.

        """
        if backup_path is None:
            backup_path = self.get_latest_backup()

        if not backup_path or not os.path.exists(backup_path):
            raise GrubBackupError("Aucune sauvegarde valide trouvée")

        # Vérifier l'intégrité avant restauration
        self._verify_backup(backup_path)
        return backup_path

    def get_latest_backup(self) -> str | None:
        """Obtient le chemin de la sauvegarde la plus récente.

        Returns:
            Optional[str]: Chemin de la sauvegarde la plus récente, ou None.

        """
        backups = self.list_backups()
        return backups[0] if backups else None

    def list_backups(self) -> list[str]:
        """List all available backups, sorted by date (most recent first).

        Returns:
            List[str]: Liste des chemins de sauvegarde.

        """
        try:
            backups: list[str] = []
            backups.extend(glob.glob(self.backup_pattern))
            for pattern in self._legacy_backup_patterns():
                backups.extend(glob.glob(pattern))
            # Trier par nom (contient le timestamp) pour éviter les problèmes avec copy2
            backups.sort(reverse=True)
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
        """Vérifie l'intégrité d'une sauvegarde.

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
            if os.path.getsize(backup_path) == 0:
                raise GrubBackupError(f"Sauvegarde vide: {backup_path}")

            # Vérifier que c'est un fichier texte basique
            with open(backup_path, encoding="utf-8") as f:
                content = f.read(1024)  # Lire les premiers 1024 caractères
                if not content.strip():
                    raise GrubBackupError(f"Sauvegarde vide ou corrompue: {backup_path}")

        except (OSError, UnicodeDecodeError) as e:
            raise GrubBackupError(f"Sauvegarde corrompue: {e}") from e
