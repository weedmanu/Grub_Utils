# Structure du Projet GRUB Manager

## Vue d'ensemble

Ce projet est une application GTK4 pour gérer la configuration GRUB de manière graphique et sécurisée. Il suit une architecture SOLID avec séparation claire des responsabilités.

## 🏆 Qualité de Code - Standards Internationaux AAA

### Standards Python (PEP 8 + Best Practices)

- **Type Hints**: Utilisation systématique pour la documentation et la validation
- **Docstrings**: Documentation complète de toutes les classes et méthodes publiques
- **Dataclasses**: Utilisation de `@dataclass` pour les objets de données (DTOs, ThemeConfiguration)
- **Immutabilité**: DTOs immutables (`frozen=True`) pour garantir la cohérence
- **Logging structuré**: Configuration centralisée dans `utils/logger.py`
- **Gestion d'erreurs**: Hiérarchie d'exceptions spécialisées dans `core/exceptions.py`

### Qualité de Code Vérifiée

- **Vulture**: 0 code mort détecté (seuil 65%)
- **Pylint**: Score 9.57/10 avec règles strictes
- **Pylint similarities**: 10/10 (aucune duplication de code)
- **Tests**: Couverture complète (unit/integration/e2e)

### Conformité Standards Linux/GRUB

- **GRUB2 Official Specification**: Génération de `theme.txt` conforme au format gfxmenu officiel
- **GNU GRUB Manual**: Respect des paramètres standards de `/etc/default/grub`
- **Séparation stricte**: Paramètres GRUB standards vs paramètres visuels personnalisés
- **Sécurité système**: Élévation de privilèges via `pkexec`, validation anti-injection
- **Backups automatiques**: Protection contre les corruptions de configuration

### Centralisation et Réutilisabilité

**Constantes et Configuration** (`utils/config.py`):

- `GRUB_COLOR_TO_HEX`: Mapping unique des couleurs GRUB → hexadécimal
- `ALLOWED_GRUB_COLOR_NAMES`: Ensemble unique de couleurs valides (frozenset)
- `GRUB_RESOLUTIONS`, `GRUB_COLORS`: Listes centralisées de valeurs autorisées
- `parse_grub_color_pair(color_string)`: Parsing unique "fg/bg" réutilisé partout

**Composants UI Partagés** (`ui/tabs/base.py`):

- `BaseTab.create_info_box()`: Méthode statique pour créer des info boxes standardisées
- Configuration des marges et espacements cohérente via constantes

**Validation Centralisée** (`core/validator.py`):

- `GrubValidator`: Classe unique de validation utilisant `ALLOWED_GRUB_COLOR_NAMES`
- Règles de validation partagées par tout le projet

**Conversion Couleurs** (`utils/config.py`):

- `grub_color_to_hex(color_name)`: Fonction unique de conversion GRUB → hex
- Utilisée par `theme_generator.py`, `preview_dialog.py`, etc.

### Architecture Exemplaire

- **Séparation des responsabilités**: Core (logique) / UI (interface) / Utils (transversal)
- **Façade Pattern**: API simplifiée pour découpler UI et implémentation
- **DTO Pattern**: Transfert de données immuable entre couches
- **DRY Principle**: Aucune duplication de code, tout est factorisé
- **Single Source of Truth**: Chaque donnée a une source unique et centralisée

## Arborescence

```
main.py                                    # Point d'entrée principal de l'application GTK
script/
├── migrate_theme_config.py                # Script de migration vers theme_config.json
└── preview_ui.py                          # Aperçu de l'interface utilisateur
src/
├── __init__.py                            # Marqueur de package Python
├── core/                                  # Logique métier centrale (architecture SOLID)
│   ├── __init__.py                        # Marqueur de package Python
│   ├── backup_manager.py                  # Gestion des sauvegardes automatiques
│   ├── command_executor.py                # Exécution sécurisée des commandes système
│   ├── config/                            # Modules de traitement de la configuration GRUB
│   │   ├── __init__.py                    # Marqueur de package Python
│   │   ├── generator.py                   # Génération du contenu de configuration
│   │   ├── loader.py                      # Chargement du fichier /etc/default/grub
│   │   ├── parser.py                      # Parsing du fichier grub.cfg pour les entrées menu
│   │   ├── theme_config.py                # Gestion de theme_config.json (ThemeConfiguration dataclass)
│   │   ├── theme_generator.py             # Génération du fichier theme.txt GRUB
│   │   └── theme_manager.py               # Gestion des modes de thème (standard/custom/modifié)
│   ├── container.py                       # Modèles/objets cœur (conteneurs)
│   ├── dtos.py                            # Objets de transfert de données (Résultats, Backups)
│   ├── exceptions.py                      # Hiérarchie d'exceptions métier spécialisées
│   ├── facade.py                          # Façade simplifiant l'API pour l'interface utilisateur
│   ├── security.py                        # Validation d'entrées et prévention des injections
│   ├── services/                          # Services métier orchestrateurs
│   │   ├── __init__.py                    # Marqueur de package Python
│   │   └── grub_service.py                # Service principal GRUB (load/save/apply/backup)
│   ├── setup.py                           # Configuration/initialisation (core)
│   └── validator.py                       # Validation des paramètres de configuration
├── ui/                                    # Interface utilisateur GTK4
│   ├── __init__.py                        # Marqueur de package Python
│   ├── app.py                             # Application principale GTK avec logique UI
│   ├── dialogs/                           # Boîtes de dialogue spécialisées
│   │   ├── __init__.py                    # Marqueur de package Python
│   │   ├── backup_selector_dialog.py      # Sélectionneur de sauvegarde
│   │   ├── base_dialog.py                 # Classe de base pour les dialogues
│   │   ├── confirm_dialog.py              # Dialogue de confirmation générique
│   │   ├── error_dialog.py                # Affichage des erreurs utilisateur
│   │   ├── preview_dialog.py              # Aperçu avant application des changements
│   │   └── text_view_utils.py             # Utilitaires pour les vues texte
│   ├── enums.py                           # Énumérations pour l'UI (ActionType)
│   ├── gtk_init.py                        # Initialisation GTK avec fallback Adwaita
│   └── tabs/                              # Onglets de l'interface utilisateur
│       ├── __init__.py                    # Marqueur de package Python
│       ├── appearance/                    # Onglet configuration apparence (package, SOLID)
│       │   ├── __init__.py                # API publique + re-exports (compat tests)
│       │   ├── tab.py                     # Implémentation de AppearanceTab
│       │   ├── theme.py                   # Parsing theme.txt + conversions couleur
│       │   └── widgets.py                 # Factories de widgets (dropdowns)
│       ├── backup.py                      # Onglet gestion des sauvegardes
│       ├── base.py                        # Classe de base pour les onglets
│       ├── general.py                     # Onglet paramètres généraux (timeout, default entry)
│       └── menu.py                        # Onglet gestion des entrées de menu
└── utils/                                 # Utilitaires transversaux
    ├── __init__.py                        # Marqueur de package Python
    ├── config.py                          # Constantes de configuration globales
    └── logger.py                          # Configuration centralisée du logging
tests/                                     # Tests unitaires et d'intégration
├── conftest.py                            # Configuration pytest
├── e2e/                                   # Tests end-to-end
├── integration/                           # Tests d'intégration
└── unit/                                  # Tests unitaires
```

## Système de Configuration

### Configuration GRUB Standard (`/etc/default/grub`)

Contient **uniquement** les paramètres standards reconnus par GRUB :

- `GRUB_TIMEOUT`, `GRUB_DEFAULT`, `GRUB_SAVEDEFAULT`
- `GRUB_GFXMODE` (résolution graphique)
- `GRUB_TERMINAL_OUTPUT` (console/gfxterm)
- `GRUB_THEME` (chemin vers theme.txt, généré automatiquement)
- `GRUB_CMDLINE_LINUX`, `GRUB_DISABLE_RECOVERY`, etc.

### Configuration Thème Personnalisé (`/boot/grub/themes/custom/theme_config.json`)

Contient **tous** les paramètres visuels du thème GRUB (non reconnus nativement par `/etc/default/grub`) :

- Positionnement menu (left, top, width, height)
- Dimensions items (height, spacing, padding)
- Couleurs (normal_fg, normal_bg, highlight_fg, highlight_bg)
- Textes (title, label, positions)
- Barre de progression (position, dimensions, couleurs)
- Polices (unicode + tailles)
- Activation du thème (enabled: true/false)

**Format** : JSON structuré via dataclass `ThemeConfiguration`  
**Avantages** :

- Séparation propre entre config GRUB standard et paramètres visuels
- Pas de pollution de `/etc/default/grub` avec des paramètres non-standard
- Format lisible et facilement éditable
- Migration automatique depuis l'ancien système via `script/migrate_theme_config.py`

### Fichier Thème GRUB Généré (`/boot/grub/themes/custom/theme.txt`)

Généré automatiquement par `theme_generator.py` à partir de `theme_config.json`.  
Conforme à la spécification officielle GRUB2 gfxmenu :

- `desktop-image`, `desktop-color`
- `boot_menu` (left, top, width, height, item*\*, selected_item*\*)
- `label` (text, font, color, position)
- `progress_bar` (position, dimensions, couleurs)

## Rôles par couche

### Core (Logique Métier)

- **Responsabilités**: Validation, sauvegarde, génération de config, exécution système
- **Principe**: Séparation claire UI/Core via DTOs et Façade
- **Sécurité**: Commandes système exécutées via pkexec, backups automatiques
- **Configuration**: Gestion séparée GRUB standard vs thème personnalisé

### UI (Interface Utilisateur)

- **Responsabilités**: Affichage GTK4, gestion événements, validation UI
- **Principe**: Découplage via Façade, widgets réutilisables
- **UX**: Dialogues spécialisés, notifications toast, confirmations
- **Sauvegarde**: AppearanceTab sauvegarde dans theme_config.json + retourne GRUB_GFXMODE

### Utils (Utilitaires)

- **Responsabilités**: Configuration globale, logging structuré, utilitaires partagés
- **Principe**: Centralisation stricte - Single Source of Truth
- **Exemples**:
  - `parse_grub_color_pair()`: Parsing unique des couleurs "fg/bg"
  - `grub_color_to_hex()`: Conversion unique GRUB → hexadécimal
  - `ALLOWED_GRUB_COLOR_NAMES`: Ensemble unique de couleurs valides
  - Constantes partagées (résolutions, couleurs, dimensions UI)

## Architecture SOLID respectée

- **S**: Single Responsibility (chaque module 1 responsabilité, pas de duplication)
- **O**: Open/Closed (extensible via Façade, pas de modification des couches internes)
- **L**: Liskov Substitution (DTOs immuables, contrats respectés)
- **I**: Interface Segregation (petites interfaces spécialisées)
- **D**: Dependency Inversion (UI dépend de Façade, pas détails implémentation)

## Principes de Qualité Appliqués

### DRY (Don't Repeat Yourself)

- Aucune duplication de code détectée
- Utilitaires centralisés et réutilisés partout
- Constantes définies une seule fois

### KISS (Keep It Simple, Stupid)

- Architecture claire en 3 couches (Core/UI/Utils)
- Façade simplifie l'utilisation du Core
- Chaque module a une responsabilité unique

### Separation of Concerns

- `/etc/default/grub`: Paramètres GRUB standards uniquement
- `/boot/grub/themes/custom/theme_config.json`: Paramètres visuels personnalisés
- Core: Logique métier sans connaissance de l'UI
- UI: Présentation sans logique métier
- Utils: Fonctions transversales réutilisables

### Fail-Safe Design

- Backups automatiques avant toute modification
- Validation stricte des entrées (anti-injection)
- Gestion d'erreurs avec hiérarchie d'exceptions spécialisées
- Rollback automatique en cas d'erreur
