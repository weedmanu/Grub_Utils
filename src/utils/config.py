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
MAIN_WINDOW_HEIGHT = 600
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

# ============================================================================
# PARAMÈTRES DE STYLE AVANCÉS - MENU BOOT
# ============================================================================

# Positionnement du menu (pourcentages ou pixels)
GRUB_MENU_POSITIONS = [
    ("10%", "Gauche 10%"),
    ("15%", "Gauche 15%"),
    ("20%", "Gauche 20%"),
    ("25%", "Gauche 25%"),
    ("30%", "Gauche 30%"),
]

GRUB_MENU_TOPS = [
    ("15%", "Haut 15%"),
    ("20%", "Haut 20%"),
    ("25%", "Haut 25%"),
    ("30%", "Haut 30%"),
]

# Dimensions du menu
GRUB_MENU_WIDTHS = [
    ("60%", "60% (Étroit)"),
    ("70%", "70%"),
    ("80%", "80% (Normal)"),
    ("85%", "85%"),
    ("90%", "90% (Large)"),
]

GRUB_MENU_HEIGHTS = [
    ("40%", "40% (Compact)"),
    ("50%", "50%"),
    ("60%", "60% (Normal)"),
    ("70%", "70%"),
    ("80%", "80% (Haut)"),
]

# Dimensions des éléments du menu
GRUB_ITEM_HEIGHTS = [
    ("20", "Compact (20px)"),
    ("24", "Normal (24px)"),
    ("28", "Moyen (28px)"),
    ("32", "Large (32px)"),
    ("36", "Très large (36px)"),
]

# Espacement entre les éléments
GRUB_ITEM_SPACINGS = [
    ("2", "Minimal (2px)"),
    ("4", "Comprimé (4px)"),
    ("6", "Normal (6px)"),
    ("8", "Spacieux (8px)"),
    ("10", "Aéré (10px)"),
]

# Padding interne des éléments
GRUB_ITEM_PADDINGS = [
    ("5", "Minimal (5px)"),
    ("10", "Normal (10px)"),
    ("15", "Moyen (15px)"),
    ("20", "Généreux (20px)"),
    ("25", "Large (25px)"),
]

# Positions de label (pourcentages ou pixels)
GRUB_LABEL_LEFTS = [
    ("0%", "Extrême gauche (0%)"),
    ("5%", "Gauche (5%)"),
    ("10%", "Gauche 10%"),
    ("15%", "Gauche 15%"),
    ("20%", "Gauche 20%"),
]

GRUB_LABEL_TOPS = [
    ("1%", "Très haut (1%)"),
    ("2%", "Haut (2%)"),
    ("5%", "Haut 5%"),
    ("10%", "Haut 10%"),
    ("15%", "Haut 15%"),
]

# Position de la barre de progression (pourcentages ou pixels)
GRUB_PROGRESS_LEFTS = [
    ("5%", "Gauche 5%"),
    ("10%", "Gauche 10%"),
    ("15%", "Gauche 15%"),
    ("20%", "Gauche 20%"),
]

GRUB_PROGRESS_BOTTOMS = [
    ("5%", "Bas 5%"),
    ("8%", "Bas 8%"),
    ("10%", "Bas (10%)"),
    ("12%", "Bas 12%"),
    ("15%", "Bas 15%"),
    ("90%", "Haut (90%)"),
]

# Dimensions de la barre de progression
GRUB_PROGRESS_WIDTHS = [
    ("60%", "60% (Étroite)"),
    ("70%", "70%"),
    ("80%", "80% (Normal)"),
    ("85%", "85%"),
    ("90%", "90% (Large)"),
]

GRUB_PROGRESS_HEIGHTS = [
    ("8", "Petit (8px)"),
    ("10", "Normal (10px)"),
    ("12", "Moyen (12px)"),
    ("14", "Grand (14px)"),
    ("16", "Très grand (16px)"),
]

# Espacement des icônes
GRUB_ICON_SPACINGS = [
    ("5", "Minimal (5px)"),
    ("8", "Compact (8px)"),
    ("10", "Normal (10px)"),
    ("12", "Spacieux (12px)"),
    ("15", "Aéré (15px)"),
]

# Couleurs pour la barre de progression (couleurs GRUB disponibles)
GRUB_PROGRESS_COLORS = [
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

# Tailles de police (en pixels)
# ⚠️ IMPORTANT: GRUB utilise uniquement la police "unicode" précompilée en .pf2
# Les tailles sont des suggestions de taille d'affichage
GRUB_FONT_SIZES = [
    ("10", "Très petit (10px)"),
    ("12", "Petit (12px)"),
    ("14", "Normal (14px)"),
    ("16", "Grand (16px)"),
    ("18", "Très grand (18px)"),
    ("20", "Extra large (20px)"),
]

# Activation/désactivation du thème
GRUB_USE_THEME_OPTIONS = [
    ("true", "Activé"),
    ("false", "Désactivé"),
]

# Familles de polices GRUB
# ⚠️ IMPORTANT: GRUB en mode gfxmenu supporte UNIQUEMENT "unicode"
# C'est la seule police précompilée disponible en format .pf2
GRUB_FONTS = [
    ("unicode", "Unicode (seule police supportée par GRUB)"),
]

# Styles de texte
# NOTE: Les styles (bold, italic) ne sont pas supportés par GRUB
# GRUB ne peut pas combiner les styles de texte dans les thèmes
GRUB_FONT_STYLES = [
    ("regular", "Régulier"),
]


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
