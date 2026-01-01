"""Theme management system for GRUB customization.

This module implements a theme management system following SOLID principles:
- Single Responsibility: Each class has one reason to change
- Open/Closed: Open for extension, closed for modification
- Liskov Substitution: All theme modes are interchangeable
- Interface Segregation: Minimal required interfaces
- Dependency Inversion: Depends on abstractions, not concretions
"""

import os
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ThemeMode(Enum):
    """Theme operating modes."""

    STANDARD = "standard"  # Default GRUB theme (no custom theme.txt)
    CUSTOM = "custom"  # Custom theme.txt
    CUSTOM_MODIFIED = "custom_modified"  # Modified custom theme.txt


@dataclass(frozen=True)
class ThemeConfig:
    """Theme configuration data (immutable)."""

    mode: ThemeMode
    theme_path: str = "/boot/grub/themes/custom/theme.txt"
    backup_path: str = "/boot/grub/themes/custom/theme.txt.bak"


class IThemeProvider(ABC):
    """Interface for theme providers.

    Defines contract for different theme modes.
    """

    @abstractmethod
    def get_mode(self) -> ThemeMode:
        """Get the theme mode."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if theme is available/active."""

    @abstractmethod
    def activate(self) -> tuple[bool, str]:
        """Activate this theme mode.

        Returns:
            Tuple of (success: bool, message: str)

        """

    @abstractmethod
    def deactivate(self) -> tuple[bool, str]:
        """Deactivate this theme mode.

        Returns:
            Tuple of (success: bool, message: str)

        """

    @abstractmethod
    def get_theme_content(self) -> str | None:
        """Get theme content if available.

        Returns:
            Theme content string or None

        """


class StandardThemeProvider(IThemeProvider):
    """Provides standard GRUB theme (no custom theme.txt).

    Single Responsibility: Only handles standard theme state.
    """

    def __init__(self, config: ThemeConfig):
        """Initialize standard theme provider.

        Args:
            config: Theme configuration

        """
        self.config = config

    def get_mode(self) -> ThemeMode:
        """Get theme mode."""
        return ThemeMode.STANDARD

    def is_available(self) -> bool:
        """Check if standard theme is active (no custom theme.txt exists)."""
        return not os.path.exists(self.config.theme_path)

    def activate(self) -> tuple[bool, str]:
        """Activate standard theme by removing custom theme.txt."""
        try:
            if os.path.exists(self.config.theme_path):
                # Backup before deletion
                if not os.path.exists(self.config.backup_path):
                    shutil.copy2(self.config.theme_path, self.config.backup_path)

                os.remove(self.config.theme_path)
                logger.info("Standard theme activated")
                return True, "Standard GRUB theme activated"

            return True, "Already using standard theme"

        except Exception as e:
            error_msg = f"Failed to activate standard theme: {e}"
            logger.error(error_msg)
            return False, error_msg

    def deactivate(self) -> tuple[bool, str]:
        """Deactivate standard theme (no-op)."""
        return True, "Standard theme cannot be deactivated"

    def get_theme_content(self) -> str | None:
        """Get content for standard theme (none)."""
        return None


class CustomThemeProvider(IThemeProvider):
    """Provides custom theme.txt.

    Single Responsibility: Handles custom theme file management.
    """

    def __init__(self, config: ThemeConfig):
        """Initialize custom theme provider.

        Args:
            config: Theme configuration

        """
        self.config = config

    def get_mode(self) -> ThemeMode:
        """Get theme mode."""
        return ThemeMode.CUSTOM

    def is_available(self) -> bool:
        """Check if custom theme exists."""
        return os.path.exists(self.config.theme_path)

    def activate(self) -> tuple[bool, str]:
        """Activate is implicit when theme.txt exists."""
        if self.is_available():
            return True, "Custom theme is active"
        return False, "Custom theme.txt not found"

    def deactivate(self) -> tuple[bool, str]:
        """Deactivate by removing theme.txt."""
        try:
            if os.path.exists(self.config.theme_path):
                os.remove(self.config.theme_path)
                logger.info("Custom theme deactivated")
                return True, "Custom theme deactivated"
            return True, "Custom theme already inactive"

        except Exception as e:
            error_msg = f"Failed to deactivate custom theme: {e}"
            logger.error(error_msg)
            return False, error_msg

    def get_theme_content(self) -> str | None:
        """Get content of custom theme.txt."""
        try:
            if self.is_available():
                with open(self.config.theme_path, encoding="utf-8") as f:
                    return f.read()
        except Exception as e:
            logger.error("Failed to read custom theme: %s", e)
        return None


class CustomModifiedThemeProvider(IThemeProvider):
    """Provides modified custom theme.

    This is a decorator-like provider that wraps custom theme
    and allows modifications without affecting the original.
    """

    def __init__(self, config: ThemeConfig, modified_path: str = None):
        """Initialize modified theme provider.

        Args:
            config: Theme configuration
            modified_path: Path to modified theme (default: theme_modif.txt)

        """
        self.config = config
        self.modified_path = modified_path or os.path.expanduser("~/Documents/GitHub/Grub_utils/theme_modif.txt")

    def get_mode(self) -> ThemeMode:
        """Get theme mode."""
        return ThemeMode.CUSTOM_MODIFIED

    def is_available(self) -> bool:
        """Check if modified theme exists."""
        return os.path.exists(self.modified_path)

    def activate(self) -> tuple[bool, str]:
        """Activate by copying modified theme to theme.txt."""
        try:
            if not self.is_available():
                return False, f"Modified theme not found at {self.modified_path}"

            # Create directory if needed
            os.makedirs(os.path.dirname(self.config.theme_path), exist_ok=True)

            # Backup original if exists
            if os.path.exists(self.config.theme_path) and not os.path.exists(self.config.backup_path):
                shutil.copy2(self.config.theme_path, self.config.backup_path)

            # Copy modified theme
            shutil.copy2(self.modified_path, self.config.theme_path)
            logger.info("Modified custom theme activated")
            return True, "Modified custom theme activated"

        except Exception as e:
            error_msg = f"Failed to activate modified theme: {e}"
            logger.error(error_msg)
            return False, error_msg

    def deactivate(self) -> tuple[bool, str]:
        """Deactivate by removing theme.txt."""
        try:
            if os.path.exists(self.config.theme_path):
                os.remove(self.config.theme_path)
                logger.info("Modified theme deactivated")
                return True, "Modified theme deactivated"
            return True, "Modified theme already inactive"

        except Exception as e:
            error_msg = f"Failed to deactivate modified theme: {e}"
            logger.error(error_msg)
            return False, error_msg

    def get_theme_content(self) -> str | None:
        """Get content of modified theme."""
        try:
            if self.is_available():
                with open(self.modified_path, encoding="utf-8") as f:
                    return f.read()
        except Exception as e:
            logger.error("Failed to read modified theme: %s", e)
        return None


class ThemeManager:
    """Central manager for theme operations.

    Single Responsibility: Orchestrates theme providers and state management.
    Dependency Inversion: Works with IThemeProvider abstractions.
    """

    def __init__(self, config: ThemeConfig):
        """Initialize theme manager.

        Args:
            config: Theme configuration

        """
        self.config = config
        self._providers = {
            ThemeMode.STANDARD: StandardThemeProvider(config),
            ThemeMode.CUSTOM: CustomThemeProvider(config),
            ThemeMode.CUSTOM_MODIFIED: CustomModifiedThemeProvider(config),
        }
        self._current_mode = self._detect_current_mode()

    def _detect_current_mode(self) -> ThemeMode:
        """Detect current active theme mode.

        Returns:
            Currently active theme mode

        """
        if not os.path.exists(self.config.theme_path):
            return ThemeMode.STANDARD

        # Check if it's the modified theme
        modified_provider = self._providers[ThemeMode.CUSTOM_MODIFIED]
        if modified_provider.is_available():
            try:
                current = self._providers[ThemeMode.CUSTOM].get_theme_content()
                modified = modified_provider.get_theme_content()
                if current and modified and current == modified:
                    return ThemeMode.CUSTOM_MODIFIED
            except Exception:
                pass

        return ThemeMode.CUSTOM

    def get_current_mode(self) -> ThemeMode:
        """Get currently active theme mode.

        Returns:
            Current theme mode

        """
        return self._detect_current_mode()

    def get_available_modes(self) -> list[ThemeMode]:
        """Get available theme modes.

        Returns:
            List of available theme modes

        """
        available: list[ThemeMode] = []
        for mode, provider in self._providers.items():
            # Standard mode is always available
            if mode == ThemeMode.STANDARD:
                available.append(mode)
            elif provider.is_available():
                available.append(mode)
        return available

    def get_provider(self, mode: ThemeMode) -> IThemeProvider | None:
        """Get provider for specific theme mode.

        Args:
            mode: Theme mode

        Returns:
            Provider instance or None

        """
        return self._providers.get(mode)

    def activate_mode(self, mode: ThemeMode) -> tuple[bool, str]:
        """Activate specific theme mode.

        Args:
            mode: Theme mode to activate

        Returns:
            Tuple of (success: bool, message: str)

        """
        provider = self.get_provider(mode)
        if not provider:
            return False, f"Unknown theme mode: {mode}"

        success, message = provider.activate()
        if success:
            self._current_mode = mode
            logger.info("Theme mode activated: %s", mode.value)

        return success, message

    def get_theme_content(self, mode: ThemeMode | None = None) -> str | None:
        """Get theme content for specific mode or current.

        Args:
            mode: Theme mode (default: current)

        Returns:
            Theme content or None

        """
        if mode is None:
            mode = self.get_current_mode()

        provider = self.get_provider(mode)
        if provider:
            return provider.get_theme_content()

        return None

    def write_theme_content(self, content: str, mode: ThemeMode) -> tuple[bool, str]:
        """Write theme content for specific mode.

        Args:
            content: Theme content to write
            mode: Target theme mode

        Returns:
            Tuple of (success: bool, message: str)

        """
        try:
            if mode == ThemeMode.STANDARD:
                return False, "Cannot write to standard theme"

            provider = self.get_provider(mode)
            if not provider:
                return False, f"Unknown theme mode: {mode}"

            # Write based on mode
            if mode == ThemeMode.CUSTOM:
                target_path = self.config.theme_path
            else:  # CUSTOM_MODIFIED
                target_path = provider.modified_path  # type: ignore

            os.makedirs(os.path.dirname(target_path), exist_ok=True)

            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info("Theme content written to %s", target_path)
            return True, "Theme written successfully"

        except Exception as e:
            error_msg = f"Failed to write theme content: {e}"
            logger.error(error_msg)
            return False, error_msg
