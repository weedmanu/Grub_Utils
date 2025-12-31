"""Constantes et configuration pour GRUB Manager."""

# Chemins système
GRUB_CONFIG_PATH = "/etc/default/grub"
GRUB_CFG_PATHS = ["/boot/grub/grub.cfg", "/boot/grub2/grub.cfg"]

# Extensions de fichiers autorisées
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tga"}
ALLOWED_THEME_EXTENSIONS = {".txt"}

# Limites de validation
BACKUP_MAX_COUNT = 3

# Timeouts (en secondes)
COMMAND_TIMEOUT = 60  # Timeout par défaut pour l'exécution des commandes
GRUB_TIMEOUT_MAX = 300  # Timeout GRUB maximum en secondes

# Timeouts UI (en millisecondes)
TOAST_TIMEOUT = 3000  # Durée d'affichage des toasts

# Dimensions UI
MAIN_WINDOW_WIDTH = 500
MAIN_WINDOW_HEIGHT = 600
PREVIEW_WINDOW_WIDTH = 1200
PREVIEW_WINDOW_HEIGHT = 800

# Espacement et marges UI
DEFAULT_MARGIN = 20
DEFAULT_SPACING = 10
GRID_COLUMN_SPACING = 10
GRID_ROW_SPACING = 10
