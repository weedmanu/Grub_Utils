# Prompt de Refactorisation Professionnelle - GRUB Manager

## Contexte

Tu es un développeur Python senior spécialisé en applications GTK4/libadwaita et systèmes Linux. Tu dois refactoriser une application de gestion GRUB existante pour la rendre production-ready.

## Objectif

Transformer le code actuel en une application professionnelle, sécurisée et maintenable en suivant les meilleures pratiques de développement Python et les standards de sécurité Linux.

## Code Source à Refactoriser

[Fournir les fichiers : main.py, grub_manager.py, app.py, et les fichiers des tabs]

## Tâches Prioritaires

### 🔴 CRITIQUE - Sécurité (À faire EN PREMIER)

1. **Éliminer les injections de commandes shell**

   - Remplacer tous les `["pkexec", "sh", "-c", " && ".join(...)]`
   - Utiliser des commandes individuelles ou des scripts temporaires sécurisés
   - Échapper/valider TOUTES les entrées utilisateur avant utilisation
   - Utiliser `shlex.quote()` pour les chemins de fichiers

2. **Validation stricte des entrées**

   - Créer une classe `GrubValidator` avec méthodes statiques
   - Valider :
     - Timeout : 0-300 secondes, entier uniquement
     - Résolution : format "NNNNxNNNN" ou "auto"
     - Chemins de fichiers : existence, extensions autorisées (.png, .jpg, .jpeg, .tga)
     - Paramètres kernel : whitelist des options courantes
   - Rejeter toute entrée invalide AVANT de toucher aux fichiers système

3. **Gestion robuste des permissions**
   - Vérifier les permissions AVANT d'essayer les opérations
   - Gérer proprement les cas où pkexec est annulé
   - Ajouter des timeouts aux opérations privilégiées

### 🟠 HAUTE PRIORITÉ - Fiabilité

4. **Système de logging professionnel**

   ```python
   # Structure attendue
   - Logger rotatif avec rotation par taille
   - Niveaux : DEBUG, INFO, WARNING, ERROR, CRITICAL
   - Format : timestamp + niveau + module + message
   - Fichiers : /var/log/grub-manager.log (si root) ou ~/.local/share/grub-manager/app.log
   - Logger toutes les opérations système, erreurs, et actions utilisateur
   ```

5. **Gestion d'erreurs complète**

   - Créer une hiérarchie d'exceptions personnalisées :
     - `GrubError` (base)
     - `GrubPermissionError`
     - `GrubConfigError`
     - `GrubValidationError`
     - `GrubBackupError`
   - Try-catch sur TOUTES les opérations I/O et subprocess
   - Messages d'erreur clairs et actionnables pour l'utilisateur
   - Ne JAMAIS laisser une exception crash l'application

6. **Gestion des backups améliorée**
   - Backups horodatés (pas juste .bak)
   - Limite du nombre de backups (garder les 5 derniers)
   - Vérification d'intégrité des backups
   - Restauration sélective avec aperçu des différences

### 🟡 MOYENNE PRIORITÉ - Architecture

7. **Refactoriser en modules séparés**

   ```
   src/
   ├── core/
   │   ├── grub_manager.py      # Logique métier principale
   │   ├── validator.py          # Validation des données
   │   ├── backup_manager.py     # Gestion des sauvegardes
   │   ├── command_executor.py   # Exécution sécurisée des commandes
   │   └── parser.py             # Parsing grub.cfg
   ├── ui/
   │   ├── app.py
   │   ├── dialogs/
   │   │   ├── error_dialog.py   # Dialogs d'erreur avec détails
   │   │   ├── confirm_dialog.py # Confirmations
   │   │   └── diff_dialog.py    # Aperçu des changements
   │   └── tabs/
   ├── utils/
   │   ├── logger.py             # Configuration logging
   │   ├── config.py             # Constantes et configuration
   │   └── signals.py            # GObject signals
   └── tests/                     # Tests unitaires
   ```

8. **Pattern Observer pour les mises à jour**

   - Utiliser GObject.signals pour notifier les changements
   - Découpler la logique métier de l'UI
   - Permettre plusieurs écouteurs (pour futures fonctionnalités)

9. **Configuration centralisée**
   - Créer config.py avec TOUTES les constantes
   - Chemins, commandes, timeouts, limites
   - Support multi-distribution (Ubuntu, Fedora, Arch, etc.)

### 🟢 AMÉLIORATIONS UX

10. **Feedback utilisateur amélioré**

    - Toast notifications pour succès (auto-dismiss 3s)
    - Dialogs détaillés pour erreurs avec bouton "Détails techniques"
    - Barre de progression lors de l'application des changements
    - Indicateurs de chargement sur toutes les opérations longues

11. **Confirmations des actions critiques**

    - Dialog de confirmation avant save_and_apply()
    - Aperçu des changements (diff) avant application
    - Option "Ne plus demander" avec checkbox (sauf actions destructrices)

12. **Tooltips et aide contextuelle**
    - Tooltips informatifs sur TOUS les widgets
    - Lien vers documentation dans l'aide
    - Messages d'erreur avec suggestions de résolution

### 🔵 QUALITÉ DU CODE

13. **Tests unitaires**

    - Couverture minimale : 70% du code core/
    - Tests pour :
      - Validation des entrées (tous les cas limites)
      - Parsing de grub.cfg (différents formats)
      - Logique de backup/restore
      - Gestion d'erreurs
    - Utiliser unittest.mock pour les opérations système

14. **Documentation complète**

    - Docstrings Google style pour TOUTES les fonctions/classes
    - README avec :
      - Installation
      - Utilisation
      - Architecture
      - Contribution
    - Commentaires inline pour la logique complexe uniquement

15. **Type hints**
    - Annotations de type pour tous les paramètres et retours
    - Utiliser `Optional`, `Union`, `List`, `Dict` de typing
    - Vérification avec mypy (niveau strict)

### ⚡ FONCTIONNALITÉS BONUS (si temps)

16. **Mode dry-run**

    - Aperçu des commandes qui seront exécutées
    - Simulation sans modification réelle

17. **Profils de configuration**

    - Sauvegarder/charger des configurations nommées
    - Profils prédéfinis (Gaming, Performance, Serveur)

18. **Détection automatique**
    - Proposer résolution optimale selon l'écran
    - Détecter si NVIDIA et suggérer nomodeset si nécessaire

## Contraintes Techniques

- **Python** : 3.10+ minimum
- **GTK** : GTK4 obligatoire, libadwaita si disponible
- **Compatibilité** : Ubuntu 22.04+, Fedora 36+, Arch Linux
- **Permissions** : Utiliser pkexec, ne JAMAIS demander sudo dans le terminal
- **Dépendances** : Minimiser les dépendances externes
- **Performance** : Chargement < 2s, opérations UI < 100ms

## Standards de Code

```python
# Style
- PEP 8 strict (formatter: black)
- Ligne max: 100 caractères
- Imports : stdlib > tiers > locaux

# Nommage
- Classes: PascalCase
- Fonctions/variables: snake_case
- Constantes: UPPER_SNAKE_CASE
- Privé: _underscore_prefix

# Commentaires
- Docstrings : format Google
- Commentaires inline : seulement pour logique complexe
- TODO avec ticket/issue reference

# Git
- Commits atomiques avec messages descriptifs
- Messages format: "type(scope): description"
  - feat, fix, refactor, docs, test, chore
```

## Livrables Attendus

1. **Code refactorisé** avec structure modulaire
2. **Tests unitaires** avec rapport de couverture
3. **Documentation** :
   - README.md complet
   - CONTRIBUTING.md
   - CHANGELOG.md
   - Docstrings sur tout le code
4. **Fichiers de configuration** :
   - requirements.txt
   - setup.py ou pyproject.toml
   - .gitignore
   - .pylintrc ou pyproject.toml (config pylint)

## Exemple de Code Attendu

### Avant (code actuel - MAUVAIS)

```python
cmd = ["pkexec", "sh", "-c", " && ".join(full_script)]
result = subprocess.run(cmd, capture_output=True, text=True, check=False)
if result.returncode != 0:
    print(f"Erreur: {result.stderr}")
    return False
```

### Après (code attendu - BON)

```python
from src.core.command_executor import SecureCommandExecutor
from src.core.validator import GrubValidator
from src.utils.logger import get_logger

logger = get_logger(__name__)

def save_and_apply(self) -> tuple[bool, str]:
    """
    Sauvegarde la configuration et met à jour GRUB.

    Returns:
        tuple[bool, str]: (succès, message d'erreur si échec)

    Raises:
        GrubValidationError: Si la configuration est invalide
        GrubPermissionError: Si pkexec est annulé
    """
    try:
        # Validation AVANT toute modification
        validator = GrubValidator()
        validator.validate_all(self.entries)

        # Backup sécurisé
        backup_manager = BackupManager()
        backup_path = backup_manager.create_backup(self.config_path)
        logger.info(f"Backup créé: {backup_path}")

        # Préparation commandes sécurisées
        executor = SecureCommandExecutor()
        commands = self._prepare_secure_commands()

        # Exécution avec gestion d'erreur
        success, output = executor.execute_with_pkexec(commands)

        if success:
            logger.info("Configuration GRUB appliquée avec succès")
            self.emit('config-changed')
            return True, ""
        else:
            logger.error(f"Échec application GRUB: {output}")
            return False, "Échec de l'application. Voir les logs pour détails."

    except GrubValidationError as e:
        logger.warning(f"Validation échouée: {e}")
        return False, f"Configuration invalide: {e}"
    except GrubPermissionError:
        logger.info("Opération annulée par l'utilisateur")
        return False, "Authentification annulée"
    except Exception as e:
        logger.exception("Erreur inattendue lors de save_and_apply")
        return False, f"Erreur inattendue: {e}"
```

## Processus de Développement

1. **Phase 1 - Sécurité** (Jour 1)

   - Corriger injections shell
   - Ajouter validation
   - Sécuriser command execution

2. **Phase 2 - Fiabilité** (Jour 2)

   - Implémenter logging
   - Gestion d'erreurs complète
   - Améliorer backups

3. **Phase 3 - Architecture** (Jour 3)

   - Refactoriser en modules
   - Implémenter signals
   - Centraliser configuration

4. **Phase 4 - UX** (Jour 4)

   - Améliorer feedback
   - Ajouter confirmations
   - Tooltips et aide

5. **Phase 5 - Qualité** (Jour 5)
   - Écrire tests
   - Documentation
   - Type hints

## Critères de Succès

✅ Aucune vulnérabilité de sécurité (injection, path traversal, etc.)
✅ Toutes les entrées utilisateur validées
✅ Logging complet de toutes les opérations
✅ Gestion d'erreur sans crash
✅ Tests unitaires avec couverture > 70%
✅ Documentation complète
✅ Type hints sur tout le code
✅ Code conforme PEP 8
✅ Interface utilisateur réactive et informative
✅ Compatible Ubuntu, Fedora, Arch

## Questions à Poser Si Besoin

- Dois-je supporter d'autres distributions (Debian, openSUSE) ?
- Faut-il une interface en ligne de commande en plus du GUI ?
- Quel niveau de verbosité pour les logs (debug par défaut ou info) ?
- Faut-il supporter UEFI spécifiquement ?
- Internationalisation (i18n) requise ?

## Commencer Par

Analyse d'abord TOUS les fichiers fournis, identifie les problèmes de sécurité critiques, puis commence par le module `command_executor.py` pour sécuriser l'exécution des commandes. Procède ensuite méthodiquement selon les phases définies.

**Important** : Commente ton code de manière pédagogique pour que je comprenne les changements et les raisons derrière chaque décision architecturale.
