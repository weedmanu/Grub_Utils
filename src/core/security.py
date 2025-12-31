"""Couche de sécurité - Validation d'entrées et prévention des injections."""

import re
from typing import Any


class SecurityError(ValueError):
    """Raise when input validation fails."""


class InputSecurityValidator:
    """Validate user inputs against injection attacks."""

    # Limites de taille
    MAX_LINE_LENGTH = 4096
    MAX_VALUE_LENGTH = 512
    MAX_PARAM_NAME_LENGTH = 256

    # Patterns dangereux
    SHELL_METACHARACTERS = r'[;&|`$(){}[\]<>\\"\']'
    NEWLINE_PATTERN = r"[\r\n\0]"

    @staticmethod
    def validate_line(value: str) -> str:
        """Validate a configuration line.

        Args:
            value: Ligne à valider

        Returns:
            str: Ligne validée et nettoyée

        Raises:
            SecurityError: Si la ligne contient des patterns dangereux

        """
        if not isinstance(value, str):
            raise SecurityError("Value must be a string")

        if len(value) > InputSecurityValidator.MAX_LINE_LENGTH:
            raise SecurityError(f"Line too long (max {InputSecurityValidator.MAX_LINE_LENGTH})")

        if re.search(InputSecurityValidator.NEWLINE_PATTERN, value):
            raise SecurityError("Newlines not allowed in values")

        return value.strip()

    @staticmethod
    def validate_parameter_name(param_name: str) -> str:
        """Validate a GRUB parameter name.

        Args:
            param_name: Nom du paramètre

        Returns:
            str: Nom validé

        Raises:
            SecurityError: Si le nom est invalide

        """
        if not param_name:
            raise SecurityError("Parameter name cannot be empty")

        if len(param_name) > InputSecurityValidator.MAX_PARAM_NAME_LENGTH:
            raise SecurityError("Parameter name too long")

        if not re.match(r"^[A-Z_][A-Z0-9_]*$", param_name):
            raise SecurityError("Invalid parameter name format")

        return param_name

    @staticmethod
    def validate_kernel_params(params: str) -> str:
        """Validate kernel parameters.

        Args:
            params: Chaîne de paramètres noyau

        Returns:
            str: Paramètres validés

        Raises:
            SecurityError: Si les paramètres contiennent des patterns dangereux

        """
        value = InputSecurityValidator.validate_line(params)

        # Interdire les pipes, redirections, substitutions
        if re.search(r"[|<>$`]", value):
            raise SecurityError("Shell metacharacters not allowed in kernel parameters")

        return value

    @staticmethod
    def validate_file_path(path: str) -> str:
        """Validate a file path against directory traversal.

        Args:
            path: Chemin du fichier

        Returns:
            str: Chemin validé

        Raises:
            SecurityError: Si le chemin essaie une traversée de répertoires

        """
        if not path:
            raise SecurityError("Path cannot be empty")

        if ".." in path:
            raise SecurityError("Directory traversal not allowed")

        if path.startswith("~"):
            raise SecurityError("Tilde expansion not allowed")

        # Vérifier que le chemin n'essaie pas d'accéder hors de /boot ou /etc
        if not path.startswith(("/etc/", "/boot/", "/tmp/", "/var/")):
            raise SecurityError(f"Path {path} not in allowed directories")

        return path

