"""GRUB configuration file generator."""

from src.utils.logger import get_logger

logger = get_logger(__name__)


class GrubConfigGenerator:  # pylint: disable=too-few-public-methods
    """Generates new GRUB configuration content."""

    def generate(  # noqa: C901
        self,
        entries: dict[str, str],
        original_lines: list[str],
        hidden_entries: list[str] | None = None,
    ) -> str:
        """Generate new configuration content.

        Args:
            entries: Configuration key-value pairs
            original_lines: Original file lines to preserve comments/structure
            hidden_entries: List of entries to hide (prefix with #)

        Returns:
            New configuration content as string

        """
        hidden_set = set(hidden_entries or [])
        new_lines = []

        # Keys that must be exported to be visible to scripts
        keys_to_export = {"GRUB_COLOR_NORMAL", "GRUB_COLOR_HIGHLIGHT"}

        for line in original_lines:
            stripped = line.strip()

            # Preserve empty lines
            if not stripped:
                new_lines.append(line.rstrip())
                continue

            # If it's a comment, check if it might be a commented key
            if stripped.startswith("#") and "=" not in stripped:
                new_lines.append(line.rstrip())
                continue

            # Check if this line contains a key we need to update
            if "=" in stripped:
                key_part = stripped.split("=")[0].strip()

                # Handle export prefix and comments
                is_exported = False
                clean_key = key_part

                # Remove leading #
                if clean_key.startswith("#"):
                    clean_key = clean_key.lstrip("#").strip()

                # Remove export
                if clean_key.startswith("export "):
                    clean_key = clean_key[7:].strip()
                    is_exported = True

                if clean_key in entries:
                    # Replace with new value
                    value = entries[clean_key]

                    # Determine if we should export
                    should_export = is_exported or clean_key in keys_to_export
                    prefix = "export " if should_export else ""

                    new_line = f'{prefix}{clean_key}="{value}"'

                    # Hide entry if in hidden list
                    if clean_key in hidden_set:
                        new_line = f"#{new_line}"

                    new_lines.append(new_line)
                else:
                    # Keep original line
                    new_lines.append(line.rstrip())
            else:
                new_lines.append(line.rstrip())

        # Add any new entries that weren't in original file
        for key, value in entries.items():
            if not self._key_in_lines(key, original_lines):
                should_export = key in keys_to_export
                prefix = "export " if should_export else ""
                new_line = f'{prefix}{key}="{value}"'

                if key in hidden_set:
                    new_line = f"#{new_line}"
                new_lines.append(new_line)

        logger.debug(
            "Configuration generated",
            extra={"entries_count": len(entries), "lines_count": len(new_lines)},
        )

        return "\n".join(new_lines) + "\n"

    def _key_in_lines(self, key: str, lines: list[str]) -> bool:
        """Check if a key exists in the original lines.

        Args:
            key: Configuration key to check
            lines: Original configuration lines

        Returns:
            True if key found in lines

        """
        for line in lines:
            stripped = line.strip()

            if "=" not in stripped:
                continue

            key_part = stripped.split("=")[0].strip()

            # Normalize key part
            if key_part.startswith("#"):
                key_part = key_part.lstrip("#").strip()

            if key_part.startswith("export "):
                key_part = key_part[7:].strip()

            if key_part == key:
                return True

        return False
