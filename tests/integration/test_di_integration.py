"""Tests d'intégration - vérifient l'interaction entre composants."""

import unittest
from unittest.mock import MagicMock

from src.core.container import Container
from src.core.dtos import OperationResultDTO


class TestContainerIntegration(unittest.TestCase):
    """Tests d'intégration du DI Container."""

    def setUp(self):
        """Préparer l'environnement pour chaque test."""
        self.container = Container()
        self._setup_mocks()

    def _setup_mocks(self):
        """Créer les mocks nécessaires."""
        self.mock_loader = MagicMock(name="ConfigLoader")
        self.mock_backup_mgr = MagicMock(name="BackupManager")

    def test_di_container_provides_all_services(self):
        """Vérifier que le conteneur fournit tous les services."""
        self.container.register_singleton("config_loader", self.mock_loader)
        self.container.register_singleton("backup_manager", self.mock_backup_mgr)

        # Résoudre tous les services
        loader = self.container.resolve("config_loader")
        backup_mgr = self.container.resolve("backup_manager")

        self.assertIsNotNone(loader)
        self.assertIsNotNone(backup_mgr)

    def test_multiple_operations_with_shared_container_state(self):
        """Tester plusieurs opérations avec état partagé du conteneur."""
        call_count = {"count": 0}

        def create_service():
            call_count["count"] += 1
            svc = MagicMock()
            svc.call_count = call_count["count"]
            return svc

        # Transient service - doit créer une nouvelle instance à chaque fois
        self.container.register("transient_service", create_service)

        svc1 = self.container.resolve("transient_service")
        svc2 = self.container.resolve("transient_service")

        self.assertEqual(svc1.call_count, 1)
        self.assertEqual(svc2.call_count, 2)
        self.assertIsNot(svc1, svc2)


class TestFacadeWithDIContainer(unittest.TestCase):
    """Tests de la Façade en combinaison avec le DI Container."""

    def setUp(self):
        """Préparer l'environnement pour chaque test."""
        self.container = Container()

    def test_facade_configured_in_container(self):
        """Tester que la façade est correctement configurée dans le conteneur."""
        mock_service = MagicMock()
        mock_service.backup_manager = MagicMock()

        # Enregistrer la façade
        self.container.register_singleton("grub_service", lambda: mock_service)

        resolved_service = self.container.resolve("grub_service")

        self.assertIs(resolved_service, mock_service)
        self.assertIsNotNone(resolved_service.backup_manager)

    def test_facade_load_configuration_via_container(self):
        """Tester le chargement de configuration via le conteneur."""
        mock_service = MagicMock()
        mock_service.load.return_value = OperationResultDTO(success=True, message="Config loaded")

        self.container.register_singleton("grub_service", lambda: mock_service)

        service = self.container.resolve("grub_service")
        result = service.load()

        self.assertTrue(result.success)
        self.assertIn("loaded", result.message.lower())


class TestBackupIntegration(unittest.TestCase):
    """Tests d'intégration du système de backup."""

    def setUp(self):
        """Préparer l'environnement pour chaque test."""
        self.container = Container()

    def test_backup_manager_initialization(self):
        """Tester l'initialisation du backup manager."""
        mock_backup_mgr = MagicMock()
        mock_backup_mgr.list_backups.return_value = ["/var/backups/grub.1.bak", "/var/backups/grub.2.bak"]

        self.container.register_singleton("backup_manager", lambda: mock_backup_mgr)

        mgr = self.container.resolve("backup_manager")
        backups = mgr.list_backups()

        self.assertEqual(len(backups), 2)

    def test_backup_restoration_workflow(self):
        """Tester le workflow de restauration de backup."""
        mock_backup_mgr = MagicMock()
        mock_backup_mgr.restore.return_value = OperationResultDTO(success=True, message="Backup restored")

        self.container.register_singleton("backup_manager", lambda: mock_backup_mgr)

        mgr = self.container.resolve("backup_manager")
        result = mgr.restore("/var/backups/grub.1.bak")

        self.assertTrue(result.success)
        mock_backup_mgr.restore.assert_called_once_with("/var/backups/grub.1.bak")


class TestContainerStartupSequence(unittest.TestCase):
    """Tests de la séquence de démarrage avec le conteneur."""

    def test_full_application_startup(self):
        """Tester la séquence complète de démarrage."""
        container = Container()

        # Simuler l'initialisation
        mocks = {
            "backup_manager": MagicMock(name="BackupManager"),
            "grub_service": MagicMock(name="GrubService"),
            "facade": MagicMock(name="Facade"),
        }

        for name, mock in mocks.items():
            container.register_singleton(name, lambda m=mock: m)

        # Vérifier que tout est enregistré
        for name in mocks:
            self.assertTrue(container.has(name))
            resolved = container.resolve(name)
            self.assertIs(resolved, mocks[name])

    def test_service_availability_after_startup(self):
        """Tester la disponibilité des services après le démarrage."""
        container = Container()

        services = {
            "config_loader": MagicMock(),
            "parser": MagicMock(),
            "generator": MagicMock(),
        }

        for name, service in services.items():
            container.register_singleton(name, lambda s=service: s)

        # Vérifier que chaque service est disponible
        for name, expected in services.items():
            resolved = container.resolve(name)
            self.assertIs(resolved, expected)


class TestContainerWithGTKIntegration(unittest.TestCase):
    """Tests d'intégration avec les composants GTK."""

    def setUp(self):
        """Préparer l'environnement pour chaque test."""
        self.container = Container()

    def test_gtk_application_can_access_facade(self):
        """Tester que l'app GTK peut accéder à la façade."""
        mock_facade = MagicMock()
        mock_facade.load_configuration.return_value = OperationResultDTO(success=True, message="Config loaded")

        self.container.register_singleton("facade", lambda: mock_facade)

        # Simuler l'accès depuis GTK
        facade = self.container.resolve("facade")
        result = facade.load_configuration()

        self.assertTrue(result.success)

    def test_multiple_tabs_share_container_state(self):
        """Tester que plusieurs onglets partagent l'état du conteneur."""
        mock_facade = MagicMock()
        call_history = []

        def log_call(op):
            call_history.append(op)
            return OperationResultDTO(success=True, message="Operation applied")

        mock_facade.apply_changes = log_call

        self.container.register_singleton("facade", lambda: mock_facade)

        # Simuler deux onglets qui utilisent la même façade
        facade1 = self.container.resolve("facade")
        facade2 = self.container.resolve("facade")

        facade1.apply_changes("operation_1")
        facade2.apply_changes("operation_2")

        # Vérifier que c'est la même instance
        self.assertIs(facade1, facade2)
        self.assertEqual(len(call_history), 2)


if __name__ == "__main__":
    unittest.main()
