"""Prévisualisation de l'interface complète.

But:
- Ouvrir l'application complète avec un backend simulé.
- Permettre de tester la navigation entre les onglets et l'interaction globale.

Usage:
- Depuis la racine du projet:
  - ./ .venv/bin/python script/preview_ui.py
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

# Ajouter la racine du projet au path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import des modules nécessaires
from src.core.dtos import OperationResultDTO
from src.ui import app as ui_app


# --- Mocking du Backend ---

class MockBackupManager:
    def create_original_backup_if_needed(self):
        return True
    
    def list_backups(self):
        return ["/tmp/mock_backup_1", "/tmp/mock_backup_2"]
    
    def get_latest_backup(self):
        return "/tmp/mock_backup_2"

class MockService:
    def __init__(self):
        self.backup_manager = MockBackupManager()
        # Minimal executor used by theme config/theme generator code paths.
        self.executor = MagicMock()
        self.executor.execute_with_pkexec.return_value = (True, "")
        self.executor.copy_file_privileged.return_value = (True, "")
        self.executor.update_grub.return_value = (True, "")
        self.entries = {
            "GRUB_DEFAULT": "0",
            "GRUB_TIMEOUT": "5",
            "GRUB_CMDLINE_LINUX_DEFAULT": "quiet splash",
            "GRUB_GFXMODE": "1920x1080",
            "GRUB_BACKGROUND": "/usr/share/images/desktop-base/desktop-grub.png",
            "GRUB_COLOR_NORMAL": "light-gray/black",
            "GRUB_COLOR_HIGHLIGHT": "white/dark-gray",
        }
        self.menu_entries = [
            {"title": "Ubuntu", "submenu": False},
            {"title": "Advanced options for Ubuntu", "submenu": True},
            {"title": "Windows Boot Manager", "submenu": False},
        ]
        self.hidden_entries = ["Windows Boot Manager"]

    def load(self):
        pass

    def save_and_apply(self):
        return True, None

    def restore_backup(self, path):
        return True

class MockFacade:
    def __init__(self, config_path=None):
        self._service = MockService()
        self._loaded = False

    @property
    def grub_service(self):
        # UI tabs expect facade.grub_service.executor
        return self._service

    def ensure_original_backup(self) -> bool:
        # Called on app activation.
        return bool(self._service.backup_manager.create_original_backup_if_needed())

    def load_configuration(self) -> OperationResultDTO:
        self._loaded = True
        return OperationResultDTO(success=True, message="Configuration loaded successfully")

    def apply_changes(self) -> OperationResultDTO:
        return OperationResultDTO(success=True, message="Configuration applied successfully")

    def list_backups(self):
        # Retourne des objets compatibles avec BackupInfoDTO
        b1 = SimpleNamespace()
        b1.path = "/tmp/grub.bak.20231027_100000"
        b1.timestamp = datetime(2023, 10, 27, 10, 0, 0).timestamp()
        b1.size_bytes = 10240
        b1.is_valid = True
        
        b2 = SimpleNamespace()
        b2.path = "/tmp/grub.bak.original"
        b2.timestamp = datetime(2023, 1, 1, 12, 0, 0).timestamp()
        b2.size_bytes = 5120
        b2.is_valid = True
        
        return [b1, b2]

    def restore_backup(self, backup_path=None):
        return OperationResultDTO(success=True, message="Backup restored successfully")

    @property
    def entries(self) -> dict[str, str]:
        return self._service.entries

    @entries.setter
    def entries(self, value: dict[str, str]) -> None:
        self._service.entries = value

    @property
    def menu_entries(self) -> list[dict]:
        return self._service.menu_entries

    @property
    def hidden_entries(self) -> list[str]:
        return self._service.hidden_entries

    @hidden_entries.setter
    def hidden_entries(self, value: list[str]) -> None:
        self._service.hidden_entries = value

    def has_backups(self) -> bool:
        return True


# --- Monkeypatching ---

# Remplacer la classe GrubFacade par notre MockFacade dans le module ui.app
ui_app.GrubFacade = MockFacade


# --- Main ---

def main() -> int:
    # Lancer l'application
    app = ui_app.GrubApp()
    return app.run(None)


if __name__ == "__main__":
    raise SystemExit(main())
