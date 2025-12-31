"""Exécution sécurisée des commandes système pour GRUB."""

import os
import subprocess
import tempfile

from src.core.security import InputSecurityValidator, SecurityError
from src.utils.config import COMMAND_TIMEOUT
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SecureCommandExecutor:
    """Classe pour exécuter des commandes système de manière sécurisée."""

    def __init__(self):
        """Initialise l'exécuteur de commandes."""
        self.timeout = COMMAND_TIMEOUT  # Timeout par défaut en secondes

    def execute_with_pkexec(self, commands: list[str]) -> tuple[bool, str]:
        """Exécute une liste de commandes via pkexec de manière sécurisée.

        Args:
            commands: Liste des commandes à exécuter.

        Returns:
            Tuple[bool, str]: (succès, message d'erreur si échec)

        """
        if not commands:
            return True, ""

        # Valider les commandes avant exécution
        try:
            for cmd in commands:
                InputSecurityValidator.validate_line(cmd)
        except SecurityError as e:
            logger.error("Security validation failed: %s", e)
            return False, str(e)

        # Créer un script temporaire sécurisé
        script_content = "#!/bin/bash\nset -e\n" + "\n".join(commands) + "\n"

        try:
            # Créer un fichier temporaire avec des permissions sécurisées
            with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as script_file:
                script_file.write(script_content)
                script_path = script_file.name

            # Rendre le script exécutable uniquement par le propriétaire
            os.chmod(script_path, 0o700)

            # Exécuter via pkexec (ou directement si déjà root)
            if os.geteuid() == 0:
                cmd = [script_path]
                logger.info("Exécution de commandes en root: %d commandes", len(commands))
            else:
                cmd = ["pkexec", script_path]
                logger.info("Exécution de commandes via pkexec: %d commandes", len(commands))

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout, check=False)

            success = not result.returncode
            output = result.stderr if not success else ""

            if success:
                logger.info("Commandes exécutées avec succès")
            else:
                logger.error("Échec exécution commandes (code %d): %s", result.returncode, output)

            return success, output

        except subprocess.TimeoutExpired:
            logger.error("Timeout lors de l'exécution des commandes")
            return False, "Timeout lors de l'exécution"
        except (OSError, subprocess.SubprocessError) as e:
            logger.exception("Erreur lors de l'exécution des commandes")
            return False, f"Erreur système: {e}"
        finally:
            # Nettoyer le script temporaire
            if "script_path" in locals() and os.path.exists(script_path):
                try:
                    os.unlink(script_path)
                except OSError:
                    pass  # Ignorer les erreurs de nettoyage

    def update_grub(self) -> tuple[bool, str]:
        """Update GRUB configuration.

        Returns:
            Tuple of (success, output/error)

        """
        commands = [
            "if command -v update-grub >/dev/null 2>&1; then",
            "    update-grub",
            "elif command -v grub-mkconfig >/dev/null 2>&1; then",
            "    grub-mkconfig -o /boot/grub/grub.cfg",
            "elif command -v grub2-mkconfig >/dev/null 2>&1; then",
            "    grub2-mkconfig -o /boot/grub2/grub.cfg",
            "else",
            '    echo "No GRUB update command found" >&2',
            "    exit 1",
            "fi",
        ]
        return self.execute_with_pkexec(commands)

    def copy_file_privileged(self, source: str, destination: str) -> tuple[bool, str]:
        """Copy file with elevated privileges using pkexec.

        Args:
            source: Source file path
            destination: Destination file path

        Returns:
            Tuple[bool, str]: (success, error_message)

        """
        commands = [f"cp '{source}' '{destination}'"]
        return self.execute_with_pkexec(commands)


