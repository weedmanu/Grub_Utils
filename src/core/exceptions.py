"""Exceptions personnalisées pour GRUB Manager."""


class GrubError(Exception):
    """Exception de base pour les erreurs GRUB."""


class GrubPermissionError(GrubError):
    """Exception levée lorsque les permissions sont insuffisantes."""


class GrubConfigError(GrubError):
    """Exception levée lors d'erreurs de configuration."""


class GrubValidationError(GrubError):
    """Exception levée lors d'erreurs de validation."""


class GrubBackupError(GrubError):
    """Exception levée lors d'erreurs de sauvegarde."""
