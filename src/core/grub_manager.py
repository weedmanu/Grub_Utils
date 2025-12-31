"""Module pour gérer la configuration de GRUB."""

import os
import re
import subprocess
import tempfile
from typing import Dict, List, Optional, Tuple

from src.core.backup_manager import BackupManager
from src.core.command_executor import SecureCommandExecutor
from src.core.exceptions import GrubConfigError
from src.core.validator import GrubValidator
from src.utils.config import GRUB_CFG_PATHS
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GrubManager:
    """Classe pour charger, modifier et appliquer la configuration GRUB."""

    def __init__(self, config_path: str = "/etc/default/grub"):
        """
        Initialise le gestionnaire avec les chemins par défaut.

        Args:
            config_path: Chemin du fichier de configuration GRUB.
        """
        self.config_path = config_path
        self.grub_cfg_path = self._find_grub_cfg_path()

        self.entries: Dict[str, str] = {}
        self.menu_entries: List[Dict] = []
        self.hidden_entries: List[str] = []
        self.lines: List[str] = []

        # Initialiser les gestionnaires
        self.backup_manager = BackupManager(config_path)
        self.executor = SecureCommandExecutor()
        self.validator = GrubValidator()

    def _find_grub_cfg_path(self) -> str:
        """Trouve le chemin correct de grub.cfg."""
        for path in GRUB_CFG_PATHS:
            if os.path.exists(path):
                return path
        return GRUB_CFG_PATHS[0]  # Fallback

    def load(self) -> None:
        """Charge la configuration depuis /etc/default/grub et le menu GRUB."""
        logger.info("Chargement de la configuration GRUB")
        try:
            self._load_config_file()
            self._load_menu_entries()
            self._determine_hidden_entries()
            logger.info("Configuration GRUB chargée avec succès")
        except Exception as e:
            logger.exception("Erreur lors du chargement de la configuration GRUB")
            raise GrubConfigError(f"Impossible de charger la configuration: {e}") from e

    def _load_config_file(self) -> None:
        """Charge le fichier de configuration /etc/default/grub."""
        self.lines = []
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.lines = f.readlines()
                for line in self.lines:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        self.entries[key.strip()] = value.strip().strip('"').strip("'")
        except OSError as e:
            logger.error("Erreur lecture fichier config: %s", e)
            raise GrubConfigError(f"Impossible de lire {self.config_path}: {e}") from e

    def _load_menu_entries(self) -> None:
        """Charge les entrées du menu GRUB."""
        self.menu_entries = self._parse_menu_entries()

    def _determine_hidden_entries(self) -> None:
        """Détermine les entrées masquées basées sur la configuration."""
        flat_entries = self.get_flat_menu_entries()
        self.hidden_entries = []

        # Vérifier les permissions des scripts
        def is_disabled(path: str) -> bool:
            return os.path.exists(path) and not os.access(path, os.X_OK)

        if is_disabled("/etc/grub.d/30_os-prober"):
            self.hidden_entries.extend([e for e in flat_entries if "Windows" in e])

        memtest_path = (
            "/etc/grub.d/20_memtest86+" if os.path.exists("/etc/grub.d/20_memtest86+") else "/etc/grub.d/20_memtest"
        )
        if is_disabled(memtest_path):
            self.hidden_entries.extend(
                [e for e in flat_entries if "memtest" in e.lower() or "memory test" in e.lower()]
            )

        if self.entries.get("GRUB_DISABLE_SUBMENU") == "y":
            self.hidden_entries.extend([e for e in flat_entries if "with Linux" in e])

        if self.entries.get("GRUB_DISABLE_RECOVERY") == "true":
            self.hidden_entries.extend([e for e in flat_entries if "recovery mode" in e.lower()])

    def _parse_menu_entries(self) -> List[Dict]:
        """Parse le fichier grub.cfg pour extraire les entrées et sous-menus."""
        entries: List[Dict] = []
        try:
            cmd = ["pkexec", "cat", self.grub_cfg_path]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            content = result.stdout if not result.returncode else ""
            if not content and os.path.exists(self.grub_cfg_path):
                with open(self.grub_cfg_path, "r", encoding="utf-8") as f:
                    content = f.read()

            stack = [entries]
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("submenu "):
                    match = re.search(r"['\"](.*?)['\"]", line)
                    if match:
                        new_submenu: Dict = {
                            "type": "submenu",
                            "name": match.group(1),
                            "entries": [],
                        }
                        stack[-1].append(new_submenu)
                        stack.append(new_submenu["entries"])
                elif line.startswith("menuentry "):
                    match = re.search(r"['\"](.*?)['\"]", line)
                    if match:
                        stack[-1].append({"type": "entry", "name": match.group(1)})
                elif line == "}" and len(stack) > 1:
                    stack.pop()
        except (OSError, subprocess.SubprocessError) as e:
            logger.warning("Erreur parsing menu: %s", e)
        return entries

    def get_flat_menu_entries(self) -> List[str]:
        """Retourne une liste plate de tous les noms d'entrées (pour la compatibilité)."""
        flat = []

        def _extract(items: List[Dict]) -> None:
            for item in items:
                if item["type"] == "entry":
                    flat.append(item["name"])
                else:
                    _extract(item["entries"])

        _extract(self.menu_entries)
        return flat

    def _get_chmod_commands(self) -> List[str]:
        """Génère les commandes chmod pour activer/désactiver les scripts GRUB."""
        scripts = {
            "os-prober": "/etc/grub.d/30_os-prober",
            "memtest": "/etc/grub.d/20_memtest86+",
        }
        if not os.path.exists(scripts["memtest"]):
            scripts["memtest"] = "/etc/grub.d/20_memtest"

        hide_windows = any("Windows" in e for e in self.hidden_entries)
        hide_memtest = any("memtest" in e.lower() or "memory test" in e.lower() for e in self.hidden_entries)

        chmod_cmds = []
        for key, path in scripts.items():
            if os.path.exists(path):
                should_hide = hide_windows if key == "os-prober" else hide_memtest
                action = "-x" if should_hide else "+x"
                chmod_cmds.append(f"chmod {action} {path}")
        return chmod_cmds

    def _prepare_new_config(self) -> List[str]:
        """Prépare le nouveau contenu de /etc/default/grub."""
        hide_recovery = any("recovery mode" in e.lower() for e in self.hidden_entries)
        hide_advanced = any("with Linux" in e for e in self.hidden_entries)

        self.entries["GRUB_DISABLE_RECOVERY"] = "true" if hide_recovery else "false"
        self.entries["GRUB_DISABLE_SUBMENU"] = "y" if hide_advanced else "n"
        self.entries.pop("GRUB_HIDDEN_ENTRIES", None)

        new_lines = []
        processed_keys = set()
        for line in self.lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                key = stripped.split("=", 1)[0].strip()
                if key in self.entries:
                    val = self.entries[key]
                    new_lines.append(f'{key}="{val}"\n' if " " in val or "," in val else f"{key}={val}\n")
                    processed_keys.add(key)
                    continue
            new_lines.append(line)

        for key, val in self.entries.items():
            if key not in processed_keys:
                new_lines.append(f'{key}="{val}"\n' if " " in val or "," in val else f"{key}={val}\n")
        return new_lines

    def restore_backup(self, backup_path: Optional[str] = None) -> bool:
        """
        Restaure la configuration depuis une sauvegarde.

        Args:
            backup_path: Chemin de la sauvegarde. Si None, utilise la plus récente.

        Returns:
            bool: True si la restauration a réussi.
        """
        try:
            # Restaurer la sauvegarde
            restored_path = self.backup_manager.restore_backup(backup_path)
            logger.info("Sauvegarde restaurée: %s", restored_path)

            # Mettre à jour GRUB
            update_cmd = self._get_update_grub_command()
            success, error = self.executor.execute_with_pkexec([update_cmd])

            if success:
                self.load()  # Recharger la config après restauration
                logger.info("Configuration GRUB restaurée avec succès")
                return True
            logger.error("Échec mise à jour GRUB après restauration: %s", error)
            return False

        except Exception:
            logger.exception("Erreur lors de la restauration")
            return False

    def _get_update_grub_command(self) -> str:
        """Détermine la commande appropriée pour mettre à jour GRUB."""
        if not subprocess.run(["which", "update-grub"], capture_output=True, check=False).returncode:
            return "update-grub"

        if os.path.exists("/boot/grub2/grub.cfg"):
            return "grub2-mkconfig -o /boot/grub2/grub.cfg"

        return "grub-mkconfig -o /boot/grub/grub.cfg"

    def save_and_apply(self) -> Tuple[bool, str]:
        """
        Sauvegarde la configuration et met à jour GRUB.

        Returns:
            Tuple[bool, str]: (succès, message d'erreur si échec)
        """
        try:
            # Validation des entrées
            self.validator.validate_all(self.entries)
            logger.info("Validation de la configuration réussie")

            # Créer une sauvegarde
            backup_path = self.backup_manager.create_backup()
            logger.info("Sauvegarde créée: %s", backup_path)

            # Préparer les commandes
            commands = self._prepare_secure_commands()
            update_cmd = self._get_update_grub_command()
            commands.append(update_cmd)

            # Exécuter les commandes
            success, error = self.executor.execute_with_pkexec(commands)

            if success:
                logger.info("Configuration GRUB appliquée avec succès")
                return True, ""
            logger.error("Échec application GRUB: %s", error)
            return False, f"Échec de l'application: {error}"

        except Exception as e:
            logger.exception("Erreur lors de save_and_apply")
            return False, f"Erreur inattendue: {e}"

    def _prepare_secure_commands(self) -> List[str]:
        """Prépare les commandes sécurisées pour la sauvegarde et application."""
        chmod_cmds = self._get_chmod_commands()
        new_lines = self._prepare_new_config()

        # Créer un fichier temporaire sécurisé
        fd, tmp_path = tempfile.mkstemp()
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp:
                tmp.writelines(new_lines)

            commands = [
                f"cp {tmp_path} {self.config_path}",
                f"chmod 644 {self.config_path}",
            ] + chmod_cmds

            return commands

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
