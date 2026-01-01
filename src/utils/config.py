"""Constantes et configuration pour GRUB Manager."""

# Chemins système
GRUB_CONFIG_PATH = "/etc/default/grub"
GRUB_CFG_PATHS = ["/boot/grub/grub.cfg", "/boot/grub2/grub.cfg"]
GRUB_BACKGROUNDS_DIR = "/boot/grub/backgrounds"

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
MAIN_WINDOW_HEIGHT = 650
PREVIEW_WINDOW_WIDTH = 1200
PREVIEW_WINDOW_HEIGHT = 800

# Espacement et marges UI
DEFAULT_MARGIN = 20
DEFAULT_SPACING = 10
GRID_COLUMN_SPACING = 10
GRID_ROW_SPACING = 10

# Résolutions GRUB standards (compatibles avec la plupart des écrans)
GRUB_RESOLUTIONS = [
    ("auto", "Automatique"),
    ("640x480", "640×480 (VGA)"),
    ("800x600", "800×600 (SVGA)"),
    ("1024x768", "1024×768 (XGA)"),
    ("1280x720", "1280×720 (HD 720p)"),
    ("1280x800", "1280×800 (WXGA)"),
    ("1280x1024", "1280×1024 (SXGA)"),
    ("1366x768", "1366×768 (HD)"),
    ("1440x900", "1440×900 (WXGA+)"),
    ("1600x900", "1600×900 (HD+)"),
    ("1680x1050", "1680×1050 (WSXGA+)"),
    ("1920x1080", "1920×1080 (Full HD)"),
    ("1920x1200", "1920×1200 (WUXGA)"),
    ("2560x1440", "2560×1440 (QHD)"),
    ("3840x2160", "3840×2160 (4K UHD)"),
]

# Couleurs GRUB disponibles (nom GRUB, label français)
GRUB_COLORS = [
    ("black", "Noir"),
    ("blue", "Bleu"),
    ("green", "Vert"),
    ("cyan", "Cyan"),
    ("red", "Rouge"),
    ("magenta", "Magenta"),
    ("brown", "Marron"),
    ("light-gray", "Gris clair"),
    ("dark-gray", "Gris foncé"),
    ("light-blue", "Bleu clair"),
    ("light-green", "Vert clair"),
    ("light-cyan", "Cyan clair"),
    ("light-red", "Rouge clair"),
    ("light-magenta", "Magenta clair"),
    ("yellow", "Jaune"),
    ("white", "Blanc"),
]

# Mapping des couleurs GRUB vers hexadécimal (palette VGA standard)
GRUB_COLOR_TO_HEX = {
    "black": "#000000",
    "blue": "#0000aa",
    "green": "#00aa00",
    "cyan": "#00aaaa",
    "red": "#aa0000",
    "magenta": "#aa00aa",
    "brown": "#aa5500",
    "light-gray": "#aaaaaa",
    "dark-gray": "#555555",
    "light-blue": "#5555ff",
    "light-green": "#55ff55",
    "light-cyan": "#55ffff",
    "light-red": "#ff5555",
    "light-magenta": "#ff55ff",
    "yellow": "#ffff55",
    "white": "#ffffff",
}

# Ensemble des noms de couleurs GRUB autorisés (palette VGA de base)
ALLOWED_GRUB_COLOR_NAMES = frozenset(GRUB_COLOR_TO_HEX.keys())


def grub_color_to_hex(color_name: str) -> str:
    """Convertit un nom de couleur GRUB en valeur hexadécimale.

    Args:
        color_name: Nom de la couleur GRUB (ex: "light-gray")

    Returns:
        str: Valeur hexadécimale (ex: "#aaaaaa")

    """
    return GRUB_COLOR_TO_HEX.get(color_name.lower(), "#aaaaaa")


def parse_grub_color_pair(color_string: str) -> tuple[str, str]:
    """Parse une paire de couleurs GRUB au format "fg/bg".

    Args:
        color_string: Couleurs au format "fg/bg" ou couleur unique

    Returns:
        tuple[str, str]: (couleur_premier_plan, couleur_arriere_plan)

    Examples:
        >>> parse_grub_color_pair("white/black")
        ('white', 'black')
        >>> parse_grub_color_pair("light-gray")
        ('light-gray', 'black')

    """
    if "/" in color_string:
        fg, bg = color_string.split("/", 1)
        return fg.strip(), bg.strip()
    return color_string.strip(), "black"
