"""GRUB menu parser for reading grub.cfg."""

import os
import re

from src.utils.config import GRUB_CFG_PATHS
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GrubMenuParser:  # pylint: disable=too-few-public-methods
    """Parses GRUB menu entries from grub.cfg."""

    # Pattern to match menu entries
    MENUENTRY_PATTERN = re.compile(r"menuentry\s+([\"'])(.+?)\1")
    SUBMENU_PATTERN = re.compile(r"submenu\s+([\"'])(.+?)\1")

    def __init__(self, grub_cfg_path: str | None = None):
        """Initialize the parser.

        Args:
            grub_cfg_path: Path to grub.cfg (auto-detected if None)

        """
        self.grub_cfg_path = grub_cfg_path or self._find_grub_cfg()

    def _find_grub_cfg(self) -> str:
        """Find grub.cfg in standard locations.

        Returns:
            Path to grub.cfg

        Raises:
            FileNotFoundError: If grub.cfg not found

        """
        # Keep the order from GRUB_CFG_PATHS.
        # Some systems can have both /boot/grub/grub.cfg and /boot/grub2/grub.cfg;
        # picking the newest file can select an unused grub.cfg and hide entries (ex: Windows).
        for path in GRUB_CFG_PATHS:
            if os.path.exists(path):
                # Use INFO so the selected path is visible even in normal mode.
                logger.info("Using grub.cfg at %s", path)
                return path

        raise FileNotFoundError("Could not find grub.cfg in standard locations")

    def parse_menu_entries(self) -> list[dict]:
        """Parse menu entries from grub.cfg.

        Returns:
            List of menu entry dictionaries with keys:
            - title: Entry title
            - linux: Linux kernel path (if present)
            - submenu: Whether this is a submenu

        Raises:
            OSError: If grub.cfg cannot be read

        """
        if not os.path.exists(self.grub_cfg_path):
            logger.warning("grub.cfg not found at %s", self.grub_cfg_path)
            return []

        try:
            with open(self.grub_cfg_path, encoding="utf-8") as f:
                content = f.read()

            entries = []
            brace_depth = 0
            submenu_depth = -1

            for line in content.splitlines():
                line = line.strip()

                # Check for submenu
                submenu_match = self.SUBMENU_PATTERN.search(line)
                if submenu_match:
                    entries.append(
                        {
                            "title": submenu_match.group(2),
                            "linux": "",
                            "submenu": True,
                        }
                    )
                    if submenu_depth == -1:
                        submenu_depth = brace_depth

                # Check for menuentry
                menuentry_match = self.MENUENTRY_PATTERN.search(line)
                if menuentry_match:
                    title = menuentry_match.group(2)
                    entries.append(
                        {
                            "title": title,
                            "linux": self._extract_linux_path(content, title),
                            "submenu": submenu_depth != -1,
                        }
                    )

                # Update brace depth
                brace_depth += line.count("{")
                brace_depth -= line.count("}")

                # Check if we exited the submenu
                if submenu_depth != -1 and brace_depth <= submenu_depth:
                    submenu_depth = -1

            logger.info("Menu entries parsed from %s: %d", self.grub_cfg_path, len(entries))
            return entries

        except OSError as e:
            logger.error("Failed to read grub.cfg: %s", e)
            raise

    def _extract_linux_path(self, content: str, title: str) -> str:
        """Extract Linux kernel path for a menu entry.

        Args:
            content: Full grub.cfg content
            title: Menu entry title

        Returns:
            Path to Linux kernel or empty string

        """
        # Simple extraction - look for "linux"/"linuxefi" line after menuentry.
        pattern = rf"menuentry\s+(?P<q>[\"']){re.escape(title)}(?P=q).*?\b(?:linux|linuxefi)\s+(\S+)"
        match = re.search(pattern, content, re.DOTALL)
        return match.group(2) if match else ""
