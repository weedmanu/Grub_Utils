"""Unit tests for theme management system.

Tests follow TDD principles with comprehensive coverage:
- Unit tests for each provider
- Integration tests for ThemeManager
- Edge case handling
"""

import unittest
import tempfile
import os
import shutil
from pathlib import Path

from src.core.config.theme_manager import (
    ThemeMode,
    ThemeConfig,
    StandardThemeProvider,
    CustomThemeProvider,
    CustomModifiedThemeProvider,
    ThemeManager,
)


class TestStandardThemeProvider(unittest.TestCase):
    """Test cases for StandardThemeProvider."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.theme_path = os.path.join(self.temp_dir, "theme.txt")
        self.backup_path = os.path.join(self.temp_dir, "theme.txt.bak")
        
        self.config = ThemeConfig(
            mode=ThemeMode.STANDARD,
            theme_path=self.theme_path,
            backup_path=self.backup_path,
        )
        self.provider = StandardThemeProvider(self.config)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_mode(self):
        """Test get_mode returns STANDARD."""
        self.assertEqual(self.provider.get_mode(), ThemeMode.STANDARD)
    
    def test_is_available_no_theme_file(self):
        """Test is_available returns True when no theme.txt exists."""
        self.assertTrue(self.provider.is_available())
    
    def test_is_available_with_theme_file(self):
        """Test is_available returns False when theme.txt exists."""
        with open(self.theme_path, "w") as f:
            f.write("test")
        self.assertFalse(self.provider.is_available())
    
    def test_activate_removes_theme(self):
        """Test activate removes theme.txt."""
        # Create theme file
        with open(self.theme_path, "w") as f:
            f.write("test content")
        
        success, message = self.provider.activate()
        
        self.assertTrue(success)
        self.assertFalse(os.path.exists(self.theme_path))
        self.assertTrue(os.path.exists(self.backup_path))
    
    def test_activate_no_theme_file(self):
        """Test activate succeeds when no theme file exists."""
        success, message = self.provider.activate()
        
        self.assertTrue(success)
        self.assertIn("already using", message.lower())
    
    def test_get_theme_content_none(self):
        """Test get_theme_content returns None for standard theme."""
        self.assertIsNone(self.provider.get_theme_content())


class TestCustomThemeProvider(unittest.TestCase):
    """Test cases for CustomThemeProvider."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.theme_path = os.path.join(self.temp_dir, "theme.txt")
        self.backup_path = os.path.join(self.temp_dir, "theme.txt.bak")
        
        self.config = ThemeConfig(
            mode=ThemeMode.CUSTOM,
            theme_path=self.theme_path,
            backup_path=self.backup_path,
        )
        self.provider = CustomThemeProvider(self.config)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_mode(self):
        """Test get_mode returns CUSTOM."""
        self.assertEqual(self.provider.get_mode(), ThemeMode.CUSTOM)
    
    def test_is_available_with_theme(self):
        """Test is_available returns True when theme.txt exists."""
        with open(self.theme_path, "w") as f:
            f.write("test")
        self.assertTrue(self.provider.is_available())
    
    def test_is_available_no_theme(self):
        """Test is_available returns False when no theme.txt."""
        self.assertFalse(self.provider.is_available())
    
    def test_deactivate_removes_theme(self):
        """Test deactivate removes theme.txt."""
        with open(self.theme_path, "w") as f:
            f.write("test content")
        
        success, message = self.provider.deactivate()
        
        self.assertTrue(success)
        self.assertFalse(os.path.exists(self.theme_path))
    
    def test_get_theme_content(self):
        """Test get_theme_content reads theme.txt."""
        test_content = "test theme content"
        with open(self.theme_path, "w") as f:
            f.write(test_content)
        
        content = self.provider.get_theme_content()
        
        self.assertEqual(content, test_content)
    
    def test_get_theme_content_no_file(self):
        """Test get_theme_content returns None when no file."""
        self.assertIsNone(self.provider.get_theme_content())


class TestCustomModifiedThemeProvider(unittest.TestCase):
    """Test cases for CustomModifiedThemeProvider."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.theme_path = os.path.join(self.temp_dir, "theme.txt")
        self.backup_path = os.path.join(self.temp_dir, "theme.txt.bak")
        self.modified_path = os.path.join(self.temp_dir, "theme_modif.txt")
        
        self.config = ThemeConfig(
            mode=ThemeMode.CUSTOM_MODIFIED,
            theme_path=self.theme_path,
            backup_path=self.backup_path,
        )
        self.provider = CustomModifiedThemeProvider(self.config, self.modified_path)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_mode(self):
        """Test get_mode returns CUSTOM_MODIFIED."""
        self.assertEqual(self.provider.get_mode(), ThemeMode.CUSTOM_MODIFIED)
    
    def test_is_available_with_file(self):
        """Test is_available returns True when modified theme exists."""
        with open(self.modified_path, "w") as f:
            f.write("test")
        self.assertTrue(self.provider.is_available())
    
    def test_is_available_no_file(self):
        """Test is_available returns False when no modified theme."""
        self.assertFalse(self.provider.is_available())
    
    def test_activate_copies_modified_theme(self):
        """Test activate copies modified theme to theme.txt."""
        test_content = "modified theme content"
        with open(self.modified_path, "w") as f:
            f.write(test_content)
        
        success, message = self.provider.activate()
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.theme_path))
        with open(self.theme_path, "r") as f:
            self.assertEqual(f.read(), test_content)
    
    def test_activate_no_modified_theme(self):
        """Test activate fails when modified theme doesn't exist."""
        success, message = self.provider.activate()
        
        self.assertFalse(success)
        self.assertIn("not found", message.lower())
    
    def test_get_theme_content(self):
        """Test get_theme_content reads modified theme."""
        test_content = "test modified content"
        with open(self.modified_path, "w") as f:
            f.write(test_content)
        
        content = self.provider.get_theme_content()
        
        self.assertEqual(content, test_content)


class TestThemeManager(unittest.TestCase):
    """Test cases for ThemeManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.theme_path = os.path.join(self.temp_dir, "theme.txt")
        self.backup_path = os.path.join(self.temp_dir, "theme.txt.bak")
        self.modified_path = os.path.join(self.temp_dir, "theme_modif.txt")
        
        self.config = ThemeConfig(
            mode=ThemeMode.STANDARD,
            theme_path=self.theme_path,
            backup_path=self.backup_path,
        )
        self.manager = ThemeManager(self.config)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_detect_standard_mode(self):
        """Test _detect_current_mode detects STANDARD."""
        mode = self.manager._detect_current_mode()
        self.assertEqual(mode, ThemeMode.STANDARD)
    
    def test_detect_custom_mode(self):
        """Test _detect_current_mode detects CUSTOM."""
        with open(self.theme_path, "w") as f:
            f.write("custom theme")
        
        mode = self.manager._detect_current_mode()
        self.assertEqual(mode, ThemeMode.CUSTOM)
    
    def test_get_current_mode(self):
        """Test get_current_mode."""
        current = self.manager.get_current_mode()
        self.assertEqual(current, ThemeMode.STANDARD)
    
    def test_get_available_modes_standard(self):
        """Test get_available_modes includes STANDARD."""
        modes = self.manager.get_available_modes()
        self.assertIn(ThemeMode.STANDARD, modes)
    
    def test_get_available_modes_with_custom(self):
        """Test get_available_modes includes CUSTOM when file exists."""
        with open(self.theme_path, "w") as f:
            f.write("custom")
        
        modes = self.manager.get_available_modes()
        self.assertIn(ThemeMode.CUSTOM, modes)
    
    def test_activate_mode(self):
        """Test activate_mode."""
        success, message = self.manager.activate_mode(ThemeMode.STANDARD)
        self.assertTrue(success)
    
    def test_get_provider(self):
        """Test get_provider returns correct provider."""
        provider = self.manager.get_provider(ThemeMode.STANDARD)
        self.assertIsNotNone(provider)
        self.assertEqual(provider.get_mode(), ThemeMode.STANDARD)
    
    def test_write_theme_content(self):
        """Test write_theme_content."""
        test_content = "new theme content"
        
        success, message = self.manager.write_theme_content(
            test_content, ThemeMode.CUSTOM
        )
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.theme_path))
        with open(self.theme_path, "r") as f:
            self.assertEqual(f.read(), test_content)
    
    def test_write_theme_content_standard_fails(self):
        """Test write_theme_content fails for STANDARD mode."""
        success, message = self.manager.write_theme_content(
            "content", ThemeMode.STANDARD
        )
        
        self.assertFalse(success)
        self.assertIn("standard", message.lower())


if __name__ == "__main__":
    unittest.main()
