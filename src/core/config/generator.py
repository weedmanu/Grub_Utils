"""GRUB configuration file generator."""

from src.utils.logger import get_logger

logger = get_logger(__name__)


class GrubConfigGenerator:  # pylint: disable=too-few-public-methods
    """Generates new GRUB configuration content."""

    def generate(
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
                clean_key = key_part.lstrip("#").strip()

                if clean_key in entries:
                    # Replace with new value
                    value = entries[clean_key]
                    new_line = f'{clean_key}="{value}"'

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
                new_line = f'{key}="{value}"'
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
            if stripped.startswith(f"{key}=") or stripped.startswith(f"#{key}="):
                return True
        return False
