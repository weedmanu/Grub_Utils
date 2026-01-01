"""GTK initialization and imports.

This module handles all gi.require_version() calls and GTK imports
in one place to comply with import position rules (E402).
"""

# ruff: noqa: E402
# pylint: disable=wrong-import-position

import gi

# Set GTK versions before importing
gi.require_version("Gtk", "4.0")
gi.require_version("GLib", "2.0")

try:
    gi.require_version("Adw", "1")
    from gi.repository import Adw

    HAS_ADW = True
except ImportError:
    HAS_ADW = False

from gi.repository import GLib, Gtk  # noqa: E402

__all__ = ["Gtk", "GLib", "Adw", "HAS_ADW"]
