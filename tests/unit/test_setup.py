"""Tests pour le module d'initialisation du conteneur DI."""

import pytest
from unittest.mock import patch, MagicMock

from src.core.setup import (
    setup_container,
    initialize_application,
    get_application_container,
    reset_application_container,
)


class TestSetupContainer:
    """Tests pour setup_container()."""

    def test_setup_container_returns_container(self):
        """setup_container retourne un objet Container."""
        container = setup_container()
        assert container is not None
        from src.core.container import Container
        assert isinstance(container, Container)

    def test_setup_container_registers_all_services(self):
        """setup_container enregistre tous les services requis."""
        container = setup_container()
        services = container.get_registered_services()
        
        expected_services = [
            'config_loader',
            'grub_parser',
            'config_generator',
            'backup_manager',
            'grub_service',
            'facade',
        ]
        
        for service in expected_services:
            assert service in services, f"Service {service} not registered"

    def test_setup_container_registers_singletons(self):
        """Tous les services sont enregistrés comme singletons."""
        container = setup_container()
        
        # Les services sont tous des singletons par construction
        # On vérifie juste qu'on peut les résoudre et qu'on récupère la même instance
        service_names = ['config_loader', 'grub_parser', 'config_generator']
        
        for service_name in service_names:
            instance1 = container.resolve(service_name)
            instance2 = container.resolve(service_name)
            assert instance1 is instance2, f"{service_name} is not a singleton"

    def test_setup_container_services_count(self):
        """setup_container enregistre exactement 6 services."""
        container = setup_container()
        services = container.get_registered_services()
        assert len(services) == 6

    def test_setup_container_resolves_facade(self):
        """Le conteneur peut résoudre la façade."""
        container = setup_container()
        facade = container.resolve('facade')
        assert facade is not None
        from src.core.facade import GrubFacade
        assert isinstance(facade, GrubFacade)

    def test_setup_container_facade_has_singleton_instance(self):
        """La façade est résolue comme le même singleton."""
        container = setup_container()
        facade1 = container.resolve('facade')
        facade2 = container.resolve('facade')
        assert facade1 is facade2


class TestInitializeApplication:
    """Tests pour initialize_application()."""

    def test_initialize_application_returns_container(self):
        """initialize_application retourne un Container."""
        reset_application_container()
        container = initialize_application()
        assert container is not None
        from src.core.container import Container
        assert isinstance(container, Container)

    def test_initialize_application_validates_critical_services(self):
        """initialize_application valide que les services critiques sont présents."""
        reset_application_container()
        container = initialize_application()
        
        critical_services = ['facade', 'grub_service']
        for service in critical_services:
            assert container.has(service), f"Critical service {service} not found"

    def test_initialize_application_raises_on_missing_service(self):
        """initialize_application lève RuntimeError si un service critique manque."""
        with patch('src.core.setup.setup_container') as mock_setup:
            mock_container = MagicMock()
            mock_container.has.return_value = False  # Simuler service manquant
            mock_setup.return_value = mock_container
            
            reset_application_container()
            with pytest.raises(RuntimeError, match="Service critique manquant"):
                initialize_application()

    def test_initialize_application_raises_on_setup_error(self):
        """initialize_application lève RuntimeError si setup_container échoue."""
        with patch('src.core.setup.setup_container', side_effect=Exception("Setup failed")):
            reset_application_container()
            with pytest.raises(RuntimeError, match="Impossible d'initialiser"):
                initialize_application()

    def test_initialize_application_logs_info(self):
        """initialize_application enregistre les messages d'info."""
        with patch('src.core.setup.logger') as mock_logger:
            reset_application_container()
            initialize_application()
            
            # Vérifier que les messages de log d'info ont été appelés
            assert mock_logger.info.called
            calls = [str(call) for call in mock_logger.info.call_args_list]
            assert any("Démarrage" in str(call) for call in calls)


class TestApplicationContainerGlobal:
    """Tests pour get_application_container() et reset_application_container()."""

    def test_get_application_container_initializes_once(self):
        """get_application_container initialise le conteneur une seule fois."""
        reset_application_container()
        
        container1 = get_application_container()
        container2 = get_application_container()
        
        # Doit être le même instance
        assert container1 is container2

    def test_get_application_container_returns_initialized_container(self):
        """get_application_container retourne un conteneur initialisé."""
        reset_application_container()
        container = get_application_container()
        
        # Vérifier que le conteneur a les services
        assert container.has('facade')
        assert container.has('grub_service')

    def test_reset_application_container_clears_state(self):
        """reset_application_container réinitialise le conteneur global."""
        # Obtenir un conteneur initialisé
        container1 = get_application_container()
        assert container1 is not None
        
        # Réinitialiser
        reset_application_container()
        
        # Obtenir un nouveau conteneur
        container2 = get_application_container()
        
        # Doit être une instance différente
        assert container1 is not container2

    def test_reset_application_container_idempotent(self):
        """reset_application_container peut être appelé plusieurs fois."""
        reset_application_container()
        reset_application_container()
        reset_application_container()
        
        # Doit fonctionner sans erreur
        container = get_application_container()
        assert container is not None

    def test_application_container_services_available(self):
        """Le conteneur global fournit tous les services nécessaires."""
        reset_application_container()
        container = get_application_container()
        
        services = container.get_registered_services()
        expected = [
            'config_loader',
            'grub_parser',
            'config_generator',
            'backup_manager',
            'grub_service',
            'facade',
        ]
        
        for service in expected:
            assert service in services
