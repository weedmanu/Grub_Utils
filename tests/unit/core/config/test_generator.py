"""Tests for the configuration generator module."""

import pytest

from src.core.config.generator import GrubConfigGenerator


class TestGrubConfigGenerator:
    """Tests for GrubConfigGenerator class."""

    @pytest.fixture
    def generator(self):
        """Fixture providing a GrubConfigGenerator instance."""
        return GrubConfigGenerator()

    def test_generate_update_existing(self, generator):
        """Test updating existing configuration keys."""
        original_lines = ["GRUB_TIMEOUT=5", "GRUB_DEFAULT=0"]
        entries = {"GRUB_TIMEOUT": "10", "GRUB_DEFAULT": "saved"}

        content = generator.generate(entries, original_lines)

        assert 'GRUB_TIMEOUT="10"' in content
        assert 'GRUB_DEFAULT="saved"' in content
        assert "GRUB_TIMEOUT=5" not in content

    def test_generate_add_new(self, generator):
        """Test adding new configuration keys."""
        original_lines = ["GRUB_TIMEOUT=5"]
        entries = {"GRUB_TIMEOUT": "5", "GRUB_THEME": "/boot/grub/themes/starfield/theme.txt"}

        content = generator.generate(entries, original_lines)

        assert 'GRUB_TIMEOUT="5"' in content
        assert 'GRUB_THEME="/boot/grub/themes/starfield/theme.txt"' in content

    def test_generate_preserve_structure(self, generator):
        """Test preserving comments and empty lines."""
        original_lines = ["# This is a comment", "", "GRUB_TIMEOUT=5", "# Another comment"]
        entries = {"GRUB_TIMEOUT": "10"}

        content = generator.generate(entries, original_lines)

        lines = content.splitlines()
        assert lines[0] == "# This is a comment"
        assert lines[1] == ""
        assert lines[2] == 'GRUB_TIMEOUT="10"'
        assert lines[3] == "# Another comment"

    def test_generate_hide_entries(self, generator):
        """Test hiding (commenting out) entries."""
        original_lines = ["GRUB_TIMEOUT=5"]
        entries = {"GRUB_TIMEOUT": "5"}
        hidden = ["GRUB_TIMEOUT"]

        content = generator.generate(entries, original_lines, hidden_entries=hidden)

        assert '#GRUB_TIMEOUT="5"' in content

    def test_generate_new_hidden_entry(self, generator):
        """Test adding a new hidden entry."""
        original_lines = []
        entries = {"GRUB_HIDDEN_TIMEOUT": "0"}
        hidden = ["GRUB_HIDDEN_TIMEOUT"]

        content = generator.generate(entries, original_lines, hidden_entries=hidden)

        assert '#GRUB_HIDDEN_TIMEOUT="0"' in content

    def test_generate_mixed_content(self, generator):
        """Test mixed scenario with updates, additions and comments."""
        original_lines = [
            "# Header",
            "GRUB_TIMEOUT=5",
            "GRUB_DISTRIBUTOR=`lsb_release -i -s 2> /dev/null || echo Debian`",
            "",
        ]
        entries = {"GRUB_TIMEOUT": "10", "GRUB_CMDLINE_LINUX": "quiet splash"}

        content = generator.generate(entries, original_lines)

        assert "# Header" in content
        assert 'GRUB_TIMEOUT="10"' in content
        assert "GRUB_DISTRIBUTOR=`lsb_release -i -s 2> /dev/null || echo Debian`" in content
        assert 'GRUB_CMDLINE_LINUX="quiet splash"' in content

    def test_key_in_lines_commented(self, generator):
        """Test detection of commented keys."""
        original_lines = ["#GRUB_TIMEOUT=5"]
        entries = {"GRUB_TIMEOUT": "10"}

        content = generator.generate(entries, original_lines)

        # Should update the commented line instead of appending
        assert 'GRUB_TIMEOUT="10"' in content
        assert content.count("GRUB_TIMEOUT") == 1

    def test_generate_empty_entries(self, generator):
        """Test generation with empty entries."""
        original_lines = ["GRUB_TIMEOUT=5", "# Comment"]
        entries = {}

        content = generator.generate(entries, original_lines)

        # Should keep original lines unchanged
        assert "GRUB_TIMEOUT=5" in content
        assert "# Comment" in content

    def test_generate_comment_only_lines(self, generator):
        """Test handling of comment-only lines without =."""
        original_lines = [
            "# This is a header comment",
            "## Another comment",
            "GRUB_TIMEOUT=5",
        ]
        entries = {"GRUB_TIMEOUT": "10"}

        content = generator.generate(entries, original_lines)
        lines = content.splitlines()

        assert lines[0] == "# This is a header comment"
        assert lines[1] == "## Another comment"
        assert lines[2] == 'GRUB_TIMEOUT="10"'

    def test_generate_line_without_equals(self, generator):
        """Test handling of lines without equals sign."""
        original_lines = [
            "GRUB_TIMEOUT=5",
            "Some random text without equals",
            "GRUB_DEFAULT=0",
        ]
        entries = {"GRUB_TIMEOUT": "10", "GRUB_DEFAULT": "saved"}

        content = generator.generate(entries, original_lines)

        assert 'GRUB_TIMEOUT="10"' in content
        assert 'GRUB_DEFAULT="saved"' in content
        assert "Some random text without equals" in content

    def test_generate_multiple_new_entries(self, generator):
        """Test adding multiple new entries not in original."""
        original_lines = ["GRUB_TIMEOUT=5"]
        entries = {
            "GRUB_TIMEOUT": "5",
            "NEW_KEY1": "value1",
            "NEW_KEY2": "value2",
            "NEW_KEY3": "value3",
        }

        content = generator.generate(entries, original_lines)

        assert 'NEW_KEY1="value1"' in content
        assert 'NEW_KEY2="value2"' in content
        assert 'NEW_KEY3="value3"' in content

    def test_generate_hide_multiple_entries(self, generator):
        """Test hiding multiple entries."""
        original_lines = ["KEY1=value1", "KEY2=value2"]
        entries = {"KEY1": "new1", "KEY2": "new2", "KEY3": "new3"}
        hidden = ["KEY1", "KEY3"]

        content = generator.generate(entries, original_lines, hidden_entries=hidden)

        assert '#KEY1="new1"' in content
        assert 'KEY2="new2"' in content
        assert '#KEY3="new3"' in content

    def test_generator_adds_export_for_colors(self, generator):
        """Ensure generator prefixes color variables with export."""
        entries = {
            "GRUB_COLOR_NORMAL": "light-gray/black",
            "GRUB_COLOR_HIGHLIGHT": "black/light-gray",
            "GRUB_TIMEOUT": "5",
        }
        content = generator.generate(entries, [])
        assert 'export GRUB_COLOR_NORMAL="light-gray/black"' in content
        assert 'export GRUB_COLOR_HIGHLIGHT="black/light-gray"' in content
        assert 'GRUB_TIMEOUT="5"' in content
        assert "export GRUB_TIMEOUT" not in content

    def test_generator_preserves_existing_export(self, generator):
        """Keep existing export prefix when present."""
        entries = {"MY_CUSTOM_VAR": "value"}
        content = generator.generate(entries, ['export MY_CUSTOM_VAR="old_value"'])
        assert 'export MY_CUSTOM_VAR="value"' in content

    def test_generator_handles_commented_export(self, generator):
        """Uncomment and export variables that were commented out."""
        entries = {"GRUB_COLOR_NORMAL": "white/black"}
        content = generator.generate(entries, ['#export GRUB_COLOR_NORMAL="light-gray/black"'])
        assert 'export GRUB_COLOR_NORMAL="white/black"' in content
        assert "#export GRUB_COLOR_NORMAL" not in content

    def test_generator_handles_hidden_export(self, generator):
        """Support hiding exported variables when requested."""
        entries = {"GRUB_COLOR_NORMAL": "white/black"}
        content = generator.generate(entries, [], ["GRUB_COLOR_NORMAL"])
        assert '#export GRUB_COLOR_NORMAL="white/black"' in content
