# GRUB Manager - Gestionnaire GRUB Graphique

> Application GTK4 moderne pour gérer la configuration GRUB de manière graphique et sécurisée

[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![GTK](https://img.shields.io/badge/GTK-4.0-green.svg)](https://www.gtk.org/)
[![Code Quality](https://img.shields.io/badge/pylint-9.71%2F10-brightgreen.svg)](https://pylint.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 📋 Table des matières

- [Vue d'ensemble](#-vue-densemble)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Utilisation](#-utilisation)
- [Architecture](#-architecture)
- [Standards de qualité](#-standards-de-qualité)
- [Centralisation](#-centralisation)
- [Configuration](#-configuration)
- [Développement](#-développement)
- [Tests](#-tests)

---

## 🎯 Vue d'ensemble

GRUB Manager est une application GTK4 professionnelle pour gérer la configuration du bootloader GRUB2. Elle offre une interface graphique intuitive tout en respectant les standards Linux et les meilleures pratiques de développement Python.

### Fonctionnalités principales

- ✅ **Configuration graphique** : Interface GTK4/Adwaita moderne
- 🎨 **Personnalisation apparence** : Couleurs, image de fond, résolution
- ⚙️ **Paramètres système** : Timeout, entrée par défaut, paramètres noyau
- 📋 **Gestion des entrées** : Masquage/affichage des entrées de menu **avec persistance après update-grub**
- 💾 **Backups automatiques** : Protection contre les corruptions
- 🔒 **Sécurité renforcée** : Validation anti-injection, élévation privilèges via pkexec
- 👁️ **Aperçu temps réel** : Prévisualisation avant application

---

## 📦 Prérequis

### Système

- **OS** : Linux (Ubuntu 20.04+, Fedora 35+, Arch, etc.)
- **Python** : 3.12 ou supérieur
- **GTK** : 4.0+
- **GRUB** : 2.x

### Dépendances Python

```bash
# Installation des dépendances système (Ubuntu/Debian)
sudo apt install python3.12 python3.12-venv python3-gi python3-gi-cairo gir1.2-gtk-4.0

# Installation des dépendances système (Fedora)
sudo dnf install python3.12 python3-gobject gtk4
```

---

## 🚀 Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-utilisateur/Grub_utils.git
cd Grub_utils
```

### 2. Créer l'environnement virtuel Python

```bash
# Créer le venv (.venv est ignoré par git)
python3.12 -m venv .venv

# Activer l'environnement
source .venv/bin/activate  # Linux/macOS
# ou
.venv\Scripts\activate     # Windows
```

### 3. Installer les dépendances

```bash
# Installation des packages Python
pip install -r requirements.txt

# Installation des outils de développement (optionnel)
pip install pylint pytest pytest-cov vulture
```

### 4. Lancer l'application

```bash
# Mode développement
python3 main.py

# Ou via le venv directement
.venv/bin/python main.py
```

---

## 🚀 Utilisation

### Lancement de l'application

```bash
python3 main.py
```

L'application nécessite les privilèges root (via pkexec) pour modifier les fichiers GRUB.

### Onglets disponibles

#### 📋 Onglet Menu

Gérez les entrées de menu GRUB :

- **Cochez** les entrées à afficher dans le menu GRUB
- **Décochez** les entrées à masquer
- Les entrées masquées sont sauvegardées dans `/etc/grub.d/hidden_entries.json`
- Un hook automatique (`/etc/kernel/postinst.d/zz-grub-hide-entries`) garantit la persistance après `update-grub`

#### ⚙️ Onglet Général

Configurez les paramètres GRUB :

- **Timeout** : Délai d'affichage du menu (0-300 secondes)
- **Entrée par défaut** : Système démarré par défaut
- **Paramètres du noyau** : Options de la ligne de commande Linux

#### 🎨 Onglet Apparence

Personnalisez l'apparence de GRUB :

- **Image de fond** : Sélectionnez une image (PNG, JPG, TGA)
- **Résolution** : Définissez la résolution d'affichage
- **Couleurs** : Menu, texte, sélection
- **Aperçu** : Prévisualisez vos changements en temps réel

#### 💾 Onglet Backup

Gérez vos sauvegardes :

- **Créer** : Sauvegarde manuelle de la configuration
- **Restaurer** : Revenir à une sauvegarde précédente
- Maximum 3 backups automatiques conservés

### Fonctionnement du masquage persistant

```
1. Utilisateur décoche des entrées dans l'onglet Menu
2. Clic sur "Enregistrer"
3. Sauvegarde dans /etc/grub.d/hidden_entries.json
4. Création du hook /etc/kernel/postinst.d/zz-grub-hide-entries
5. Application immédiate à grub.cfg
6. Lors d'un update-grub : le hook ré-applique automatiquement les masquages
```

---

## 🏗️ Architecture

### Structure du projet

```
.
├── .venv/                    # Environnement virtuel Python (git-ignoré)
├── main.py                   # Point d'entrée principal
├── src/
│   ├── core/                 # Logique métier (SOLID)
│   │   ├── config/           # Gestion configuration GRUB
│   │   │   ├── generator.py          # Génération /etc/default/grub
│   │   │   ├── loader.py             # Chargement configuration
│   │   │   ├── parser.py             # Parsing grub.cfg
│   │   │   ├── hidden_entries_manager.py  # Gestion entrées masquées
│   │   │   └── line_processor.py     # Traitement/normalisation des lignes
│   │   ├── services/         # Services métier
│   │   │   ├── grub_service.py      # Service principal GRUB
│   │   │   ├── save_manager.py      # Gestion sauvegarde
│   │   │   └── file_copy_helper.py  # Helper copie fichiers
│   │   ├── backup_manager.py # Gestion backups
│   │   ├── command_executor.py # Exécution commandes système
│   │   ├── container.py      # Conteneur DI (inutilisé legacy)
│   │   ├── dtos.py           # Data Transfer Objects
│   │   ├── exceptions.py     # Hiérarchie exceptions
│   │   ├── facade.py         # Façade API simplifiée
│   │   ├── security.py       # Validation anti-injection
│   │   ├── setup.py          # Configuration conteneur
│   │   └── validator.py      # Validation configuration
│   ├── ui/                   # Interface utilisateur GTK4
│   │   ├── dialogs/          # Dialogues spécialisés
│   │   │   ├── grub_screen_builder.py  # Builder écran GRUB
│   │   │   ├── summary_builder.py      # Builder résumé changements
│   │   │   ├── preview_dialog.py       # Aperçu avant application
│   │   │   ├── backup_selector_dialog.py
│   │   │   ├── confirm_dialog.py
│   │   │   ├── error_dialog.py
│   │   │   ├── base_dialog.py
│   │   │   └── text_view_utils.py
│   │   ├── tabs/             # Onglets interface
│   │   │   ├── appearance.py          # Onglet apparence
│   │   │   ├── appearance_ui_builder.py # Builder UI apparence
│   │   │   ├── general.py             # Onglet général
│   │   │   ├── menu.py                # Onglet menu
│   │   │   ├── backup.py              # Onglet backups
│   │   │   └── base.py                # Classe de base
│   │   ├── app.py            # Application principale GTK
│   │   ├── app_state.py      # État application (widgets)
│   │   ├── enums.py          # Énumérations UI
│   │   └── gtk_init.py       # Initialisation GTK
│   └── utils/                # Utilitaires transversaux
│       ├── config.py         # Configuration centralisée
│       └── logger.py         # Logging centralisé
├── tests/                    # Tests (unit/integration/e2e)
├── script/                   # Scripts utilitaires
├── requirements.txt          # Dépendances Python
├── pyproject.toml            # Configuration projet
├── pytest.ini                # Configuration pytest
└── README.md                 # Ce fichier
```

### Séparation des couches (SOLID)

```
┌─────────────────────────────────────────────┐
│              UI Layer (GTK4)                │
│  - Présentation uniquement                  │
│  - Aucune logique métier                    │
└──────────────────┬──────────────────────────┘
                   │ via Façade
┌──────────────────▼──────────────────────────┐
│            Core Layer (Business)            │
│  - Logique métier                           │
│  - Validation, sauvegarde, génération       │
│  - Services, managers, generators           │
└──────────────────┬──────────────────────────┘
                   │ utilise
┌──────────────────▼──────────────────────────┐
│           Utils Layer (Shared)              │
│  - Configuration centralisée                │
│  - Logging structuré                        │
│  - Constantes globales                      │
└─────────────────────────────────────────────┘
```

---

## 🎖️ Standards de qualité

### Exigences de code obligatoires

#### 1. **Pylint** : Score minimum **9.5/10**

```bash
# Vérification
pylint src/ --score=y

# Score actuel : 9.71/10 ✅
```

**Règles strictes appliquées** :

- ✅ Pas de violations **R09XX** (SOLID/SRP : too-many-_, too-few-_)
- ✅ Pas de violations **E** (erreurs)
- ✅ **R0801** < 10% (duplication de code)
- ✅ Nommage cohérent : `*Manager`, `*Service`, `*Generator`, `*Loader`, `*Validator`, `*Builder`

#### 2. **Vulture** : 0 code mort (seuil 65%)

```bash
# Vérification
vulture src/ --min-confidence 65

# Résultat attendu : aucune sortie ✅
```

#### 3. **Type Hints** : Couverture 100%

- Tous les paramètres de fonction typés
- Tous les retours de fonction typés
- Utilisation de `from __future__ import annotations` si nécessaire

#### 4. **Docstrings** : Couverture 100%

Format Google Style :

```python
def ma_fonction(param1: str, param2: int) -> bool:
    """Description courte de la fonction.

    Description détaillée optionnelle.

    Args:
        param1: Description du paramètre 1
        param2: Description du paramètre 2

    Returns:
        Description du retour

    Raises:
        ValueError: Si param2 < 0

    """
```

#### 5. **Tests** : Couverture minimum 80%

```bash
# Exécution tests avec couverture
pytest tests/ --cov=src --cov-report=html

# Voir rapport : htmlcov/index.html
```

### Standards Python (PEP)

- **PEP 8** : Style de code Python
- **PEP 257** : Docstring conventions
- **PEP 484** : Type hints
- **PEP 526** : Variable annotations
- **PEP 585** : Generic types (`list[str]` au lieu de `List[str]`)

### Principes SOLID appliqués

| Principe                  | Implémentation                                                        |
| ------------------------- | --------------------------------------------------------------------- |
| **S**ingle Responsibility | Responsabilités séparées (Loader/Generator/Parser/Managers/Service)   |
| **O**pen/Closed           | API stable via `GrubFacade`, évolution via composants internes dédiés |
| **L**iskov Substitution   | DTOs immutables (`@dataclass(frozen=True)`)                           |
| **I**nterface Segregation | Interfaces spécialisées (SaveCallbacks, etc.)                         |
| **D**ependency Inversion  | UI → Façade ← Core (injection via `Container`/`setup_container`)      |

### Patterns appliqués

- **Façade Pattern** : `GrubFacade` simplifie l'API pour l'UI
- **Builder Pattern** : `GrubCSSBuilder`, `GrubMenuBuilder`, `SummaryBuilder`, `AppearanceUIBuilder`
- **Manager Pattern** : `BackupManager`, `SaveManager`, `HiddenEntriesManager`
- **DTO Pattern** : `OperationResultDTO`, `BackupInfoDTO`, `PreviewConfigDTO`, `SaveResult`
- **Strategy Pattern** : Validation via `GrubValidator`

---

## 🔄 Centralisation

### Principe : Single Source of Truth

**Tout ce qui peut être centralisé DOIT l'être** pour éviter la duplication et garantir la cohérence.

### 1. Configuration (`src/utils/config.py`)

**Centralisation des constantes** :

```python
# ✅ BON : Constante centralisée
from src.utils.config import GRUB_COLORS, GRUB_COLOR_TO_HEX

# ❌ MAUVAIS : Constante locale dupliquée
COLORS = ["black", "white", "red", ...]  # À éviter !
```

**Contenu centralisé** :

- `GRUB_COLORS` : Liste unique des couleurs GRUB autorisées
- `GRUB_COLOR_TO_HEX` : Mapping unique couleurs → hexadécimal
- `ALLOWED_GRUB_COLOR_NAMES` : Frozenset de validation
- `GRUB_RESOLUTIONS` : Résolutions graphiques supportées
- `GRUB_CFG_PATHS` : Chemins standards de configuration
- `MAIN_WINDOW_WIDTH/HEIGHT` : Dimensions fenêtre
- `TOAST_TIMEOUT` : Durée notifications

**Fonctions centralisées** :

- `parse_grub_color_pair(color_string)` : Parsing "fg/bg"
- `grub_color_to_hex(color_name)` : Conversion GRUB → hex

### 2. Logging (`src/utils/logger.py`)

**Configuration unique du logging** :

```python
# ✅ BON : Logger centralisé
from src.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("Message")

# ❌ MAUVAIS : Configuration locale
import logging
logging.basicConfig(...)  # À éviter !
```

**Configuration centralisée** :

- Format unique : `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- Niveau par défaut : `INFO`
- Handler : `StreamHandler(sys.stdout)`
- Réutilisé par tous les modules via `get_logger(__name__)`

### 3. Exceptions (`src/core/exceptions.py`)

**Hiérarchie unique d'exceptions métier** :

```python
GrubError (base)
├── GrubConfigError       # Erreurs de configuration
├── GrubValidationError   # Erreurs de validation
├── GrubBackupError       # Erreurs de backup
├── GrubFileError         # Erreurs de fichiers
├── GrubApplyError        # Erreurs d'application (legacy)
├── GrubThemeError        # Erreurs de thème (legacy)
└── GrubParseError        # Erreurs de parsing (legacy)
```

**Usage** :

```python
# ✅ BON : Exception spécialisée
from src.core.exceptions import GrubValidationError

raise GrubValidationError(f"Invalid color: {color}")

# ❌ MAUVAIS : Exception générique
raise ValueError(f"Invalid color: {color}")  # Trop générique
```

### 4. Validation (`src/core/validator.py`)

**Validation centralisée** :

```python
# ✅ BON : Validation centralisée
from src.core.validator import GrubValidator

validator = GrubValidator()
validator.validate_color("white/black")

# ❌ MAUVAIS : Validation locale
if color not in ["black", "white", ...]:  # Duplication !
```

**Méthodes centralisées** :

- `validate_color(color)` : Validation couleurs GRUB
- `validate_timeout(timeout)` : Validation timeout
- `validate_resolution(resolution)` : Validation résolution

### 5. Widgets UI (`src/ui/tabs/base.py`)

**Composants UI réutilisables** :

```python
# ✅ BON : Widget centralisé
from src.ui.tabs.base import BaseTab

class MonTab(BaseTab):
    def __init__(self, app):
        super().__init__(app)
        info_box = self.create_info_box()  # Méthode héritée

# ❌ MAUVAIS : Recréer le widget
info_box = Gtk.Box(...)  # Duplication de code
```

### 6. Builders (`src/ui/dialogs/*_builder.py`)

**Construction UI déléguée** :

- `grub_screen_builder.py` : Construction écran GRUB (couleurs, CSS, menu) via `GrubCSSBuilder` / `GrubMenuBuilder`
- `SummaryBuilder` : Construction résumé changements
- `AppearanceUIBuilder` : Construction interface apparence

**Principe** : Extraire la logique de construction complexe dans des classes dédiées.

### Checklist centralisation

Avant d'ajouter du code, vérifier :

- [ ] Cette constante existe-t-elle déjà dans `src/utils/config.py` ?
- [ ] Cette fonction de validation existe-t-elle dans `src/core/validator.py` ?
- [ ] Ce widget existe-t-il dans `src/ui/tabs/base.py` ?
- [ ] Cette exception existe-t-elle dans `src/core/exceptions.py` ?
- [ ] Ce logger est-il créé via `get_logger(__name__)` ?

**Règle d'or** : Si utilisé 2+ fois → centraliser !

---

## ⚙️ Configuration

### Configuration GRUB Standard (`/etc/default/grub`)

Contient **uniquement** les paramètres standards reconnus par GRUB :

```bash
GRUB_TIMEOUT=5
GRUB_DEFAULT=0
GRUB_GFXMODE=1024x768
GRUB_TERMINAL_OUTPUT=gfxterm
GRUB_THEME=/boot/grub/themes/custom/theme.txt
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"
```

### Thème GRUB (`GRUB_THEME`)

Le projet gère la clé `GRUB_THEME` dans `/etc/default/grub` (validation du chemin et écriture de la valeur).
Il ne génère pas de fichier `theme.txt` ni de configuration de thème avancée ; le fichier (s'il est utilisé) doit déjà exister sur le système.

---

## 🛠️ Développement

### Configuration environnement

```bash
# Activer venv
source .venv/bin/activate

# Installer dépendances dev
pip install -r requirements.txt
pip install pylint pytest pytest-cov vulture black isort
```

### Workflow de développement

1. **Créer une branche**

   ```bash
   git checkout -b feature/ma-fonctionnalite
   ```

2. **Développer en respectant les standards**

   - Type hints sur toutes les fonctions
   - Docstrings Google Style
   - Nommage cohérent (`*Manager`, `*Service`, etc.)
   - Centraliser les constantes/fonctions réutilisables

3. **Vérifier la qualité**

   ```bash
   # Pylint
   pylint src/ --score=y
   # Objectif : 9.5+/10

   # Vulture (code mort)
   vulture src/ --min-confidence 65
   # Objectif : aucune sortie

   # Tests
   pytest tests/ --cov=src
   # Objectif : 80%+ couverture
   ```

4. **Formater le code**

   ```bash
   # Black (formateur)
   black src/ tests/

   # isort (tri imports)
   isort src/ tests/
   ```

5. **Commit et push**
   ```bash
   git add .
   git commit -m "feat: description de la fonctionnalité"
   git push origin feature/ma-fonctionnalite
   ```

### Conventions de nommage

| Type         | Pattern                    | Exemple                                                                 |
| ------------ | -------------------------- | ----------------------------------------------------------------------- |
| Gestionnaire | `*Manager`                 | `BackupManager`, `SaveManager`                                          |
| Service      | `*Service`                 | `GrubService`                                                           |
| Générateur   | `*Generator`               | `GrubConfigGenerator`                                                   |
| Chargeur     | `*Loader`                  | `GrubConfigLoader`                                                      |
| Validateur   | `*Validator`               | `GrubValidator`                                                         |
| Constructeur | `*Builder`                 | `GrubCSSBuilder`, `GrubMenuBuilder`, `SummaryBuilder`                   |
| DTO          | `*DTO`, `*Result`, `*Info` | `PreviewConfigDTO`, `SaveResult`, `BackupInfoDTO`, `OperationResultDTO` |
| Helper       | `*Helper`                  | `FileCopyHelper`                                                        |

### Règles d'or

1. **SRP** : 1 classe = 1 responsabilité unique
2. **DRY** : Pas de duplication → centraliser
3. **Type hints** : Typer 100% du code
4. **Docstrings** : Documenter 100% API publique
5. **Tests** : Tester toute nouvelle fonctionnalité
6. **Pylint** : Maintenir score > 9.5/10

---

## 🧪 Tests

### Structure des tests

```
tests/
├── unit/              # Tests unitaires (isolation)
│   ├── core/
│   └── ui/
├── integration/       # Tests d'intégration (modules combinés)
└── e2e/              # Tests end-to-end (scénarios complets)
```

### Exécution

```bash
# Tous les tests
pytest tests/

# Tests unitaires uniquement
pytest tests/unit/

# Avec couverture
pytest tests/ --cov=src --cov-report=html
# Ouvrir htmlcov/index.html

# Tests spécifiques
pytest tests/unit/core/test_validator.py -v

# Mode verbose avec détails
pytest tests/ -vv
```

---

## 📦 Packaging Debian (.deb)

Le dépôt contient une configuration Debian prête à l'emploi dans `debian/` ainsi que les fichiers desktop/AppStream dans `data/`.

### Dépendances de build

Sur Debian/Ubuntu :

```bash
sudo apt update
sudo apt install -y build-essential devscripts debhelper dh-python
```

### Construire le paquet

Depuis la racine du projet :

```bash
dpkg-buildpackage -us -uc
```

Le `.deb` est généré dans le dossier parent.

### Installer / désinstaller

```bash
sudo apt install ./../grub-manager-gtk_*_all.deb

# Désinstallation
sudo apt remove grub-manager-gtk
```

### Intégration desktop

- Lanceur : `com.github.grubutils.GrubManager.desktop`
- Commande : `grub-manager-gtk`

Note : l'application demandera une élévation de privilèges via `pkexec` pour modifier la configuration GRUB.

### Écrire un test

```python
# tests/unit/core/test_validator.py
import pytest
from src.core.validator import GrubValidator
from src.core.exceptions import GrubValidationError

def test_validate_color_valid():
    """Test validation couleur valide."""
    validator = GrubValidator()
    # Ne doit pas lever d'exception
    validator.validate_color("white/black")

def test_validate_color_invalid():
    """Test validation couleur invalide."""
    validator = GrubValidator()
    with pytest.raises(GrubValidationError):
        validator.validate_color("invalid/color")
```

---

## 📝 Licence

MIT License - voir fichier [LICENSE](LICENSE)

---

## 🤝 Contribution

Les contributions sont les bienvenues ! Merci de :

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Respecter les standards de qualité (Pylint 9.5+, tests, docstrings)
4. Commit (`git commit -m 'feat: Add AmazingFeature'`)
5. Push (`git push origin feature/AmazingFeature`)
6. Ouvrir une Pull Request

---

## 📞 Support

- **Issues** : [GitHub Issues](https://github.com/votre-utilisateur/Grub_utils/issues)
- **Discussions** : [GitHub Discussions](https://github.com/votre-utilisateur/Grub_utils/discussions)

---

**Développé avec ❤️ et respect des standards SOLID/Clean Code**
