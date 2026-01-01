"""Widgets/factories pour l'onglet Apparence.

Responsabilité: créer des dropdowns GTK (couleurs, pourcentages, valeurs).
"""

from __future__ import annotations

from typing import Any


def create_percentage_dropdown(gtk_module: Any, options: list, default: str):
    """Create a dropdown for percentage selection."""
    model = gtk_module.StringList()
    for _value, label in options:
        model.append(label)

    dropdown = gtk_module.DropDown(model=model)
    dropdown.set_enable_search(False)

    for idx, (value, _) in enumerate(options):
        if value == default:
            dropdown.set_selected(idx)
            break

    return dropdown


def create_simple_dropdown(gtk_module: Any, options: list, default: str):
    """Create a simple dropdown from a list of options."""
    model = gtk_module.StringList()

    for item in options:
        if isinstance(item, tuple):
            model.append(item[1] if len(item) > 1 else str(item[0]))
        else:
            model.append(str(item))

    dropdown = gtk_module.DropDown(model=model)
    dropdown.set_enable_search(False)

    for idx, item in enumerate(options):
        value = item[0] if isinstance(item, tuple) else item
        if str(value) == str(default):
            dropdown.set_selected(idx)
            break

    return dropdown


def get_dropdown_value(dropdown, options: list) -> str:
    """Get selected value from dropdown."""
    idx = dropdown.get_selected()
    if 0 <= idx < len(options):
        item = options[idx]
        return item[0] if isinstance(item, tuple) else str(item)
    return ""


def select_from_dropdown(dropdown, value: str, options: list) -> None:
    """Select an item in dropdown by value."""
    for idx, (opt_value, _) in enumerate(options):
        if opt_value == value:
            dropdown.set_selected(idx)
            return
    dropdown.set_selected(0)


def select_from_simple_dropdown(dropdown, value: str, options: list) -> None:
    """Select an item in simple dropdown by value."""
    for idx, item in enumerate(options):
        opt_value = item[0] if isinstance(item, tuple) else item
        if str(opt_value) == str(value):
            dropdown.set_selected(idx)
            return
    dropdown.set_selected(0)


def create_color_dropdown(gtk_module: Any, colors: list, default: str, *, color_to_hex: dict):
    """Dropdown de couleur avec un carré (swatch) discret.

    Le modèle stocke les *valeurs* GRUB (ex: "light-gray"). L'affichage est un
    swatch carré (24x24) pour rester compact.
    """
    color_values = [value for value, _ in colors]
    color_labels = dict(colors)

    model = gtk_module.StringList()
    for value in color_values:
        model.append(value)

    dropdown = gtk_module.DropDown(model=model)
    dropdown.set_enable_search(False)

    factory = gtk_module.SignalListItemFactory()

    def setup_func(_factory, list_item):
        swatch = gtk_module.DrawingArea()
        swatch.set_content_width(24)
        swatch.set_content_height(24)
        swatch.set_margin_top(2)
        swatch.set_margin_bottom(2)
        swatch.set_margin_start(2)
        swatch.set_margin_end(2)
        list_item.set_child(swatch)

    def bind_func(_factory, list_item):
        string_obj = list_item.get_item()
        swatch = list_item.get_child()
        if not string_obj or not swatch:
            return

        value = string_obj.get_string()
        hex_color = color_to_hex.get(value, "#aaaaaa")
        label = color_labels.get(value, value)

        def draw_func(_area, cr, width, height, color_hex=hex_color):
            r = int(color_hex[1:3], 16) / 255
            g = int(color_hex[3:5], 16) / 255
            b = int(color_hex[5:7], 16) / 255

            cr.set_source_rgb(r, g, b)
            cr.rectangle(1, 1, width - 2, height - 2)
            cr.fill()

            cr.set_source_rgb(0.35, 0.35, 0.35)
            cr.set_line_width(1)
            cr.rectangle(0.5, 0.5, width - 1, height - 1)
            cr.stroke()

        swatch.set_draw_func(draw_func)
        swatch.set_tooltip_text(label)

    factory.connect("setup", setup_func)
    factory.connect("bind", bind_func)
    dropdown.set_list_factory(factory)
    dropdown.set_factory(factory)

    for idx, value in enumerate(color_values):
        if value == default:
            dropdown.set_selected(idx)
            break

    return dropdown
