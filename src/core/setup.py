"""Configuration d'initialisation du conteneur d'injection de dépendances."""

from src.core.backup_manager import BackupManager
from src.core.config.generator import GrubConfigGenerator
from src.core.config.loader import GrubConfigLoader
from src.core.config.parser import GrubMenuParser
from src.core.config.theme_generator import GrubThemeGenerator
from src.core.config.theme_manager import ThemeManager
from src.core.container import Container
from src.core.facade import GrubFacade
from src.core.services.grub_service import GrubService
from src.utils.logger import get_logger

logger = get_logger(__name__)


def setup_container() -> Container:
    """Configure et retourne le conteneur d'injection de dépendances.

    Enregistre tous les services et leurs dépendances dans le conteneur.
    Utilise le pattern singleton pour les services stateless.

    Returns:
        Container configuré et prêt à l'emploi

    """
    container = Container()

    # ===== Couche Configuration =====

    # ConfigLoader - Charge le fichier /etc/default/grub
    container.register_singleton("config_loader", GrubConfigLoader)

    # GrubConfigParser - Parse les entrées menu
    container.register_singleton("grub_parser", GrubMenuParser)

    # GrubConfigGenerator - Génère la configuration
    container.register_singleton("config_generator", GrubConfigGenerator)

    # ThemeGenerator - Génère les fichiers theme.txt
    container.register_singleton("theme_generator", GrubThemeGenerator)

    logger.info("Configuration layer enregistrée")

    # ===== Couche Métier =====

    # BackupManager - Gère les sauvegardes
    container.register_singleton("backup_manager", BackupManager)

    # GrubService - Service principal GRUB
    # Dépend implicitement de ConfigLoader et BackupManager
    container.register_singleton("grub_service", GrubService)

    # ThemeManager - Gère les modes de thème (standard/custom/modified)
    container.register_singleton("theme_manager", ThemeManager)

    logger.info("Business layer enregistrée")

    # ===== Couche API/Façade =====

    # GrubFacade - Interface simplifiée pour l'UI
    container.register_singleton("facade", GrubFacade)

    logger.info("Facade layer enregistrée")

    logger.info("Conteneur DI configuré avec %d services", len(container.get_registered_services()))

    return container


def initialize_application() -> Container:
    """Initialise l'application complète.

    Point d'entrée pour le démarrage de l'application.
    Effectue la configuration du conteneur et les validations.

    Returns:
        Container configuré et validé

    Raises:
        RuntimeError: Si l'initialisation échoue

    """
    try:
        logger.info("Démarrage de l'initialisation de l'application")

        # Configurer le conteneur
        container = setup_container()

        # Vérifier que tous les services critiques sont présents
        critical_services = ["facade", "theme_manager", "grub_service"]
        for service_name in critical_services:
            if not container.has(service_name):
                raise RuntimeError(f"Service critique manquant: {service_name}")

        logger.info("Application initialisée avec succès")
        return container

    except Exception as e:
        logger.exception("Erreur lors de l'initialisation: %s", e)
        raise RuntimeError(f"Impossible d'initialiser l'application: {e}") from e


# Conteneur global de l'application
_APPLICATION_CONTAINER: Container | None = None


def get_application_container() -> Container:
    """Obtenir le conteneur global de l'application.

    Initialise le conteneur si nécessaire.

    Returns:
        Le conteneur global de l'application

    """
    global _APPLICATION_CONTAINER  # pylint: disable=global-statement

    if _APPLICATION_CONTAINER is None:
        _APPLICATION_CONTAINER = initialize_application()

    return _APPLICATION_CONTAINER


def reset_application_container() -> None:
    """Réinitialiser le conteneur global (pour les tests)."""
    global _APPLICATION_CONTAINER  # pylint: disable=global-statement
    if _APPLICATION_CONTAINER is not None:
        _APPLICATION_CONTAINER.clear()
    _APPLICATION_CONTAINER = None
