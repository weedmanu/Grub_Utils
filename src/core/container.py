"""Conteneur d'injection de dépendances légèrement couplé."""

from collections.abc import Callable
from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ContainerError(Exception):
    """Erreur liée au conteneur d'injection."""


class Container:
    """Conteneur simple et efficace pour l'injection de dépendances.

    Supporte les patterns singleton et transient avec résolution lazy.

    Utilisation:
        container = Container()
        container.register_singleton('service', MyService)
        service = container.resolve('service')
    """

    def __init__(self) -> None:
        """Initialise le conteneur vide."""
        self._services: dict[str, dict[str, Any]] = {}
        self._singletons: dict[str, Any] = {}
        self._resolving: set = set()  # Pour détection de cycles

    def register_singleton(self, name: str, factory: Callable) -> None:
        """Enregistrer un service singleton.

        Args:
            name: Identifiant unique du service
            factory: Fonction/classe créant le service

        Raises:
            ContainerError: Si le service est déjà enregistré
            ValueError: Si factory est None

        """
        if factory is None:
            raise ValueError(f"Factory ne peut pas être None pour '{name}'")

        if name in self._services:
            raise ContainerError(f"Le service '{name}' est déjà enregistré. Utilisez .replace() pour le remplacer.")

        self._services[name] = {"factory": factory, "is_singleton": True}
        logger.debug("Service singleton enregistré: %s", name)

    def register(self, name: str, factory: Callable) -> None:
        """Enregistrer un service transient.

        Une nouvelle instance est créée à chaque résolution.

        Args:
            name: Identifiant unique du service
            factory: Fonction/classe créant le service

        Raises:
            ContainerError: Si le service est déjà enregistré

        """
        if factory is None:
            raise ValueError(f"Factory ne peut pas être None pour '{name}'")

        if name in self._services:
            raise ContainerError(f"Le service '{name}' est déjà enregistré. Utilisez .replace() pour le remplacer.")

        self._services[name] = {"factory": factory, "is_singleton": False}
        logger.debug("Service transient enregistré: %s", name)

    def resolve(self, name: str) -> Any:
        """Résoudre et retourner une instance du service.

        Args:
            name: Identifiant du service à résoudre

        Returns:
            Instance du service

        Raises:
            ContainerError: Si le service n'existe pas
            RecursionError: Si dépendances circulaires détectées

        """
        if name not in self._services:
            raise ContainerError(
                f"Le service '{name}' n'existe pas. " f"Services disponibles: {list(self._services.keys())}"
            )

        # Détection des cycles
        if name in self._resolving:
            raise ContainerError(f"Dépendance circulaire détectée lors de la résolution de '{name}'")

        service_info = self._services[name]

        # Retourner le singleton en cache s'il existe
        if service_info["is_singleton"] and name in self._singletons:
            logger.debug("Service singleton résolu depuis le cache: %s", name)
            return self._singletons[name]

        # Créer l'instance
        try:
            self._resolving.add(name)

            factory = service_info["factory"]

            # Si c'est une classe, l'instancier
            if isinstance(factory, type):
                instance = factory()
            # Sinon, l'appeler comme fonction
            else:
                instance = factory()

            # Cacher le singleton
            if service_info["is_singleton"]:
                self._singletons[name] = instance
                logger.debug("Service singleton créé et mis en cache: %s", name)
            else:
                logger.debug("Service transient créé: %s", name)

            return instance

        except Exception as e:
            logger.error("Erreur lors de la résolution de '%s': %s", name, e)
            raise
        finally:
            self._resolving.discard(name)

    def has(self, name: str) -> bool:
        """Vérifier si un service est enregistré.

        Args:
            name: Identifiant du service

        Returns:
            True si le service existe, False sinon

        """
        return name in self._services

    def get_registered_services(self) -> list[str]:
        """Lister tous les services enregistrés.

        Returns:
            Liste des identifiants des services

        """
        return list(self._services.keys())

    def clear(self) -> None:
        """Effacer tous les services et singletons en cache.

        Utile pour les tests ou réinitialisation.
        """
        self._services.clear()
        self._singletons.clear()
        self._resolving.clear()
        logger.info("Conteneur vidé")

    def replace(self, name: str, factory: Callable, is_singleton: bool = True) -> None:
        """Remplacer un service existant.

        Args:
            name: Identifiant du service
            factory: Nouvelle fonction/classe factory
            is_singleton: Si True, créer un singleton

        """
        if name in self._singletons:
            del self._singletons[name]

        if name in self._services:
            del self._services[name]

        if is_singleton:
            self.register_singleton(name, factory)
        else:
            self.register(name, factory)

        logger.debug("Service remplacé: %s", name)

    def __repr__(self) -> str:
        """Représentation textuelle du conteneur."""
        services_str = ", ".join(self._services.keys())
        return f"<Container(services=[{services_str}])>"


# Instance globale du conteneur (optionnel)
_GLOBAL_CONTAINER: Container | None = None


def get_container() -> Container:
    """Obtenir l'instance globale du conteneur.

    Returns:
        Le conteneur global

    """
    global _GLOBAL_CONTAINER  # pylint: disable=global-statement
    if _GLOBAL_CONTAINER is None:
        _GLOBAL_CONTAINER = Container()
    return _GLOBAL_CONTAINER


def reset_container() -> None:
    """Réinitialiser le conteneur global (pour les tests)."""
    global _GLOBAL_CONTAINER  # pylint: disable=global-statement
    _GLOBAL_CONTAINER = None
