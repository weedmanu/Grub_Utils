"""GRUB service for orchestrating configuration operations."""

import os
import re
import struct
import tempfile
import zlib

from src.core.backup_manager import BackupManager
from src.core.command_executor import SecureCommandExecutor
from src.core.config.generator import GrubConfigGenerator
from src.core.config.hidden_entries_manager import HiddenEntriesManager
from src.core.config.loader import GrubConfigLoader
from src.core.config.parser import GrubMenuParser
from src.core.exceptions import (
    GrubConfigError,
    GrubServiceError,
    GrubValidationError,
)
from src.core.services.save_manager import SaveCallbacks, SaveManager
from src.core.validator import GrubValidator
from src.utils.config import GRUB_BACKGROUNDS_DIR, GRUB_CFG_PATHS, GRUB_CONFIG_PATH
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GrubService:  # pylint: disable=too-many-instance-attributes
    """Main service for GRUB configuration management."""

    def __init__(self, config_path: str = GRUB_CONFIG_PATH):
        """Initialize the GRUB service.

        Args:
            config_path: Path to GRUB configuration file

        """
        self.config_path = config_path

        # Initialize components
        self.loader = GrubConfigLoader(config_path)
        self.parser = GrubMenuParser()
        self.generator = GrubConfigGenerator()
        self.validator = GrubValidator()
        self.backup_manager = BackupManager(config_path)
        self.executor = SecureCommandExecutor()
        self.hidden_entries_manager = HiddenEntriesManager()

        # Initialize save manager
        self.save_manager = SaveManager(self.backup_manager, self.generator, self.validator, self.executor)

        # State
        self.entries: dict[str, str] = {}
        self.original_lines: list[str] = []
        self.menu_entries: list[dict] = []
        self.hidden_entries: list[str] = []
        self._loaded = False

    def load(self) -> None:
        """Load GRUB configuration.

        Raises:
            GrubConfigError: If configuration cannot be loaded

        """
        logger.debug("[GRUB_SERVICE] Chargement configuration GRUB")
        try:
            self.entries, self.original_lines = self.loader.load()
            logger.debug("[GRUB_SERVICE] %d entrées et %d lignes chargées", len(self.entries), len(self.original_lines))

            self.menu_entries = self.parser.parse_menu_entries()
            logger.info("[GRUB_SERVICE] grub.cfg utilisé: %s", self.parser.grub_cfg_path)
            logger.debug("[GRUB_SERVICE] %d entrées de menu parsées", len(self.menu_entries))

            # Charger les entrées masquées depuis le fichier de configuration
            self.hidden_entries = self.hidden_entries_manager.load_hidden_entries()
            logger.debug("[GRUB_SERVICE] %d entrées masquées chargées", len(self.hidden_entries))

            self._loaded = True

            logger.info(
                "GRUB configuration loaded",
                extra={
                    "config_entries": len(self.entries),
                    "menu_entries": len(self.menu_entries),
                },
            )
        except (OSError, ValueError) as e:
            logger.error("Failed to load configuration: %s", e)
            raise GrubServiceError(f"Load failed: {e}") from e

    def save_and_apply(self) -> tuple[bool, str]:
        """Save configuration and apply changes.

        Returns:
            Tuple of (success, error_message)

        """
        if not self._loaded:
            return False, "Configuration not loaded"

        logger.debug("Sauvegarde - GRUB_BACKGROUND présent: %s", "GRUB_BACKGROUND" in self.entries)

        try:
            callbacks = SaveCallbacks(
                prepare_resources=self._prepare_resources,
                write_config=self._write_config,
                update_grub=self._update_grub,
                apply_hidden=self._apply_hidden_entries,
            )

            result = self.save_manager.execute_save(
                entries=self.entries,
                original_lines=self.original_lines,
                hidden_entries=self.hidden_entries,
                callbacks=callbacks,
            )
            return result.as_tuple

        except (GrubValidationError, GrubConfigError) as e:
            logger.error("Validation error: %s", e)
            return False, str(e)
        except (OSError, ValueError) as e:
            logger.exception("Save failed: %s", e)
            return False, f"Save failed: {e}"

    def _prepare_resources(self) -> tuple[bool, str]:
        """Prepare background images and themes.

        Returns:
            Tuple of (success, error_message)

        """
        logger.debug("[GRUB_SERVICE] Préparation des ressources (images/thèmes)")

        # Manage color script based on whether colors are defined
        has_colors = bool(self.entries.get("GRUB_COLOR_NORMAL") or self.entries.get("GRUB_COLOR_HIGHLIGHT"))

        if has_colors:
            success, error = self._install_color_script()
            if not success:
                logger.warning("[GRUB_SERVICE] Échec installation script couleurs: %s", error)
                # Non-fatal, continue
        else:
            # Remove color script if it exists
            self._remove_color_script()

        # Copy background image to /boot/grub if needed
        success, error = self._copy_background_image()
        if not success:
            logger.error("[GRUB_SERVICE] Échec copie image de fond: %s", error)
            return False, error

        logger.debug("[GRUB_SERVICE] Ressources préparées avec succès")
        return True, ""

    def _install_color_script(self) -> tuple[bool, str]:
        """Install GRUB color script to /etc/grub.d/05_grub_colors.

        Returns:
            Tuple of (success, error_message)

        """
        # Get color values from current configuration
        color_normal = self.entries.get("GRUB_COLOR_NORMAL", "light-gray/black")
        color_highlight = self.entries.get("GRUB_COLOR_HIGHLIGHT", "white/dark-gray")

        script_content = f"""#!/bin/sh
# Script pour appliquer les couleurs personnalisées GRUB
# Généré automatiquement par Grub Utils

cat << 'EOF'
# Couleurs personnalisées
set color_normal={color_normal}
set color_highlight={color_highlight}
set menu_color_normal={color_normal}
set menu_color_highlight={color_highlight}
EOF
"""

        try:
            # Write script to temp file
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".sh") as tmp:
                tmp.write(script_content)
                tmp_path = tmp.name

            # Copy to /etc/grub.d/ with elevated privileges
            dest_path = "/etc/grub.d/05_grub_colors"
            success, output = self.executor.copy_file_privileged(tmp_path, dest_path)

            # Cleanup temp file
            os.unlink(tmp_path)

            if not success:
                return False, f"Failed to copy color script: {output}"

            # Make executable
            chmod_cmd = [f"chmod +x {dest_path}"]
            success, output = self.executor.execute_with_pkexec(chmod_cmd)

            if not success:
                return False, f"Failed to make color script executable: {output}"

            logger.info("Color script installed to %s", dest_path)
            return True, ""

        except OSError as e:
            logger.exception("Failed to install color script")
            return False, str(e)

    def _remove_color_script(self) -> None:
        """Remove GRUB color script from /etc/grub.d/ if it exists."""
        script_path = "/etc/grub.d/05_grub_colors"
        try:
            # Check if file exists first
            if not os.path.exists(script_path):
                return

            # Remove with elevated privileges
            rm_cmd = [f"rm -f {script_path}"]
            success, output = self.executor.execute_with_pkexec(rm_cmd)

            if success:
                logger.info("Color script removed from %s", script_path)
            else:
                logger.warning("Failed to remove color script: %s", output)

        except OSError as e:
            logger.warning("Error removing color script: %s", e)

    def _write_config(self, content: str) -> tuple[bool, str]:
        """Write configuration to file.

        Args:
            content: New configuration content

        Returns:
            Tuple of (success, error_message)

        """
        logger.debug("[GRUB_SERVICE] Écriture config dans %s", self.config_path)
        try:
            # Write to temp file first
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".grub") as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            logger.debug("[GRUB_SERVICE] Fichier temporaire créé: %s", tmp_path)

            # Copy with elevated privileges
            success, output = self.executor.copy_file_privileged(tmp_path, self.config_path)

            # Cleanup temp file
            os.unlink(tmp_path)
            logger.debug("[GRUB_SERVICE] Fichier temporaire nettoyé")

            if not success:
                logger.error("[GRUB_SERVICE] Échec copie config: %s", output)
                return False, f"Failed to write config: {output}"

            logger.debug("[GRUB_SERVICE] Configuration écrite dans le fichier système")
            return True, ""

        except OSError as e:
            logger.exception("[GRUB_SERVICE] Échec écriture configuration")
            return False, str(e)

    def _update_grub(self) -> tuple[bool, str]:
        """Update GRUB bootloader.

        Returns:
            Tuple of (success, error_message)

        """
        logger.debug("[GRUB_SERVICE] Mise à jour GRUB (update-grub)")
        try:
            success, output = self.executor.update_grub()
            if not success:
                logger.error("[GRUB_SERVICE] update-grub échec: %s", output)
                return False, f"update-grub failed: {output}"
            logger.debug("[GRUB_SERVICE] GRUB mis à jour avec succès")
            return True, ""
        except (OSError, RuntimeError) as e:
            logger.exception("[GRUB_SERVICE] Exception lors update-grub")
            return False, str(e)

    def restore_backup(self, backup_path: str | None = None) -> bool:
        """Restore from backup.

        Args:
            backup_path: Specific backup to restore (latest if None)

        Returns:
            True if successful

        """
        try:
            restored_path = self.backup_manager.restore_backup(backup_path)
            logger.info("Restored backup: %s", restored_path)

            # Reload configuration
            self.load()

            # Update GRUB
            success, _ = self._update_grub()
            return success

        except (GrubConfigError, OSError) as e:
            logger.exception("Failed to restore backup: %s", e)
            return False

    def _apply_hidden_entries(self) -> tuple[bool, str]:
        """Apply hidden entries to grub.cfg by removing them and save configuration.

        Cette méthode fait deux choses :
        1. Sauvegarde les entrées masquées dans un fichier de configuration persistant
        2. Masque les entrées dans grub.cfg actuel

        Returns:
            Tuple of (success, error_message)

        """
        # Sauvegarder les entrées masquées de manière persistante
        success, error = self.hidden_entries_manager.save_hidden_entries(self.hidden_entries, self.executor)
        if not success:
            logger.error("Échec de sauvegarde des entrées masquées: %s", error)
            return False, error

        if not self.hidden_entries:
            return True, ""

        # Find grub.cfg
        grub_cfg_path = None
        for path in GRUB_CFG_PATHS:
            if os.path.exists(path):
                grub_cfg_path = path
                break

        if not grub_cfg_path:
            logger.warning("grub.cfg not found, cannot hide entries")
            return True, ""

        try:
            return self._process_and_apply_hidden_entries(grub_cfg_path)

        except OSError as e:
            logger.exception("Failed to apply hidden entries")
            return False, str(e)

    def _process_and_apply_hidden_entries(self, grub_cfg_path: str) -> tuple[bool, str]:
        """Process grub.cfg to hide entries and apply changes.

        Args:
            grub_cfg_path: Path to grub.cfg

        Returns:
            Tuple of (success, error_message)

        """
        try:
            with open(grub_cfg_path, encoding="utf-8") as f:
                lines = f.readlines()

            new_lines = self._filter_hidden_entries(lines)

            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".cfg") as tmp:
                tmp.writelines(new_lines)
                tmp_path = tmp.name

            success, output = self.executor.copy_file_privileged(tmp_path, grub_cfg_path)
            os.unlink(tmp_path)

            if not success:
                return False, f"Failed to apply hidden entries: {output}"

            return True, ""

        except OSError as e:
            logger.exception("Failed to process hidden entries")
            return False, str(e)

    def _filter_hidden_entries(self, lines: list[str]) -> list[str]:
        """Filter out hidden entries from grub.cfg lines.

        Args:
            lines: Original lines from grub.cfg

        Returns:
            Filtered lines with hidden entries removed

        """
        new_lines = []
        skipping = False
        skip_level = 0
        current_level = 0

        for line in lines:
            stripped = line.strip()

            is_entry_start = stripped.startswith("menuentry ") or stripped.startswith("submenu ")

            if not skipping and is_entry_start:
                parts = stripped.split("'")
                if len(parts) >= 2:
                    title = parts[1]
                    if title in self.hidden_entries:
                        skipping = True
                        skip_level = current_level

            open_braces = line.count("{")
            close_braces = line.count("}")

            if skipping:
                current_level += open_braces
                current_level -= close_braces

                if current_level <= skip_level:
                    skipping = False

                continue

            new_lines.append(line)
            current_level += open_braces
            current_level -= close_braces

        return new_lines

    def _copy_background_image(self) -> tuple[bool, str]:
        """Copy background image to /boot/grub/backgrounds if it's from user directory.

        Returns:
            Tuple of (success, error_message)

        """
        bg_path = self.entries.get("GRUB_BACKGROUND", "")

        if not bg_path:
            return True, ""

        # Handle solid color backgrounds
        if self._is_solid_color_background(bg_path):
            return self._generate_solid_color_background(bg_path)

        # If already in /boot/grub, no need to copy
        if bg_path.startswith("/boot/grub/"):
            return True, ""

        # If file doesn't exist, skip (validation will catch it later)
        if not os.path.exists(bg_path):
            return True, ""

        # Copy the image file
        return self._copy_image_file(bg_path)

    def _is_solid_color_background(self, bg_path: str) -> bool:
        """Check if background path is a solid color specification."""
        if not isinstance(bg_path, str):
            return False

        stripped = bg_path.strip()
        if stripped.startswith("color:"):
            stripped = stripped.split(":", 1)[1].strip()

        return bool(re.fullmatch(r"#?[0-9a-fA-F]{6}", stripped))

    def _generate_solid_color_background(self, bg_path: str) -> tuple[bool, str]:
        """Generate a solid color PNG background.

        Args:
            bg_path: Color specification (color:#RRGGBB or #RRGGBB)

        Returns:
            Tuple of (success, error_message)

        """
        # Extract hex color
        hex_color = bg_path.strip()
        if hex_color.startswith("color:"):
            hex_color = hex_color.split(":", 1)[1].strip()
        if not hex_color.startswith("#"):
            hex_color = f"#{hex_color}"

        hex_no_hash = hex_color[1:].lower()
        filename = f"solid_{hex_no_hash}.png"
        dest_path = os.path.join(GRUB_BACKGROUNDS_DIR, filename)

        try:
            # Create directory
            success, error = self._ensure_backgrounds_directory()
            if not success:
                return False, error

            # Generate PNG file
            with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".png") as tmp:
                tmp_path = tmp.name

            self._write_solid_color_png(tmp_path, hex_color)

            # Copy to destination
            success, error = self.executor.copy_file_privileged(tmp_path, dest_path)
            os.unlink(tmp_path)

            if not success:
                return False, f"Failed to write solid background image: {error}"

            self.entries["GRUB_BACKGROUND"] = dest_path
            logger.info("Solid background generated: %s", dest_path)
            return True, ""

        except OSError as e:
            logger.exception("Failed to generate solid background")
            return False, str(e)

    def _copy_image_file(self, bg_path: str) -> tuple[bool, str]:
        """Copy image file to /boot/grub/backgrounds.

        Args:
            bg_path: Source image path

        Returns:
            Tuple of (success, error_message)

        """
        try:
            filename = os.path.basename(bg_path)
            dest_path = os.path.join(GRUB_BACKGROUNDS_DIR, filename)

            # Create directory
            success, error = self._ensure_backgrounds_directory()
            if not success:
                return False, error

            # Copy the file
            success, error = self.executor.copy_file_privileged(bg_path, dest_path)
            if not success:
                return False, f"Failed to copy background image: {error}"

            # Update entry
            self.entries["GRUB_BACKGROUND"] = dest_path
            logger.info("Background image copied to %s", dest_path)
            return True, ""

        except OSError as e:
            logger.exception("Failed to copy background image")
            return False, str(e)

    def _ensure_backgrounds_directory(self) -> tuple[bool, str]:
        """Ensure backgrounds directory exists.

        Returns:
            Tuple of (success, error_message)

        """
        mkdir_cmd = f"mkdir -p {GRUB_BACKGROUNDS_DIR}"
        success, error = self.executor.execute_with_pkexec([mkdir_cmd])
        if not success:
            return False, f"Failed to create backgrounds directory: {error}"
        return True, ""

    @staticmethod
    def _write_solid_color_png(file_path: str, hex_color: str) -> None:
        """Write a minimal 1x1 PNG with a single RGB color.

        Args:
            file_path: Path where to write the PNG
            hex_color: Color in #RRGGBB format

        """

        def _chunk(chunk_type: bytes, data: bytes) -> bytes:
            length = struct.pack(">I", len(data))
            crc = zlib.crc32(chunk_type)
            crc = zlib.crc32(data, crc)
            return length + chunk_type + data + struct.pack(">I", crc & 0xFFFFFFFF)

        hex_color = hex_color.strip()
        if hex_color.startswith("color:"):
            hex_color = hex_color.split(":", 1)[1].strip()
        if not hex_color.startswith("#"):
            hex_color = f"#{hex_color}"

        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)

        signature = b"\x89PNG\r\n\x1a\n"
        ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
        # filter byte 0 + RGB
        raw = bytes([0, r, g, b])
        idat = zlib.compress(raw)
        png = signature + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", idat) + _chunk(b"IEND", b"")

        with open(file_path, "wb") as f:
            f.write(png)
