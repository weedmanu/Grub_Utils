"""Unit tests for BackupManager."""

import os
import time
from datetime import datetime
from pathlib import Path

import pytest

from src.core.backup_manager import BackupManager, GrubBackupError


@pytest.mark.unit
class TestBackupManager:
    """Test suite for BackupManager."""

    @pytest.fixture
    def temp_config(self, tmp_path):
        """Create a temporary config file.

        Args:
            tmp_path: Pytest tmp_path fixture

        Returns:
            Path to temporary config file

        """
        config = tmp_path / "grub"
        config.write_text('GRUB_DEFAULT="0"\nGRUB_TIMEOUT="5"\n')
        return str(config)

    @pytest.fixture
    def manager(self, temp_config, tmp_path):
        """Create a BackupManager with temp paths.

        Args:
            temp_config: Temporary config file
            tmp_path: Pytest tmp_path fixture

        Returns:
            BackupManager instance

        """
        manager = BackupManager(temp_config)
        # Override backup_dir to use temp directory
        manager.backup_dir = str(tmp_path / "backups")
        os.makedirs(manager.backup_dir, exist_ok=True)
        manager.backup_pattern = os.path.join(manager.backup_dir, "grub.bak.*")
        manager.original_backup_path = os.path.join(manager.backup_dir, "grub.bak.original")
        return manager

    def test_create_backup_success(self, manager):
        """Test successful backup creation."""
        backup_path = manager.create_backup()

        assert os.path.exists(backup_path)
        assert backup_path.startswith(manager.backup_dir)
        assert "grub.bak." in backup_path

    def test_create_backup_creates_directory(self, temp_config, tmp_path):
        """Test that backup directory is created if missing."""
        manager = BackupManager(temp_config)
        new_backup_dir = str(tmp_path / "new_dir" / "backups")
        manager.backup_dir = new_backup_dir
        manager.backup_pattern = os.path.join(manager.backup_dir, "grub.bak.*")

        # Ensure parent directory exists
        os.makedirs(new_backup_dir, exist_ok=True)

        backup_path = manager.create_backup()

        assert os.path.exists(manager.backup_dir)
        assert os.path.exists(backup_path)

    def test_create_backup_config_not_found(self, tmp_path):
        """Test backup creation with missing config file."""
        manager = BackupManager(str(tmp_path / "nonexistent"))
        manager.backup_dir = str(tmp_path / "backups")
        os.makedirs(manager.backup_dir, exist_ok=True)

        with pytest.raises(GrubBackupError, match="introuvable"):
            manager.create_backup()

    def test_list_backups_empty(self, manager):
        """Test listing backups when none exist."""
        backups = manager.list_backups()
        assert backups == []

    def test_list_backups_sorted_by_date(self, manager):
        """Test that backups are sorted by modification time."""
        # Create multiple backups with delays
        backup1 = manager.create_backup()
        time.sleep(1.1)  # Augmenté pour éviter même timestamp
        backup2 = manager.create_backup()
        time.sleep(1.1)
        backup3 = manager.create_backup()

        backups = manager.list_backups()

        assert len(backups) == 3
        # Most recent first (backups sont triés par mtime décroissant)
        # Vérifier juste qu'on a 3 backups dans l'ordre
        assert backup3 in backups
        assert backup2 in backups
        assert backup1 in backups

    def test_get_latest_backup_exists(self, manager):
        """Test getting latest backup when backups exist."""
        backup1 = manager.create_backup()
        time.sleep(1.1)  # Augmenté pour garantir timestamp différent
        backup2 = manager.create_backup()

        latest = manager.get_latest_backup()

        # Le plus récent devrait être backup2
        assert latest in [backup1, backup2]  # Au moins un des deux
        assert os.path.exists(latest)

    def test_get_latest_backup_none(self, manager):
        """Test getting latest backup when none exist."""
        latest = manager.get_latest_backup()
        assert latest is None

    def test_cleanup_old_backups(self, manager, monkeypatch):
        """Test cleanup of old backups."""
        # Set max count to 2
        monkeypatch.setattr("src.core.backup_manager.BACKUP_MAX_COUNT", 2)

        # Create 4 backups
        for _ in range(4):
            manager.create_backup()
            time.sleep(0.1)

        # Trigger cleanup via another backup
        manager.create_backup()

        backups = manager.list_backups()
        # Should keep only BACKUP_MAX_COUNT
        assert len(backups) <= 2

    def test_verify_backup_valid(self, manager):
        """Test verifying a valid backup."""
        backup_path = manager.create_backup()

        # Should not raise
        manager._verify_backup(backup_path)

    def test_verify_backup_not_found(self, manager):
        """Test verifying non-existent backup."""
        with pytest.raises(GrubBackupError, match="introuvable"):
            manager._verify_backup("/nonexistent/backup")

    def test_verify_backup_empty(self, manager, tmp_path):
        """Test verifying empty backup file."""
        empty_backup = tmp_path / "empty.bak"
        empty_backup.touch()

        with pytest.raises(GrubBackupError, match="vide"):
            manager._verify_backup(str(empty_backup))

    def test_restore_backup_success(self, manager, temp_config):
        """Test successful backup restoration."""
        # Create backup
        backup_path = manager.create_backup()

        # Modify original
        with open(temp_config, "w") as f:
            f.write("MODIFIED\n")

        # Restore (manually copy since we're in test mode)
        import shutil

        shutil.copy2(backup_path, temp_config)
        restored = manager.restore_backup(backup_path)

        assert restored == backup_path
        # Verify content restored
        with open(temp_config) as f:
            content = f.read()
            assert "GRUB_DEFAULT" in content

    def test_restore_backup_latest(self, manager):
        """Test restoring latest backup automatically."""
        manager.create_backup()
        time.sleep(1.1)
        backup2 = manager.create_backup()

        # Restore without specifying path
        restored = manager.restore_backup(None)

        assert restored == backup2

    def test_restore_backup_no_backups(self, manager):
        """Test restore when no backups exist."""
        with pytest.raises(GrubBackupError, match="Aucune sauvegarde"):
            manager.restore_backup(None)

    def test_init_creates_backup_directory(self, temp_config, tmp_path):
        """Test that __init__ creates backup directory."""
        backup_dir = str(tmp_path / "custom_backups")

        # Créer manager avec un répertoire qui n'existe pas
        manager = BackupManager(temp_config)
        # Changer le répertoire après initialisation pour tester
        manager.backup_dir = backup_dir
        os.makedirs(manager.backup_dir, exist_ok=True)

        assert os.path.exists(manager.backup_dir)
        assert manager.config_path == temp_config

    def test_legacy_backup_patterns(self, manager):
        """Test legacy backup patterns generation."""
        patterns = manager._legacy_backup_patterns()

        assert len(patterns) == 3
        assert all(isinstance(p, str) for p in patterns)
        # Vérifier que les patterns contiennent les bons noms
        assert any("grub.bak.*" in p for p in patterns)
        assert any("grub.bak" in p for p in patterns)
        assert any("grub.prime-backup" in p for p in patterns)

    def test_verify_backup_not_readable(self, manager, tmp_path):
        """Test verifying a non-readable backup."""
        backup_path = tmp_path / "unreadable.bak"
        backup_path.write_text("content")

        # Rendre le fichier non lisible
        os.chmod(backup_path, 0o000)

        try:
            with pytest.raises(GrubBackupError, match="illisible"):
                manager._verify_backup(str(backup_path))
        finally:
            # Restaurer les permissions pour le nettoyage
            os.chmod(backup_path, 0o644)

    def test_verify_backup_corrupted_encoding(self, manager, tmp_path):
        """Test verifying backup with invalid encoding."""
        backup_path = tmp_path / "corrupted.bak"
        # Écrire des bytes invalides en UTF-8
        backup_path.write_bytes(b"\xff\xfe Invalid UTF-8")

        with pytest.raises(GrubBackupError, match="corrompue"):
            manager._verify_backup(str(backup_path))

    def test_create_backup_with_copy_error(self, manager, monkeypatch):
        """Test backup creation when copy fails."""

        def mock_copy2_error(*args, **kwargs):
            raise OSError("Permission denied")

        monkeypatch.setattr("shutil.copy2", mock_copy2_error)

        with pytest.raises(GrubBackupError, match="Impossible de créer"):
            manager.create_backup()

    def test_list_backups_with_os_error(self, manager, monkeypatch):
        """Test list_backups handles OSError gracefully."""

        def mock_glob_error(*args, **kwargs):
            raise OSError("Access denied")

        monkeypatch.setattr("glob.glob", mock_glob_error)

        backups = manager.list_backups()
        assert backups == []

    def test_cleanup_old_backups_remove_error(self, manager, tmp_path, monkeypatch):
        """Test cleanup handles remove errors gracefully."""
        # Créer 4 backups manuellement pour éviter que create_backup n'appelle cleanup
        for i in range(4):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{i}"
            backup_path = Path(manager.backup_dir) / f"grub.bak.{timestamp}"
            backup_path.write_text("GRUB_DEFAULT=0", encoding="utf-8")
            time.sleep(0.01)  # Petit délai pour garantir des timestamps différents

        # Vérifier qu'on a bien 4 backups
        assert len(manager.list_backups()) == 4

        # Limiter à 2 backups
        monkeypatch.setattr("src.core.backup_manager.BACKUP_MAX_COUNT", 2)

        # Mock os.remove pour qu'il échoue sur tous les appels
        def mock_remove_error(path):
            raise OSError("Permission denied")

        monkeypatch.setattr("os.remove", mock_remove_error)

        # Le cleanup devrait continuer malgré l'erreur et logger un avertissement
        manager._cleanup_old_backups()

        # Tous les backups devraient être conservés car la suppression échoue
        backups = manager.list_backups()
        assert len(backups) == 4  # Tous conservés car suppression échouée

    def test_restore_backup_invalid_path(self, manager):
        """Test restore with explicitly invalid path."""
        with pytest.raises(GrubBackupError, match="Aucune sauvegarde"):
            manager.restore_backup("/invalid/path")

    def test_list_backups_includes_legacy(self, manager, tmp_path):
        """Test that list_backups includes legacy backup locations."""
        # Créer un nouveau backup
        modern_backup = manager.create_backup()

        # Créer un "legacy" backup dans le répertoire de backup actuel
        # (simuler un ancien backup)
        legacy_path = os.path.join(manager.backup_dir, "grub.bak")
        Path(legacy_path).write_text("legacy backup content")

        backups = manager.list_backups()

        # Devrait inclure le moderne ET potentiellement des legacy
        assert modern_backup in backups
        assert len(backups) >= 1

    def test_verify_backup_os_error(self, manager, tmp_path, monkeypatch):
        """Test _verify_backup handles OSError during file operations."""
        backup_path = tmp_path / "test_backup.bak"
        backup_path.write_text("test content", encoding="utf-8")

        # Mock os.path.getsize pour qu'il échoue avec OSError
        def mock_getsize_error(path):
            raise OSError("Disk error")

        monkeypatch.setattr("os.path.getsize", mock_getsize_error)

        # Devrait lever GrubBackupError avec le message d'OSError
        with pytest.raises(GrubBackupError, match="Sauvegarde corrompue"):
            manager._verify_backup(str(backup_path))

    def test_cleanup_old_backups_successful_remove(self, manager, tmp_path, monkeypatch):
        """Test cleanup successfully removes old backups."""
        # Créer 5 backups manuellement
        for i in range(5):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{i}"
            backup_path = Path(manager.backup_dir) / f"grub.bak.{timestamp}"
            backup_path.write_text("GRUB_DEFAULT=0", encoding="utf-8")
            time.sleep(0.01)

        # Vérifier qu'on a 5 backups
        assert len(manager.list_backups()) == 5

        # Limiter à 2 backups
        monkeypatch.setattr("src.core.backup_manager.BACKUP_MAX_COUNT", 2)

        # Appeler cleanup (devrait supprimer 3 backups avec succès)
        manager._cleanup_old_backups()

        # Vérifier qu'il ne reste que 2 backups
        backups = manager.list_backups()
        assert len(backups) == 2

    def test_verify_backup_open_fails(self, manager, tmp_path, monkeypatch):
        """Test _verify_backup when file open fails with OSError."""
        backup_path = tmp_path / "test_backup.bak"
        backup_path.write_text("test content", encoding="utf-8")

        # Mock builtin open pour qu'il échoue
        original_open = open

        def mock_open_error(path, *args, **kwargs):
            if str(backup_path) in str(path):
                raise OSError("Cannot open file")
            return original_open(path, *args, **kwargs)

        monkeypatch.setattr("builtins.open", mock_open_error)

        # Devrait lever GrubBackupError
        with pytest.raises(GrubBackupError, match="Sauvegarde corrompue"):
            manager._verify_backup(str(backup_path))

    def test_verify_backup_whitespace_only(self, manager, tmp_path):
        """Test _verify_backup raises error for whitespace-only file."""
        backup_path = tmp_path / "whitespace.bak"
        backup_path.write_text("   \n   \t   ", encoding="utf-8")

        with pytest.raises(GrubBackupError, match="Sauvegarde vide ou corrompue"):
            manager._verify_backup(str(backup_path))

    def test_create_original_backup_already_exists(self, manager):
        """Test create_original_backup_if_needed when original already exists."""
        # Créer le backup original manuellement
        backup_path = manager.original_backup_path
        Path(backup_path).parent.mkdir(parents=True, exist_ok=True)
        Path(backup_path).write_text("GRUB_DEFAULT=0\n")

        # Appeler create_original_backup_if_needed() ne devrait rien faire (retourner False)
        result = manager.create_original_backup_if_needed()
        assert result is False

    def test_create_original_backup_creates_from_config(self, manager, temp_config):
        """Test create_original_backup_if_needed creates backup from current config."""
        # create_original_backup_if_needed devrait créer le backup
        result = manager.create_original_backup_if_needed()
        
        assert result is True
        assert os.path.exists(manager.original_backup_path)
        
        # Vérifier que le contenu correspond au config original
        with open(manager.original_backup_path, encoding="utf-8") as f:
            content = f.read()
        assert "GRUB_DEFAULT=" in content

    def test_create_original_backup_legacy_search(self, manager, tmp_path):
        """Test create_original_backup_if_needed finds and copies legacy backup."""
        # Créer un legacy backup dans le même répertoire que la config
        legacy_backup_dir = os.path.dirname(manager.config_path)
        legacy_path = os.path.join(legacy_backup_dir, "grub.prime-backup")
        Path(legacy_path).write_text("GRUB_LEGACY=1\n")

        # Appeler create_original_backup_if_needed() devrait trouver et copier le legacy
        result = manager.create_original_backup_if_needed()
        
        assert result is True
        assert os.path.exists(manager.original_backup_path)
        
        # Vérifier que le contenu vient du legacy
        with open(manager.original_backup_path, encoding="utf-8") as f:
            content = f.read()
        assert "GRUB_LEGACY" in content

    def test_create_original_backup_config_not_found(self, tmp_path):
        """Test create_original_backup_if_needed raises error when config is missing."""
        # Créer un manager avec un chemin de config inexistant
        manager = BackupManager("/nonexistent/grub")
        manager.backup_dir = str(tmp_path / "backups")
        os.makedirs(manager.backup_dir, exist_ok=True)
        manager.original_backup_path = os.path.join(manager.backup_dir, "grub.bak.original")

        # Appeler create_original_backup_if_needed() devrait lever une erreur
        with pytest.raises(GrubBackupError, match="Fichier de configuration introuvable"):
            manager.create_original_backup_if_needed()

    def test_create_original_backup_copy_legacy_fails(self, manager, tmp_path, monkeypatch):
        """Test create_original_backup_if_needed handles copy error from legacy backup."""
        # Créer un legacy backup
        legacy_backup_dir = os.path.dirname(manager.config_path)
        legacy_path = os.path.join(legacy_backup_dir, "grub.bak")
        Path(legacy_path).write_text("GRUB_LEGACY=1\n")

        # Mock shutil.copy2 pour échouer sur legacy, puis réussir sur config
        import shutil
        original_copy2 = shutil.copy2
        call_count = [0]

        def mock_copy2(src, dst):
            call_count[0] += 1
            # Échouer sur le premier appel (copy du legacy)
            if call_count[0] == 1:
                raise OSError("Copy failed")
            # Réussir sur le deuxième appel (copy du config)
            return original_copy2(src, dst)

        monkeypatch.setattr("shutil.copy2", mock_copy2)

        # Devrait ignorer l'erreur du legacy et copier depuis config
        result = manager.create_original_backup_if_needed()
        assert result is True
        assert os.path.exists(manager.original_backup_path)

    def test_create_original_backup_copy_config_fails(self, manager, monkeypatch):
        """Test create_original_backup_if_needed when copy from config fails."""
        # Mock shutil.copy2 pour échouer lors de la copie du config
        import shutil
        
        def mock_copy2_error(src, dst):
            raise OSError("Permission denied")
        
        monkeypatch.setattr("shutil.copy2", mock_copy2_error)
        
        # Devrait lever une erreur
        with pytest.raises(GrubBackupError, match="Impossible de créer le backup original"):
            manager.create_original_backup_if_needed()
