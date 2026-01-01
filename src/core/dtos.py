"""Data Transfer Objects pour découpler l'UI du Core."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BackupInfoDTO:
    """DTO pour les informations de sauvegarde."""

    path: str
    timestamp: float
    size_bytes: int
    is_valid: bool


@dataclass(frozen=True)
class OperationResultDTO:
    """DTO pour le résultat d'une opération."""

    success: bool
    message: str
    error_details: str | None = None


@dataclass(frozen=True)
class PreviewConfigDTO:
    """DTO for preview dialog configuration comparison."""

    old_config: dict[str, str]
    new_config: dict[str, str]
    menu_entries: list[dict] | None = None
    hidden_entries: list[str] | None = None

    @property
    def has_changes(self) -> bool:
        """Check if there are changes between old and new config."""
        return self.old_config != self.new_config
