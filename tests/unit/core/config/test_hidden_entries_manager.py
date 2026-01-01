"""Tests pour le gestionnaire d'entrées masquées."""

import json
import os
import tempfile
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.core.config.hidden_entries_manager import HiddenEntriesManager


@pytest.fixture
def temp_config_path():
    """Fixture pour créer un fichier de configuration temporaire."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def manager(temp_config_path):
    """Fixture pour créer un gestionnaire avec un chemin temporaire."""
    return HiddenEntriesManager(temp_config_path)


@pytest.fixture
def mock_executor():
    """Fixture pour créer un mock de SecureCommandExecutor."""
    executor = MagicMock()
    executor.write_file_privileged.return_value = (True, "")
    executor.run_command.return_value = (True, "")
    return executor


class TestHiddenEntriesManager:
    """Tests pour HiddenEntriesManager."""

    def test_load_hidden_entries_file_not_exists(self, manager):
        """Test du chargement quand le fichier n'existe pas."""
        hidden = manager.load_hidden_entries()
        assert hidden == []

    def test_load_hidden_entries_success(self, manager, temp_config_path):
        """Test du chargement réussi des entrées."""
        config_data = {
            "hidden_entries": ["Entry1", "Entry2", "Entry3"],
            "version": "1.0"
        }
        with open(temp_config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        hidden = manager.load_hidden_entries()
        assert hidden == ["Entry1", "Entry2", "Entry3"]

    def test_load_hidden_entries_invalid_json(self, manager, temp_config_path):
        """Test du chargement avec un JSON invalide."""
        with open(temp_config_path, "w", encoding="utf-8") as f:
            f.write("invalid json {")

        hidden = manager.load_hidden_entries()
        assert hidden == []

    def test_save_hidden_entries_success(self, manager, mock_executor):
        """Test de la sauvegarde réussie des entrées."""
        entries = ["Entry1", "Entry2"]
        success, error = manager.save_hidden_entries(entries, mock_executor)

        assert success is True
        assert error == ""
        assert mock_executor.write_file_privileged.call_count == 2  # Config + script

    def test_save_hidden_entries_empty_list(self, manager, mock_executor):
        """Test de la sauvegarde d'une liste vide."""
        success, error = manager.save_hidden_entries([], mock_executor)

        assert success is True
        assert error == ""

    def test_save_hidden_entries_write_fail(self, manager, mock_executor):
        """Test de la sauvegarde quand l'écriture échoue."""
        mock_executor.write_file_privileged.return_value = (False, "Permission denied")
        entries = ["Entry1"]

        success, error = manager.save_hidden_entries(entries, mock_executor)

        assert success is False
        assert "Permission denied" in error

    def test_clear_hidden_entries(self, manager, mock_executor):
        """Test de la suppression de toutes les entrées masquées."""
        success, error = manager.clear_hidden_entries(mock_executor)

        assert success is True
        # Vérifie que save_hidden_entries a été appelé avec une liste vide
        mock_executor.write_file_privileged.assert_called()

    def test_remove_config_files_success(self, manager, mock_executor, temp_config_path):
        """Test de la suppression des fichiers de configuration."""
        # Créer le fichier
        with open(temp_config_path, "w") as f:
            f.write("{}")

        success, error = manager.remove_config_files(mock_executor)

        assert success is True
        assert error == ""
        assert mock_executor.run_command.call_count == 2  # rm config + rm script

    def test_remove_config_files_not_exists(self, manager, mock_executor):
        """Test de la suppression quand les fichiers n'existent pas."""
        success, error = manager.remove_config_files(mock_executor)

        assert success is True
        # Devrait quand même essayer de supprimer
        assert mock_executor.run_command.call_count >= 1

    def test_create_grub_script_success(self, manager, mock_executor):
        """Test de la création du script GRUB."""
        success, error = manager._create_grub_script(mock_executor)

        assert success is True
        assert error == ""
        # Vérifie que le script est créé et rendu exécutable
        assert mock_executor.write_file_privileged.called
        assert mock_executor.run_command.called

    def test_create_grub_script_chmod_fail(self, manager, mock_executor):
        """Test de la création du script quand chmod échoue."""
        mock_executor.run_command.return_value = (False, "chmod failed")

        success, error = manager._create_grub_script(mock_executor)

        assert success is False
        assert "chmod failed" in error


@pytest.mark.integration
class TestHiddenEntriesIntegration:
    """Tests d'intégration pour le gestionnaire."""

    def test_save_and_load_cycle(self, manager, mock_executor, temp_config_path):
        """Test du cycle complet sauvegarde-chargement."""
        # Mock pour simuler l'écriture réussie
        def write_side_effect(path, content):
            if path == temp_config_path:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
            return True, ""

        mock_executor.write_file_privileged.side_effect = write_side_effect

        # Sauvegarder
        entries = ["Ubuntu (recovery)", "Windows Boot Manager"]
        success, _ = manager.save_hidden_entries(entries, mock_executor)
        assert success is True

        # Charger
        loaded = manager.load_hidden_entries()
        assert loaded == entries

    def test_multiple_saves_overwrite(self, manager, mock_executor, temp_config_path):
        """Test que les sauvegardes multiples écrasent les précédentes."""
        def write_side_effect(path, content):
            if path == temp_config_path:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
            return True, ""

        mock_executor.write_file_privileged.side_effect = write_side_effect

        # Première sauvegarde
        manager.save_hidden_entries(["Entry1", "Entry2"], mock_executor)
        first_load = manager.load_hidden_entries()

        # Deuxième sauvegarde
        manager.save_hidden_entries(["Entry3"], mock_executor)
        second_load = manager.load_hidden_entries()

        assert first_load != second_load
        assert second_load == ["Entry3"]
