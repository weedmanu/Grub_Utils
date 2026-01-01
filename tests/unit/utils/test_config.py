import pytest

from src.utils.config import grub_color_to_hex


@pytest.mark.unit
def test_grub_color_to_hex():
    assert grub_color_to_hex("black") == "#000000"
    assert grub_color_to_hex("white") == "#ffffff"
    assert grub_color_to_hex("unknown") == "#aaaaaa"
    assert grub_color_to_hex("BLUE") == "#0000aa"
