"""Package de l'onglet Apparence.

Ce package découpe l'ancien module monolithique en sous-modules (SOLID) tout en
préservant l'API publique :

    from src.ui.tabs.appearance import AppearanceTab

Note: Les constantes (GRUB_*) sont exposées au niveau du package pour permettre
les patchs de tests via "src.ui.tabs.appearance.GRUB_COLORS", etc.
"""

from __future__ import annotations

from src.ui.gtk_init import Gtk
from src.utils.config import (
    GRUB_COLOR_TO_HEX,
    GRUB_COLORS,
    GRUB_FONT_SIZES,
    GRUB_FONT_STYLES,
    GRUB_FONTS,
    GRUB_ICON_SPACINGS,
    GRUB_ITEM_HEIGHTS,
    GRUB_ITEM_PADDINGS,
    GRUB_ITEM_SPACINGS,
    GRUB_LABEL_LEFTS,
    GRUB_LABEL_TOPS,
    GRUB_MENU_HEIGHTS,
    GRUB_MENU_POSITIONS,
    GRUB_MENU_TOPS,
    GRUB_MENU_WIDTHS,
    GRUB_PROGRESS_BOTTOMS,
    GRUB_PROGRESS_COLORS,
    GRUB_PROGRESS_HEIGHTS,
    GRUB_PROGRESS_LEFTS,
    GRUB_PROGRESS_WIDTHS,
    GRUB_RESOLUTIONS,
    PREVIEW_WINDOW_HEIGHT,
    PREVIEW_WINDOW_WIDTH,
)

from .tab import AppearanceTab

__all__ = [
    "AppearanceTab",
    "Gtk",
    # constantes / mappings (utiles en prod + patchs tests)
    "GRUB_COLORS",
    "GRUB_COLOR_TO_HEX",
    "GRUB_RESOLUTIONS",
    "GRUB_MENU_POSITIONS",
    "GRUB_MENU_TOPS",
    "GRUB_MENU_WIDTHS",
    "GRUB_MENU_HEIGHTS",
    "GRUB_ITEM_HEIGHTS",
    "GRUB_ITEM_SPACINGS",
    "GRUB_ITEM_PADDINGS",
    "GRUB_LABEL_LEFTS",
    "GRUB_LABEL_TOPS",
    "GRUB_PROGRESS_BOTTOMS",
    "GRUB_PROGRESS_LEFTS",
    "GRUB_PROGRESS_WIDTHS",
    "GRUB_PROGRESS_HEIGHTS",
    "GRUB_ICON_SPACINGS",
    "GRUB_PROGRESS_COLORS",
    "GRUB_FONTS",
    "GRUB_FONT_SIZES",
    "GRUB_FONT_STYLES",
    "PREVIEW_WINDOW_HEIGHT",
    "PREVIEW_WINDOW_WIDTH",
]
