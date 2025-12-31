"""Tests pour le validateur GRUB."""

import os
import tempfile
import unittest

from src.core.validator import GrubValidationError, GrubValidator


class TestGrubValidator(unittest.TestCase):
    """Tests pour GrubValidator."""

    def setUp(self):
        """Configuration des tests."""
        self.validator = GrubValidator()

    def test_validate_timeout_valid(self):
        """Test validation timeout valide."""
        self.assertEqual(self.validator.validate_timeout("5"), 5)
        self.assertEqual(self.validator.validate_timeout("0"), 0)
        self.assertEqual(self.validator.validate_timeout("300"), 300)

    def test_validate_timeout_invalid(self):
        """Test validation timeout invalide."""
        with self.assertRaises(GrubValidationError):
            self.validator.validate_timeout("abc")
        with self.assertRaises(GrubValidationError):
            self.validator.validate_timeout("-1")
        with self.assertRaises(GrubValidationError):
            self.validator.validate_timeout("301")

    def test_validate_timeout_empty(self):
        """Test validation timeout vide."""
        self.assertEqual(self.validator.validate_timeout(""), 5)  # Valeur par défaut

    def test_validate_gfxmode_valid(self):
        """Test validation GFXMODE valide."""
        self.assertEqual(self.validator.validate_gfxmode("auto"), "auto")
        self.assertEqual(self.validator.validate_gfxmode("1920x1080"), "1920x1080")
        self.assertEqual(self.validator.validate_gfxmode("1024x768"), "1024x768")

    def test_validate_gfxmode_invalid(self):
        """Test validation GFXMODE invalide."""
        with self.assertRaises(GrubValidationError):
            self.validator.validate_gfxmode("invalid")
        with self.assertRaises(GrubValidationError):
            self.validator.validate_gfxmode("1920")  # Format incorrect

    def test_validate_gfxmode_empty(self):
        """Test validation GFXMODE vide."""
        self.assertEqual(self.validator.validate_gfxmode(""), "auto")

    def test_validate_file_path_valid_image(self):
        """Test validation chemin fichier image valide."""
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            result = self.validator.validate_file_path(tmp_path, self.validator.ALLOWED_IMAGE_EXTENSIONS)
            self.assertEqual(result, tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_validate_file_path_invalid_extension(self):
        """Test validation chemin fichier extension invalide."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with self.assertRaises(GrubValidationError):
                self.validator.validate_file_path(tmp_path, self.validator.ALLOWED_IMAGE_EXTENSIONS)
        finally:
            os.unlink(tmp_path)

    def test_validate_file_path_nonexistent(self):
        """Test validation chemin fichier inexistant."""
        with self.assertRaises(GrubValidationError):
            self.validator.validate_file_path("/nonexistent/file.png", self.validator.ALLOWED_IMAGE_EXTENSIONS)

    def test_validate_file_path_directory(self):
        """Test validation chemin répertoire au lieu de fichier."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaises(GrubValidationError):
                self.validator.validate_file_path(tmp_dir, self.validator.ALLOWED_IMAGE_EXTENSIONS)

    def test_validate_kernel_params_valid(self):
        """Test validation paramètres noyau valides."""
        valid_params = [
            "quiet splash",
            "nomodeset",
            "console=tty1",
            "root=UUID=12345678-1234-1234-1234-123456789012",
        ]
        for param in valid_params:
            with self.subTest(param=param):
                result = self.validator.validate_kernel_params(param)
                self.assertEqual(result, param)

    def test_validate_kernel_params_invalid(self):
        """Test validation paramètres noyau invalides."""
        invalid_params = [
            "quiet;splash",  # Point-virgule dans la chaîne
            "param@invalid",  # Caractère invalide
        ]
        for param in invalid_params:
            with self.subTest(param=param):
                with self.assertRaises(GrubValidationError):
                    self.validator.validate_kernel_params(param)

    def test_validate_all_valid(self):
        """Test validation complète valide."""
        entries = {
            "GRUB_TIMEOUT": "10",
            "GRUB_GFXMODE": "1920x1080",
            "GRUB_CMDLINE_LINUX_DEFAULT": "quiet splash",
        }

        # Ne devrait pas lever d'exception
        self.validator.validate_all(entries)

        # Vérifier que les valeurs ont été validées/transformées
        self.assertEqual(entries["GRUB_TIMEOUT"], "10")  # String
        self.assertEqual(entries["GRUB_GFXMODE"], "1920x1080")

    def test_validate_all_invalid_timeout(self):
        """Test validation complète avec timeout invalide."""
        entries = {"GRUB_TIMEOUT": "abc"}

        with self.assertRaises(GrubValidationError):
            self.validator.validate_all(entries)

    def test_validate_all_invalid_gfxmode(self):
        """Test validation complète avec GFXMODE invalide."""
        entries = {"GRUB_GFXMODE": "invalid"}

        with self.assertRaises(GrubValidationError):
            self.validator.validate_all(entries)

    def test_validate_all_with_file_paths(self):
        """Test validation complète avec chemins de fichiers."""
        # Créer des fichiers temporaires
        with (
            tempfile.NamedTemporaryFile(suffix=".png", delete=False) as img_tmp,
            tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as theme_tmp,
        ):

            img_path = img_tmp.name
            theme_path = theme_tmp.name

        try:
            entries = {"GRUB_BACKGROUND": img_path, "GRUB_THEME": theme_path}

            self.validator.validate_all(entries)

            self.assertEqual(entries["GRUB_BACKGROUND"], img_path)
            self.assertEqual(entries["GRUB_THEME"], theme_path)

        finally:
            os.unlink(img_path)
            os.unlink(theme_path)


if __name__ == "__main__":
    unittest.main()
