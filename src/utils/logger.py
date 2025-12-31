"""Configuration du système de logging pour GRUB Manager."""

import logging
import logging.handlers
import os


def get_log_path() -> str:
    """Détermine le chemin du fichier de log en fonction des permissions.

    Returns:
        str: Chemin du fichier de log.

    """
    # Essayer d'abord /var/log si on a les droits (root)
    system_log = "/var/log/grub-manager/app.log"
    try:
        os.makedirs(os.path.dirname(system_log), exist_ok=True)
        with open(system_log, "a", encoding="utf-8"):
            pass  # Test d'écriture
        return system_log
    except (OSError, PermissionError):
        pass

    # Fallback vers le répertoire utilisateur
    user_log = os.path.expanduser("~/.local/share/grub-manager/app.log")
    os.makedirs(os.path.dirname(user_log), exist_ok=True)
    return user_log


def get_logger(name: str) -> logging.Logger:
    """Obtain a logger for a specific module.

    Args:
        name: Nom du module (généralement __name__)

    Returns:
        logging.Logger: Logger pour le module.

    """
    return logging.getLogger(f"grub_manager.{name}")


def setup_logging(debug: bool = False) -> None:
    """Configure the logging system for the entire application.

    Args:
        debug: Enable debug logging level.

    """
    log_path = get_log_path()
    log_level = logging.DEBUG if debug else logging.INFO

    # Root logger configuration
    root_logger = logging.getLogger("grub_manager")
    root_logger.setLevel(log_level)

    # File handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(log_level)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
