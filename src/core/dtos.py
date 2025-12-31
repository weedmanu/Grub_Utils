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
