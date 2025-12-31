"""Validation des entrées utilisateur pour GRUB."""

import os
import re
from typing import Dict, Optional

from src.utils.config import GRUB_TIMEOUT_MAX
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GrubValidationError(ValueError):
    """Exception levée lorsqu'une validation échoue."""


class GrubValidator:
    """Classe pour valider les entrées utilisateur de GRUB."""

    # Extensions autorisées pour les fichiers
    ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tga"}
    ALLOWED_THEME_EXTENSIONS = {".txt"}

    # Patterns de validation
    GFXMODE_PATTERN = re.compile(r"^(auto|\d{3,4}x\d{3,4})$")
    TIMEOUT_PATTERN = re.compile(r"^\d+$")

    # Liste blanche des paramètres kernel courants
    ALLOWED_KERNEL_PARAMS = {
        "quiet",
        "splash",
        "nomodeset",
        "ro",
        "rw",
        "initrd",
        "root",
        "console",
        "loglevel",
        "debug",
        "noresume",
        "acpi",
        "pci",
        "usb",
        "scsi",
        "ata",
        "ide",
        "nvme",
        "ahci",
        "xhci",
        "ehci",
        "ohci",
        "uhci",
        "pata",
        "sata",
        "raid",
        "lvm",
        "crypt",
        "dm",
        "md",
        "btrfs",
        "ext4",
        "xfs",
        "zfs",
        "swap",
        "resume",
        "uuid",
        "label",
        "partuuid",
        "gpt",
        "mbr",
        "bios",
        "efi",
        "uefi",
        "secureboot",
        "tpm",
        "ima",
        "evm",
        "apparmor",
        "selinux",
        "audit",
        "syslog",
        "kmsg",
        "printk",
        "panic",
        "reboot",
        "poweroff",
        "halt",
        "emergency",
        "single",
        "rescue",
        "recovery",
    }

    @staticmethod
    def validate_timeout(timeout_str: str) -> int:
        """
        Validate GRUB timeout.

        Args:
            timeout_str: Chaîne représentant le timeout.

        Returns:
            int: Timeout validé.

        Raises:
            GrubValidationError: Si invalide.
        """
        if not timeout_str:
            return 5  # Valeur par défaut

        if not GrubValidator.TIMEOUT_PATTERN.match(timeout_str):
            raise GrubValidationError("Le timeout doit être un entier positif")

        timeout = int(timeout_str)
        if not 0 <= timeout <= GRUB_TIMEOUT_MAX:
            raise GrubValidationError(f"Le timeout doit être entre 0 et {GRUB_TIMEOUT_MAX} secondes")

        return timeout

    @staticmethod
    def validate_gfxmode(gfxmode: str) -> str:
        """
        Validate GFXMODE resolution.

        Args:
            gfxmode: Chaîne de résolution.

        Returns:
            str: GFXMODE validé.

        Raises:
            GrubValidationError: Si invalide.
        """
        if not gfxmode or gfxmode.lower() == "auto":
            return "auto"

        if not GrubValidator.GFXMODE_PATTERN.match(gfxmode):
            raise GrubValidationError("Format de résolution invalide (utilisez NNNNxNNNN ou 'auto')")

        return gfxmode

    @staticmethod
    def validate_file_path(file_path: str, allowed_extensions: set) -> Optional[str]:
        """
        Validate a file path.

        Args:
            file_path: Chemin du fichier.
            allowed_extensions: Extensions autorisées.

        Returns:
            str or None: Chemin validé ou None si vide.

        Raises:
            GrubValidationError: Si invalide.
        """
        if not file_path:
            return None

        # Vérifier que le fichier existe
        if not os.path.exists(file_path):
            raise GrubValidationError(f"Le fichier n'existe pas: {file_path}")

        # Vérifier que c'est un fichier (pas un répertoire)
        if not os.path.isfile(file_path):
            raise GrubValidationError(f"Le chemin n'est pas un fichier: {file_path}")

        # Vérifier l'extension
        _, ext = os.path.splitext(file_path.lower())
        if ext not in allowed_extensions:
            allowed_str = ", ".join(allowed_extensions)
            raise GrubValidationError(f"Extension non autorisée. Extensions permises: {allowed_str}")

        # Vérifier les permissions de lecture
        if not os.access(file_path, os.R_OK):
            raise GrubValidationError(f"Impossible de lire le fichier: {file_path}")

        return file_path

    @staticmethod
    def validate_kernel_params(params_str: str) -> str:
        """
        Validate kernel parameters.

        Args:
            params_str: Chaîne des paramètres.

        Returns:
            str: Paramètres validés.

        Raises:
            GrubValidationError: Si invalide.
        """
        if not params_str:
            return ""

        # Diviser en paramètres individuels
        params = params_str.split()

        # Vérifier chaque paramètre
        for param in params:
            # Supprimer les valeurs après =
            param_key = param.split("=", 1)[0]

            # Vérifier les caractères autorisés (alphanumériques, tirets, underscores, égal, point, slash)
            if not re.match(r"^[a-zA-Z0-9_=-]+$", param_key):
                raise GrubValidationError(f"Paramètre noyau invalide: {param_key}")

            # Vérifier contre la liste blanche (si pas de valeur)
            if "=" not in param and param not in GrubValidator.ALLOWED_KERNEL_PARAMS:
                logger.warning("Paramètre noyau non standard: %s", param)

        return params_str

    @staticmethod
    def validate_all(entries: Dict[str, str]) -> None:
        """
        Validate all GRUB entries.

        Args:
            entries: Dictionnaire des entrées GRUB.

        Raises:
            GrubValidationError: Si une validation échoue.
        """
        try:
            # Valider le timeout
            if "GRUB_TIMEOUT" in entries:
                entries["GRUB_TIMEOUT"] = str(GrubValidator.validate_timeout(entries["GRUB_TIMEOUT"]))

            # Valider GFXMODE
            if "GRUB_GFXMODE" in entries:
                entries["GRUB_GFXMODE"] = GrubValidator.validate_gfxmode(entries["GRUB_GFXMODE"])

            # Valider l'image de fond
            if "GRUB_BACKGROUND" in entries:
                validated_path = GrubValidator.validate_file_path(
                    entries["GRUB_BACKGROUND"], GrubValidator.ALLOWED_IMAGE_EXTENSIONS
                )
                if validated_path is None:
                    del entries["GRUB_BACKGROUND"]
                else:
                    entries["GRUB_BACKGROUND"] = validated_path

            # Valider le thème
            if "GRUB_THEME" in entries:
                validated_path = GrubValidator.validate_file_path(
                    entries["GRUB_THEME"], GrubValidator.ALLOWED_THEME_EXTENSIONS
                )
                if validated_path is None:
                    del entries["GRUB_THEME"]
                else:
                    entries["GRUB_THEME"] = validated_path

            # Valider les paramètres noyau
            if "GRUB_CMDLINE_LINUX_DEFAULT" in entries:
                entries["GRUB_CMDLINE_LINUX_DEFAULT"] = GrubValidator.validate_kernel_params(
                    entries["GRUB_CMDLINE_LINUX_DEFAULT"]
                )

        except GrubValidationError:
            raise  # Re-lever l'exception
        except Exception as e:
            logger.exception("Erreur inattendue lors de la validation")
            raise GrubValidationError(f"Erreur de validation: {e}") from e
