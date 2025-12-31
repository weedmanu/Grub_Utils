# Changelog

Tous les changements notables apportés à GRUB Manager seront documentés dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
et ce projet respecte [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-31

### Ajouté

- **Sécurité renforcée** : Élimination complète des injections de commandes shell
- **Validation stricte** : Validation de toutes les entrées utilisateur (timeout, résolution, chemins de fichiers, paramètres noyau)
- **Système de logging professionnel** : Logging rotatif avec niveaux appropriés et séparation root/utilisateur
- **Gestion d'erreurs complète** : Hiérarchie d'exceptions personnalisées et gestion robuste des erreurs
- **Backups améliorés** : Sauvegardes horodatées avec limite automatique et vérification d'intégrité
- **Architecture modulaire** : Refactorisation en modules séparés (core, ui, utils)
- **Interface utilisateur améliorée** : Toasts, tooltips, confirmations, dialogs d'erreur détaillés
- **Tests unitaires** : Couverture de 89% pour le validator avec tests complets
- **Documentation complète** : README, docstrings Google style, architecture documentée
- **Type hints** : Annotations de type complètes sur tout le code
- **Pattern Observer** : Utilisation de GObject signals pour la découplage UI/logique
- **Configuration centralisée** : Constantes et configuration dans un module dédié

### Changé

- **Refactorisation complète** : Passage d'un script monolithique à une application professionnelle
- **Exécution sécurisée** : Remplacement des `sh -c` par des scripts temporaires sécurisés
- **Gestion des permissions** : Utilisation exclusive de `pkexec` sans fallback sudo
- **Interface GTK4** : Modernisation avec libadwaita et meilleures pratiques GTK4

### Corrigé

- **Vulnérabilités de sécurité** : Injection de commandes, path traversal, validation insuffisante
- **Gestion d'erreurs** : Plus d'exceptions non gérées crashant l'application
- **Permissions** : Gestion propre des cas où pkexec est annulé
- **Backups** : Problèmes de restauration et de nettoyage des anciennes sauvegardes

### Sécurité

- **Validation d'entrée** : Timeout 0-300s, résolution NNNNxNNNN ou auto, extensions de fichiers whitelistées
- **Échappement sécurisé** : Utilisation de scripts temporaires au lieu de concaténation de commandes
- **Audit logging** : Trace complète de toutes les opérations système et actions utilisateur
- **Permissions minimales** : Exécution avec les droits root uniquement quand nécessaire

### Technique

- **Python 3.10+** : Support des dernières fonctionnalités de langage
- **GTK4 obligatoire** : Interface moderne et maintenue
- **Compatibilité multi-distribution** : Ubuntu, Fedora, Arch Linux
- **Dépendances minimales** : Réduction des dépendances externes
- **Performance** : Chargement < 2s, opérations UI < 100ms

### Tests

- **Couverture 89%** pour le module validator
- **Tests unitaires** pour tous les cas limites de validation
- **Tests d'intégration** pour les opérations système simulées
- **CI/CD ready** : Configuration pytest et outils de qualité

## [0.1.0] - 2025-01-01

### Ajouté

- Version initiale basée sur Grub Customizer Python
- Interface GTK basique pour configuration GRUB
- Support des paramètres principaux (timeout, default entry, kernel params)
- Gestion des apparences (résolution, background, thème)
- Menu de gestion des entrées cachées
- Sauvegarde/restauration basique

### Connu

- Vulnérabilités de sécurité (injection shell)
- Gestion d'erreurs insuffisante
- Pas de validation d'entrée
- Code monolithique
- Pas de tests
- Interface rudimentaire
