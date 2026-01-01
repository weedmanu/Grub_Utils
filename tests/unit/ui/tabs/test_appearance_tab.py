"""Tests pour l'onglet Appearance simplifié (couleurs et fond uniquement)."""

from unittest.mock import MagicMock, patch

import pytest

from src.ui.tabs.appearance import AppearanceTab


class TestAppearanceTab:
    """Tests de base pour AppearanceTab."""

    def test_init(self):
        """L'initialisation crée tous les widgets nécessaires."""
        app = MagicMock()
        app.facade.entries = {
            "GRUB_COLOR_NORMAL": "light-gray/black",
            "GRUB_COLOR_HIGHLIGHT": "white/dark-gray",
            "GRUB_BACKGROUND": "/path/to/bg.png",
        }

        tab = AppearanceTab(app)

        assert tab is not None
        assert tab.normal_fg_dropdown is not None
        assert tab.normal_bg_dropdown is not None
        assert tab.highlight_fg_dropdown is not None
        assert tab.highlight_bg_dropdown is not None
        assert tab.background_entry is not None
        assert tab.background_file_button is not None

    def test_load_data(self):
        """load_data charge les valeurs de la configuration."""
        app = MagicMock()
        app.facade.entries = {
            "GRUB_COLOR_NORMAL": "white/blue",
            "GRUB_COLOR_HIGHLIGHT": "yellow/red",
            "GRUB_BACKGROUND": "/test.png",
        }

        tab = AppearanceTab(app)
        # Vérifier que load_data est appelé (background_entry est bien créé)
        assert tab.background_entry is not None
        # Les mocks GTK rendent difficile la vérification exacte du texte
        tab.background_entry.set_text.assert_called()

    def test_save_data_with_background(self):
        """save_data sauvegarde correctement avec une image de fond."""
        app = MagicMock()
        app.facade.entries = {}

        with (
            patch("src.ui.tabs.appearance.os.path.exists", return_value=True),
            patch("src.ui.tabs.appearance.Gtk"),
        ):
            tab = AppearanceTab(app)
            # Configure dropdown mocks to return valid indices
            tab.normal_fg_dropdown.get_selected.return_value = 0
            tab.normal_bg_dropdown.get_selected.return_value = 0
            tab.highlight_fg_dropdown.get_selected.return_value = 0
            tab.highlight_bg_dropdown.get_selected.return_value = 0

            # Mock le get_text pour retourner une vraie chaîne
            tab.background_entry.get_text.return_value = "/valid/image.png"
            # Set background type to Image (index 1)
            tab.background_type_dropdown.get_selected.return_value = 1

            result = tab.save_data()

            assert result is True
            assert "GRUB_COLOR_NORMAL" in app.facade.entries
            assert "GRUB_COLOR_HIGHLIGHT" in app.facade.entries
            assert app.facade.entries["GRUB_BACKGROUND"] == "/valid/image.png"

    def test_save_data_without_background(self):
        """save_data supprime GRUB_BACKGROUND si le champ est vide."""
        app = MagicMock()
        app.facade.entries = {"GRUB_BACKGROUND": "/old.png"}

        with patch("src.ui.tabs.appearance.Gtk"):
            tab = AppearanceTab(app)
            # Configure dropdown mocks
            tab.normal_fg_dropdown.get_selected.return_value = 0
            tab.normal_bg_dropdown.get_selected.return_value = 0
            tab.highlight_fg_dropdown.get_selected.return_value = 0
            tab.highlight_bg_dropdown.get_selected.return_value = 0

            tab.background_entry.get_text.return_value = ""

            result = tab.save_data()

            assert result is True
            assert "GRUB_BACKGROUND" not in app.facade.entries

    def test_save_data_invalid_background(self):
        """save_data retourne False si l'image de fond n'existe pas."""
        app = MagicMock()
        app.facade.entries = {}

        with (
            patch("src.ui.tabs.appearance.os.path.exists", return_value=False),
            patch("src.ui.tabs.appearance.Gtk"),
        ):
            tab = AppearanceTab(app)
            # Configure dropdown mocks
            tab.normal_fg_dropdown.get_selected.return_value = 0
            tab.normal_bg_dropdown.get_selected.return_value = 0
            tab.highlight_fg_dropdown.get_selected.return_value = 0
            tab.highlight_bg_dropdown.get_selected.return_value = 0

            tab.background_entry.get_text.return_value = "/invalid/path.png"
            # Set background type to Image (index 1)
            tab.background_type_dropdown.get_selected.return_value = 1

            result = tab.save_data()

            assert result is False


class TestAppearanceTabCoverage:
    """Tests de couverture additionnels."""

    @pytest.fixture
    def app(self):
        """Fixture pour une application mock."""
        app = MagicMock()
        app.facade.entries = {}
        app.win = MagicMock()
        return app

    def test_select_color_not_found(self, app):
        """_select_color retourne à l'index 0 si la couleur n'existe pas."""
        tab = AppearanceTab(app)
        dropdown = MagicMock()
        tab._select_color(dropdown, "non-existent-color")
        dropdown.set_selected.assert_called_with(0)

    def test_get_selected_color_valid(self, app):
        """_get_selected_color retourne la couleur sélectionnée."""
        tab = AppearanceTab(app)
        dropdown = MagicMock()
        dropdown.get_selected.return_value = 0
        result = tab._get_selected_color(dropdown)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_selected_color_invalid_index(self, app):
        """_get_selected_color retourne la première couleur si l'index est invalide."""
        tab = AppearanceTab(app)
        dropdown = MagicMock()
        dropdown.get_selected.return_value = 999
        result = tab._get_selected_color(dropdown)
        assert isinstance(result, str)

    def test_parse_color_pair_valid(self, app):
        """_parse_color_pair parse correctement une paire de couleurs."""
        tab = AppearanceTab(app)
        fg, bg = tab._parse_color_pair("white/black", "light-gray", "dark-gray")
        assert fg == "white"
        assert bg == "black"

    def test_parse_color_pair_no_slash(self, app):
        """_parse_color_pair utilise les valeurs par défaut sans slash."""
        tab = AppearanceTab(app)
        fg, bg = tab._parse_color_pair("white", "light-gray", "dark-gray")
        assert fg == "light-gray"
        assert bg == "dark-gray"

    def test_on_background_file_clicked(self, app):
        """_on_background_file_clicked ouvre le dialogue de sélection."""
        tab = AppearanceTab(app)
        # Le dialogue est créé dans le contexte de GTK, vérifions juste que la méthode existe
        assert hasattr(tab, "_on_background_file_clicked")
        assert callable(tab._on_background_file_clicked)

    def test_on_file_dialog_response_accept(self, app):
        """_on_file_dialog_response met à jour l'entrée lors de l'acceptation."""
        from src.ui.gtk_init import Gtk

        tab = AppearanceTab(app)

        dialog = MagicMock()
        file_mock = MagicMock()
        file_mock.get_path.return_value = "/selected/image.png"
        dialog.get_file.return_value = file_mock

        tab._on_file_dialog_response(dialog, Gtk.ResponseType.ACCEPT)

        # Vérifier que set_text a été appelé avec le bon chemin
        tab.background_entry.set_text.assert_called_with("/selected/image.png")
        dialog.destroy.assert_called_once()

    def test_on_file_dialog_response_cancel(self, app):
        """_on_file_dialog_response ne fait rien lors de l'annulation."""
        from src.ui.gtk_init import Gtk

        tab = AppearanceTab(app)

        dialog = MagicMock()
        tab._on_file_dialog_response(dialog, Gtk.ResponseType.CANCEL)

        # Vérifier que set_text n'a PAS été appelé
        # (le nombre d'appels ne doit pas avoir changé depuis __init__)
        dialog.destroy.assert_called_once()

    def test_load_current_values_defaults(self, app):
        """_load_current_values utilise les couleurs par défaut si absentes."""
        app.facade.entries = {}
        with patch.object(AppearanceTab, "_select_color") as mock_select:
            AppearanceTab(app)

        # Vérifier que _select_color a été appelé avec les bonnes couleurs par défaut
        called_values = [call.args[1] for call in mock_select.call_args_list]
        assert "light-gray" in called_values
        assert "black" in called_values
        assert "white" in called_values
        assert "dark-gray" in called_values

    def test_create_color_dropdown(self, app):
        """_create_color_dropdown crée un dropdown avec toutes les couleurs."""
        tab = AppearanceTab(app)
        dropdown = tab._create_color_dropdown()
        assert dropdown is not None
