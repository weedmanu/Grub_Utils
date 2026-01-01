"""Parsing et utilitaires theme.txt.

Responsabilité: lecture/parse du theme.txt et conversions couleur.
"""

from __future__ import annotations

import os
from typing import Any


def parse_theme_file(theme_path: str, logger: Any) -> dict:  # noqa: C901
    """Parse theme.txt file to extract configuration."""
    theme_values: dict[str, str] = {}

    try:
        if not os.path.exists(theme_path):
            return theme_values

        with open(theme_path, encoding="utf-8") as f:
            lines = f.readlines()

        in_boot_menu = False
        in_label = False
        in_progress = False

        for line in lines:
            line = line.strip()

            if line.startswith("+ boot_menu"):
                in_boot_menu = True
                in_label = False
                in_progress = False
                continue
            if line.startswith("+ label"):
                in_label = True
                in_boot_menu = False
                in_progress = False
                continue
            if line.startswith("+ progress_bar"):
                in_progress = True
                in_boot_menu = False
                in_label = False
                continue
            if line.startswith("}"):
                in_boot_menu = False
                in_label = False
                in_progress = False
                continue

            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"')

            if in_boot_menu:
                if key == "left":
                    theme_values["menu_left"] = value
                elif key == "top":
                    theme_values["menu_top"] = value
                elif key == "width":
                    theme_values["menu_width"] = value
                elif key == "height":
                    theme_values["menu_height"] = value
                elif key == "item_height":
                    theme_values["item_height"] = value
                elif key == "item_spacing":
                    theme_values["item_spacing"] = value
                elif key == "item_padding":
                    theme_values["item_padding"] = value
                elif key == "icon_spacing":
                    theme_values["icon_spacing"] = value
                elif key == "item_font":
                    theme_values["font_item"] = value
                elif key == "selected_item_font":
                    theme_values["font_item_highlight"] = value

            elif in_label:
                if key == "left":
                    theme_values["label_left"] = value
                elif key == "top":
                    theme_values["label_top"] = value
                elif key == "font":
                    theme_values["font_label"] = value

            elif in_progress:
                if key == "bottom":
                    theme_values["progress_bottom"] = value
                elif key == "border_color":
                    theme_values["progress_border"] = value
                elif key == "bar_color":
                    theme_values["progress_bar"] = value

    except Exception as exc:  # noqa: BLE001
        logger.warning("Erreur lors du parsing du theme.txt: %s", exc)

    return theme_values


def hex_to_color_name(hex_color: str, color_to_hex: dict[str, str]) -> str:
    """Convert hex color code to GRUB color name."""
    hex_color = hex_color.lower()
    for color_name, hex_value in color_to_hex.items():
        if hex_value.lower() == hex_color:
            return color_name
    return ""
