# Structure du Projet GRUB Manager

## Vue d'ensemble

Ce projet est une application GTK4 pour gérer la configuration GRUB de manière graphique et sécurisée. Il suit une architecture SOLID avec séparation claire des responsabilités.

## Arborescence

```
grub_manager/
├── main.py                                    # Point d'entrée principal de l'application GTK
├── src/                                       # Code source principal
│   ├── core/                                  # Logique métier centrale (architecture SOLID)
│   │   ├── backup_manager.py                  # Gestion des sauvegardes automatiques
│   │   ├── command_executor.py                # Exécution sécurisée des commandes système
│   │   ├── config/                            # Modules de traitement de la configuration GRUB
│   │   │   ├── generator.py                   # Génération du contenu de configuration
│   │   │   ├── loader.py                      # Chargement du fichier /etc/default/grub
│   │   │   └── parser.py                      # Parsing du fichier grub.cfg pour les entrées menu
│   │   ├── dtos.py                            # Objets de transfert de données (Résultats, Backups)
│   │   ├── exceptions.py                      # Hiérarchie d'exceptions métier spécialisées
│   │   ├── facade.py                          # Façade simplifiant l'API pour l'interface utilisateur
│   │   ├── security.py                        # Validation d'entrées et prévention des injections
│   │   ├── services/                          # Services métier orchestrateurs
│   │   │   └── grub_service.py                # Service principal GRUB (load/save/apply/backup)
│   │   └── validator.py                       # Validation des paramètres de configuration
│   ├── ui/                                    # Interface utilisateur GTK4
│   │   ├── app.py                             # Application principale GTK avec logique UI
│   │   ├── dialogs/                           # Boîtes de dialogue spécialisées
│   │   │   ├── backup_selector_dialog.py      # Sélectionneur de sauvegarde
│   │   │   ├── base_dialog.py                 # Classe de base pour les dialogues
│   │   │   ├── confirm_dialog.py              # Dialogue de confirmation générique
│   │   │   ├── error_dialog.py                # Affichage des erreurs utilisateur
│   │   │   ├── preview_dialog.py              # Aperçu avant application des changements
│   │   │   └── text_view_utils.py             # Utilitaires pour les vues texte
│   │   ├── gtk_init.py                        # Initialisation GTK avec fallback Adwaita
│   │   └── tabs/                              # Onglets de l'interface utilisateur
│   │       ├── appearance.py                  # Onglet configuration apparence (thème, background)
│   │       ├── base.py                        # Classe de base pour les onglets
│   │       ├── general.py                     # Onglet paramètres généraux (timeout, default entry)
│   │       └── menu.py                        # Onglet gestion des entrées de menu
│   └── utils/                                 # Utilitaires transversaux
│       ├── config.py                          # Constantes de configuration globales
│       └── logger.py                          # Configuration centralisée du logging
```

## Rôles par couche

### Core (Logique Métier)

- **Responsabilités**: Validation, sauvegarde, génération de config, exécution système
- **Principe**: Séparation claire UI/Core via DTOs et Façade
- **Sécurité**: Commandes système exécutées via pkexec, backups automatiques

### UI (Interface Utilisateur)

- **Responsabilités**: Affichage GTK4, gestion événements, validation UI
- **Principe**: Découplage via Façade, widgets réutilisables
- **UX**: Dialogues spécialisés, notifications toast, confirmations

### Utils (Utilitaires)

- **Responsabilités**: Configuration globale, logging structuré
- **Principe**: Utilitaires transversaux partagés par toutes les couches

## Architecture SOLID respectée

- **S**: Single Responsibility (chaque module 1 responsabilité)
- **O**: Open/Closed (extensible via Façade)
- **L**: Liskov Substitution (DTOs immuables)
- **I**: Interface Segregation (petites interfaces spécialisées)
- **D**: Dependency Inversion (UI dépend de Façade, pas détails implémentation)
