"""Gestionnaire des entrées de menu GRUB masquées avec persistance après update-grub."""

# pylint: disable=duplicate-code

import json
import os

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Chemin du fichier de configuration des entrées masquées
HIDDEN_ENTRIES_CONFIG = "/etc/grub.d/hidden_entries.json"

# Chemin du script GRUB personnalisé
GRUB_CUSTOM_SCRIPT = "/etc/grub.d/41_custom_hide"


class HiddenEntriesManager:
    """Gestionnaire pour la persistance des entrées de menu masquées."""

    def __init__(self, config_path: str = HIDDEN_ENTRIES_CONFIG):
        """Initialise le gestionnaire.

        Args:
            config_path: Chemin du fichier de configuration

        """
        self.config_path = config_path

    def load_hidden_entries(self) -> list[str]:
        """Charge la liste des entrées masquées depuis le fichier de configuration.

        Returns:
            Liste des titres d'entrées à masquer

        """
        if not os.path.exists(self.config_path):
            logger.debug("Aucun fichier de configuration des entrées masquées trouvé")
            return []

        try:
            with open(self.config_path, encoding="utf-8") as f:
                data = json.load(f)
                hidden = data.get("hidden_entries", [])
                logger.info("Chargement de %d entrées masquées", len(hidden))
                return hidden
        except (OSError, json.JSONDecodeError) as e:
            logger.error("Erreur lors du chargement des entrées masquées: %s", e)
            return []

    def save_hidden_entries(self, hidden_entries: list[str], executor) -> tuple[bool, str]:
        """Sauvegarde la liste des entrées masquées.

        Cette méthode crée :
        1. Un fichier JSON avec la liste des entrées masquées
        2. Un script GRUB exécutable dans /etc/grub.d/ qui masque les entrées

        Args:
            hidden_entries: Liste des titres d'entrées à masquer
            executor: SecureCommandExecutor pour les opérations privilégiées

        Returns:
            Tuple (succès, message_erreur)

        """
        try:
            # 1. Créer le fichier de configuration JSON
            config_data = {
                "hidden_entries": hidden_entries,
                "version": "1.0",
            }
            config_json = json.dumps(config_data, indent=2, ensure_ascii=False)

            # Sauvegarder le fichier JSON avec privilèges
            success, error = executor.write_file_privileged(self.config_path, config_json)
            if not success:
                return False, f"Échec de sauvegarde du fichier de configuration: {error}"

            # 2. Créer le script GRUB personnalisé
            success, error = self._create_grub_script(executor)
            if not success:
                return False, f"Échec de création du script GRUB: {error}"

            logger.info("Sauvegarde de %d entrées masquées réussie", len(hidden_entries))
            return True, ""

        except OSError as e:
            logger.exception("Erreur lors de la sauvegarde des entrées masquées")
            return False, str(e)

    def _create_grub_script(self, executor) -> tuple[bool, str]:
        """Crée un hook APT pour ré-appliquer les entrées masquées après update-grub.

        GRUB ne fournit pas de mécanisme natif pour masquer des entrées via /etc/grub.d/.
        La solution est de créer un hook APT qui modifie grub.cfg APRÈS sa génération.

        Args:
            executor: SecureCommandExecutor

        Returns:
            Tuple (succès, message_erreur)

        """
        # Créer un script Python qui sera exécuté après update-grub
        hook_script = f'''#!/usr/bin/env python3
"""Hook APT pour ré-appliquer les entrées masquées après update-grub."""

import json
import os

CONFIG_PATH = "{self.config_path}"
GRUB_CFG_PATHS = ["/boot/grub/grub.cfg", "/boot/grub2/grub.cfg"]

def load_hidden_entries():
    """Charge les entrées masquées depuis la configuration."""
    if not os.path.exists(CONFIG_PATH):
        return []
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("hidden_entries", [])
    except (OSError, json.JSONDecodeError):
        return []

def apply_hidden_entries():
    """Masque les entrées dans grub.cfg."""
    hidden = load_hidden_entries()
    if not hidden:
        return

    # Trouver grub.cfg
    grub_cfg = None
    for path in GRUB_CFG_PATHS:
        if os.path.exists(path):
            grub_cfg = path
            break

    if not grub_cfg:
        return

    try:
        with open(grub_cfg, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = []
        skipping = False
        skip_level = 0
        current_level = 0

        for line in lines:
            stripped = line.strip()
            is_entry = stripped.startswith("menuentry ") or stripped.startswith("submenu ")

            if not skipping and is_entry:
                parts = stripped.split("'")
                if len(parts) >= 2:
                    title = parts[1]
                    if title in hidden:
                        skipping = True
                        skip_level = current_level

            open_b = line.count("{{")
            close_b = line.count("}}")

            if skipping:
                current_level += open_b
                current_level -= close_b
                if current_level <= skip_level:
                    skipping = False
                continue

            new_lines.append(line)
            current_level += open_b
            current_level -= close_b

        with open(grub_cfg, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    except OSError:
        pass

if __name__ == "__main__":
    apply_hidden_entries()
'''

        # Sauvegarder le hook avec privilèges
        hook_path = "/etc/kernel/postinst.d/zz-grub-hide-entries"
        success, error = executor.write_file_privileged(hook_path, hook_script)
        if not success:
            return False, error

        # Rendre le hook exécutable
        success, error = executor.run_command(["chmod", "+x", hook_path])
        if not success:
            return False, f"Échec de rendre le hook exécutable: {error}"

        return True, ""

    def clear_hidden_entries(self, executor) -> tuple[bool, str]:
        """Supprime toutes les entrées masquées.

        Args:
            executor: SecureCommandExecutor

        Returns:
            Tuple (succès, message_erreur)

        """
        return self.save_hidden_entries([], executor)

    def remove_config_files(self, executor) -> tuple[bool, str]:
        """Supprime les fichiers de configuration et scripts associés.

        Args:
            executor: SecureCommandExecutor

        Returns:
            Tuple (succès, message_erreur)

        """
        try:
            hook_path = "/etc/kernel/postinst.d/zz-grub-hide-entries"

            # Supprimer le fichier de configuration
            if os.path.exists(self.config_path):
                success, error = executor.run_command(["rm", "-f", self.config_path])
                if not success:
                    return False, f"Échec de suppression de {self.config_path}: {error}"

            # Supprimer le hook APT
            success, error = executor.run_command(["rm", "-f", hook_path])
            if not success:
                return False, f"Échec de suppression de {hook_path}: {error}"

            # Supprimer l'ancien script GRUB si présent
            if os.path.exists(GRUB_CUSTOM_SCRIPT):
                executor.run_command(["rm", "-f", GRUB_CUSTOM_SCRIPT])

            logger.info("Fichiers de configuration des entrées masquées supprimés")
            return True, ""

        except OSError as e:
            logger.exception("Erreur lors de la suppression des fichiers de configuration")
            return False, str(e)
