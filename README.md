# GRUB Manager

Une application GTK4 moderne et sécurisée pour gérer la configuration de GRUB sur Linux.

## Fonctionnalités

- **Configuration complète de GRUB** : Timeout, entrée par défaut, paramètres noyau
- **Personnalisation de l'apparence** : Résolution, image de fond, thèmes
- **Gestion du menu** : Masquer/afficher des entrées spécifiques
- **Sauvegarde et restauration** : Système de sauvegardes automatiques
- **Interface moderne** : GTK4 avec libadwaita (si disponible)
- **Sécurité renforcée** : Validation stricte des entrées, exécution sécurisée des commandes
- **Logging complet** : Suivi de toutes les opérations

## Installation

### Prérequis

- Python 3.10+
- GTK4
- `pkexec` (pour l'authentification root)
- Distributions supportées : Ubuntu 22.04+, Fedora 36+, Arch Linux

### Installation depuis les sources

```bash
# Cloner le dépôt
git clone https://github.com/votre-utilisateur/grub-manager.git
cd grub-manager

# Créer un environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
python main.py
```

### Installation système (recommandé)

```bash
# Installation des dépendances système
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0  # Ubuntu/Debian
sudo dnf install python3-gobject gtk4                    # Fedora
sudo pacman -S python-gobject gtk4                       # Arch

# Copier dans /opt
sudo cp -r . /opt/grub-manager
sudo chmod +x /opt/grub-manager/main.py

# Créer un lanceur desktop
sudo cp grub-manager.desktop /usr/share/applications/
```

## Utilisation

### Interface graphique

Lancez l'application et utilisez les onglets pour configurer :

1. **Général** : Timeout, entrée par défaut, paramètres noyau
2. **Apparence** : Résolution, image de fond, thème
3. **Menu** : Masquer/afficher des entrées spécifiques

Cliquez sur "Sauvegarder et appliquer" pour valider les changements.

### Ligne de commande

```bash
# Sauvegarde de la configuration actuelle
python main.py --backup

# Restauration de la dernière sauvegarde
python main.py --restore

# Mode dry-run (aperçu des changements)
python main.py --dry-run
```

## Architecture

```
src/
├── core/                 # Logique métier
│   ├── grub_manager.py   # Gestionnaire principal
│   ├── validator.py      # Validation des données
│   ├── backup_manager.py # Gestion des sauvegardes
│   ├── command_executor.py # Exécution sécurisée
│   └── exceptions.py     # Exceptions personnalisées
├── ui/                   # Interface utilisateur
│   ├── app.py           # Application principale
│   ├── dialogs/         # Dialogs (erreur, confirmation)
│   └── tabs/            # Onglets de configuration
└── utils/               # Utilitaires
    ├── logger.py        # Configuration logging
    └── config.py        # Constantes
```

## Sécurité

- **Aucune injection de commandes** : Utilisation de scripts temporaires sécurisés
- **Validation stricte** : Toutes les entrées utilisateur sont validées
- **Permissions minimales** : Utilise `pkexec` pour les opérations privilégiées
- **Audit logging** : Toutes les opérations sont tracées

## Tests

```bash
# Exécuter tous les tests
python -m unittest discover src/tests/

# Tests avec couverture
python -m pytest --cov=src/ src/tests/
```

## Développement

### Configuration de l'environnement de développement

```bash
# Installer les outils de développement
pip install -r requirements-dev.txt

# Vérification du code
ruff check src/
mypy src/
pylint src/

# Tests
python -m unittest discover src/tests/
```

### Structure des commits

Format: `type(scope): description`

- `feat:` Nouvelle fonctionnalité
- `fix:` Correction de bug
- `refactor:` Refactorisation
- `docs:` Documentation
- `test:` Tests
- `chore:` Maintenance

## Dépannage

### Problèmes courants

**Erreur d'authentification**

- Vérifiez que `pkexec` est installé
- Assurez-vous d'avoir les droits sudo

**Interface ne se lance pas**

- Vérifiez que GTK4 est installé
- Essayez `export GTK_DEBUG=interactive`

**Changements non appliqués**

- Vérifiez les logs : `~/.local/share/grub-manager/app.log`
- Vérifiez les permissions sur `/etc/default/grub`

### Logs

Les logs sont disponibles dans :

- `/var/log/grub-manager/app.log` (si root)
- `~/.local/share/grub-manager/app.log` (utilisateur)

## Contribution

1. Fork le projet
2. Créez une branche (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Committez (`git commit -am 'feat: ajoute nouvelle fonctionnalité'`)
4. Pushez (`git push origin feature/nouvelle-fonctionnalite`)
5. Ouvrez une Pull Request

## Licence

MIT License - voir le fichier LICENSE pour plus de détails.

## Remerciements

- Basé sur les spécifications GRUB
- Interface inspirée de Grub Customizer
- Communauté GTK pour la documentation
