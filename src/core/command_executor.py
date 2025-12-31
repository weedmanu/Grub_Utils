"""Exécution sécurisée des commandes système pour GRUB."""

import os
import subprocess
import tempfile
from typing import List, Tuple

from src.utils.config import COMMAND_TIMEOUT
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SecureCommandExecutor:
    """Classe pour exécuter des commandes système de manière sécurisée."""

    def __init__(self):
        """Initialise l'exécuteur de commandes."""
        self.timeout = COMMAND_TIMEOUT  # Timeout par défaut en secondes

    def execute_with_pkexec(self, commands: List[str]) -> Tuple[bool, str]:
        """
        Exécute une liste de commandes via pkexec de manière sécurisée.

        Args:
            commands: Liste des commandes à exécuter.

        Returns:
            Tuple[bool, str]: (succès, message d'erreur si échec)
        """
        if not commands:
            return True, ""

        # Créer un script temporaire sécurisé
        script_content = "#!/bin/bash\nset -e\n" + "\n".join(commands) + "\n"

        try:
            # Créer un fichier temporaire avec des permissions sécurisées
            with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as script_file:
                script_file.write(script_content)
                script_path = script_file.name

            # Rendre le script exécutable uniquement par le propriétaire
            os.chmod(script_path, 0o700)

            # Exécuter via pkexec
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
