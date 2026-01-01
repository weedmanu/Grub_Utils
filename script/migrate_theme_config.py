#!/usr/bin/env python3
"""Script de migration pour nettoyer les paramètres non-standard de /etc/default/grub.

Ce script :
1. Lit /etc/default/grub
2. Extrait les paramètres de thème non-standard (GRUB_MENU_*, GRUB_FONT_*, etc.)
3. Crée theme_config.json avec ces valeurs
4. Supprime ces paramètres de /etc/default/grub
5. Garde uniquement les paramètres standards GRUB
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour importer les modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config.theme_config import ThemeConfiguration, ThemeConfigManager
from src.core.command_executor import SecureCommandExecutor
from src.core.config.loader import GrubConfigLoader
from src.core.config.generator import GrubConfigGenerator
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Paramètres non-standard à supprimer de /etc/default/grub
NON_STANDARD_PARAMS = {
    "GRUB_MENU_LEFT",
    "GRUB_MENU_TOP",
    "GRUB_MENU_WIDTH",
    "GRUB_MENU_HEIGHT",
    "GRUB_ITEM_HEIGHT",
    "GRUB_ITEM_SPACING",
    "GRUB_ITEM_PADDING",
    "GRUB_ICON_SPACING",
    "GRUB_TITLE_TEXT",
    "GRUB_LABEL_TEXT",
    "GRUB_LABEL_LEFT",
    "GRUB_LABEL_TOP",
    "GRUB_LABEL_COLOR",
    "GRUB_PROGRESS_LEFT",
    "GRUB_PROGRESS_BOTTOM",
    "GRUB_PROGRESS_WIDTH",
    "GRUB_PROGRESS_HEIGHT",
    "GRUB_PROGRESS_FG",
    "GRUB_PROGRESS_BG",
    "GRUB_PROGRESS_BORDER",
    "GRUB_PROGRESS_BAR",
    "GRUB_FONT_NORMAL",
    "GRUB_FONT_HIGHLIGHT",
    "GRUB_FONT_LABEL",
    "GRUB_FONT_ITEM",
    "GRUB_FONT_ITEM_HIGHLIGHT",
    "GRUB_USE_THEME",
}


def migrate_to_theme_config():
    """Migrer les paramètres de thème vers theme_config.json."""
    print("🔄 Migration des paramètres de thème...")
    
    # 1. Charger la configuration GRUB actuelle
    loader = GrubConfigLoader()
    entries, original_lines = loader.load()
    
    print(f"📖 Configuration GRUB chargée ({len(entries)} paramètres)")
    
    # 2. Créer ThemeConfiguration à partir des paramètres GRUB
    config_manager = ThemeConfigManager()
    theme_config = config_manager.load_from_grub_config(entries)
    
    print(f"✨ Configuration thème créée (enabled={theme_config.enabled})")
    
    # 3. Sauvegarder dans theme_config.json
    executor = SecureCommandExecutor()
    success, error = config_manager.save(theme_config, executor)
    
    if not success:
        print(f"❌ Erreur lors de la sauvegarde de theme_config.json: {error}")
        return False
    
    print(f"✅ theme_config.json créé avec succès")
    
    # 4. Supprimer les paramètres non-standard de /etc/default/grub
    cleaned_entries = {k: v for k, v in entries.items() if k not in NON_STANDARD_PARAMS}
    removed_count = len(entries) - len(cleaned_entries)
    
    print(f"🧹 {removed_count} paramètres non-standard retirés")
    
    # 5. Générer le nouveau fichier /etc/default/grub
    generator = GrubConfigGenerator()
    new_content = generator.generate(cleaned_entries, original_lines)
    
    # 6. Sauvegarder le nouveau fichier
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.grub') as f:
        f.write(new_content)
        temp_path = f.name
    
    success, error = executor.copy_file_privileged(temp_path, "/etc/default/grub")
    
    import os
    os.unlink(temp_path)
    
    if not success:
        print(f"❌ Erreur lors de la mise à jour de /etc/default/grub: {error}")
        return False
    
    print("✅ /etc/default/grub nettoyé avec succès")
    print("\n📋 Résumé:")
    print(f"   • Paramètres migrés vers theme_config.json: {removed_count}")
    print(f"   • Paramètres restants dans /etc/default/grub: {len(cleaned_entries)}")
    print("\n✨ Migration terminée avec succès!")
    
    return True


if __name__ == "__main__":
    try:
        success = migrate_to_theme_config()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.exception("Erreur lors de la migration")
        print(f"\n❌ Erreur fatale: {e}")
        sys.exit(1)
