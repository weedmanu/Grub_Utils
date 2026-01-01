"""Helper pour gérer le processus de sauvegarde et application de la configuration GRUB."""

# pylint: disable=too-few-public-methods
# SaveManager est un gestionnaire spécialisé avec interface minimaliste

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.core.exceptions import GrubBackupError, GrubConfigError, GrubFileError, GrubValidationError
from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.core.backup_manager import BackupManager
    from src.core.command_executor import SecureCommandExecutor  # noqa: F401
    from src.core.config.generator import GrubConfigGenerator  # noqa: F401
    from src.core.validator import GrubValidator

logger = get_logger(__name__)


@dataclass
class SaveResult:
    """Résultat d'une opération de sauvegarde."""

    success: bool
    error_message: str = ""

    @property
    def as_tuple(self) -> tuple[bool, str]:
        """Retourne le résultat sous forme de tuple."""
        return self.success, self.error_message


@dataclass
class SaveCallbacks:
    """Callbacks pour les étapes de sauvegarde."""

    prepare_resources: Callable[[], tuple[bool, str]]
    write_config: Callable[[str], tuple[bool, str]]
    update_grub: Callable[[], tuple[bool, str]]
    apply_hidden: Callable[[], tuple[bool, str]]


class SaveManager:
    """Gestionnaire du processus complet de sauvegarde et application."""

    def __init__(
        self,
        backup_manager: "BackupManager",
        generator: "GrubConfigGenerator",
        validator: "GrubValidator",
        executor: "SecureCommandExecutor",
    ):
        """Initialise le gestionnaire.

        Args:
            backup_manager: Gestionnaire de sauvegardes
            generator: Générateur de configuration
            validator: Validateur de configuration
            executor: Exécuteur de commandes

        """
        self.backup_manager = backup_manager
        self.generator = generator
        self.validator = validator
        self.executor = executor
        self._backup_path: str | None = None

    def execute_save(
        self,
        entries: dict[str, str],
        original_lines: list[str],
        hidden_entries: list[str],
        callbacks: SaveCallbacks,
    ) -> SaveResult:
        """Exécute le processus complet de sauvegarde.

        Args:
            entries: Entrées de configuration
            original_lines: Lignes originales du fichier
            hidden_entries: Entrées masquées
            callbacks: Callbacks pour les différentes étapes

        Returns:
            SaveResult avec succès et message d'erreur

        """
        # Étape 1: Préparer les ressources
        result = self._step_prepare_resources(callbacks.prepare_resources)
        if not result.success:
            return result

        # Étape 2: Valider
        result = self._step_validate(entries)
        if not result.success:
            return result

        # Étape 3: Créer la sauvegarde
        result = self._step_create_backup()
        if not result.success:
            return result

        # Étapes 4-6 avec gestion centralisée
        return self._execute_remaining_steps(entries, original_lines, hidden_entries, callbacks)

    def _execute_remaining_steps(
        self,
        entries: dict[str, str],
        original_lines: list[str],
        hidden_entries: list[str],
        callbacks: SaveCallbacks,
    ) -> SaveResult:
        """Exécute les étapes 4-6 avec rollback automatique.

        Args:
            entries: Entrées de configuration
            original_lines: Lignes originales
            hidden_entries: Entrées masquées
            callbacks: Callbacks

        Returns:
            SaveResult

        """
        # Étape 4: Écrire
        result = self._step_write_config(entries, original_lines, hidden_entries, callbacks.write_config)
        if not result.success:
            self._rollback()
            return result

        # Étape 5: Mettre à jour
        result = self._step_update_grub(callbacks.update_grub)
        if not result.success:
            self._rollback()
            return result

        # Étape 6: Appliquer masquage
        result = self._step_apply_hidden(callbacks.apply_hidden)
        if not result.success:
            self._rollback()
            return result

        return SaveResult(success=True)

    def _step_prepare_resources(self, prepare_callback) -> SaveResult:
        """Prépare les ressources (images de fond, etc.)."""
        success, error = prepare_callback()
        if not success:
            logger.error("Failed to prepare resources: %s", error)
            return SaveResult(success=False, error_message=error)
        return SaveResult(success=True)

    def _step_validate(self, entries: dict[str, str]) -> SaveResult:
        """Validate the configuration."""
        try:
            logger.debug(
                "[SAVE_MANAGER] Avant validation - GRUB_BACKGROUND: %s, valeur: '%s'",
                "GRUB_BACKGROUND" in entries,
                entries.get("GRUB_BACKGROUND", "N/A"),
            )
            self.validator.validate_all(entries)
            logger.debug(
                "[SAVE_MANAGER] Après validation - GRUB_BACKGROUND: %s, valeur: '%s'",
                "GRUB_BACKGROUND" in entries,
                entries.get("GRUB_BACKGROUND", "N/A"),
            )
            return SaveResult(success=True)
        except (GrubValidationError, GrubConfigError) as e:
            logger.error("Validation error: %s", e)
            return SaveResult(success=False, error_message=str(e))

    def _step_create_backup(self) -> SaveResult:
        """Crée une sauvegarde."""
        try:
            self._backup_path = self.backup_manager.create_backup()
            logger.info("Backup created: %s", self._backup_path)
            return SaveResult(success=True)
        except (GrubBackupError, OSError, ValueError) as e:
            logger.error("Backup creation failed: %s", e)
            return SaveResult(success=False, error_message=f"Backup failed: {e}")

    def _step_write_config(
        self,
        entries: dict[str, str],
        original_lines: list[str],
        hidden_entries: list[str],
        write_callback,
    ) -> SaveResult:
        """Génère et écrit la nouvelle configuration."""
        try:
            logger.debug(
                "[SAVE_MANAGER] Génération config - GRUB_BACKGROUND: %s, valeur: '%s'",
                "GRUB_BACKGROUND" in entries,
                entries.get("GRUB_BACKGROUND", "N/A"),
            )
            new_content = self.generator.generate(entries, original_lines, hidden_entries)
            logger.debug("[SAVE_MANAGER] Contenu généré (%d caractères)", len(new_content))
            logger.debug("[SAVE_MANAGER] GRUB_BACKGROUND dans contenu: %s", "GRUB_BACKGROUND" in new_content)
            success, error = write_callback(new_content)
            if not success:
                return SaveResult(success=False, error_message=error)
            logger.debug("[SAVE_MANAGER] Configuration écrite avec succès")
            return SaveResult(success=True)
        except (GrubConfigError, GrubFileError, OSError) as e:
            logger.error("Failed to write config: %s", e)
            return SaveResult(success=False, error_message=f"Write failed: {e}")

    def _step_update_grub(self, update_callback) -> SaveResult:
        """Met à jour GRUB."""
        success, error = update_callback()
        if not success:
            logger.error("GRUB update failed: %s", error)
            return SaveResult(success=False, error_message=error)
        return SaveResult(success=True)

    def _step_apply_hidden(self, hidden_callback) -> SaveResult:
        """Applique les entrées masquées."""
        success, error = hidden_callback()
        if not success:
            logger.error("Failed to apply hidden entries: %s", error)
            return SaveResult(success=False, error_message=error)
        return SaveResult(success=True)

    def _rollback(self) -> None:
        """Effectue un rollback vers la sauvegarde."""
        if self._backup_path:
            try:
                self.backup_manager.restore_backup(self._backup_path)
                logger.info("Rollback successful")
            except (GrubBackupError, OSError, ValueError) as e:
                logger.warning("Rollback failed: %s", e)
