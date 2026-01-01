import importlib
import sys


def test_gtk_init_adw_present():
    # Ensure clean state
    if "src.ui.gtk_init" in sys.modules:
        del sys.modules["src.ui.gtk_init"]

    # The conftest already sets up gi to succeed.
    # We just need to import and check.
    from src.ui import gtk_init

    assert gtk_init.HAS_ADW is True


def test_gtk_init_adw_missing():
    # Ensure clean state
    if "src.ui.gtk_init" in sys.modules:
        del sys.modules["src.ui.gtk_init"]

    # We need to patch gi.require_version to raise ImportError for Adw
    # Since gi is mocked in conftest, we need to find where it is.
    # sys.modules["gi"] is the mock.

    mock_gi = sys.modules["gi"]
    print(f"DEBUG: mock_gi id: {id(mock_gi)}")
    print(f"DEBUG: mock_gi.require_version id: {id(mock_gi.require_version)}")

    # Save original side effect if any
    original_side_effect = mock_gi.require_version.side_effect

    def side_effect(namespace, version):
        print(f"DEBUG: require_version called with {namespace}, {version}")
        if namespace == "Adw":
            print("DEBUG: Raising ImportError")
            raise ImportError("Adw not found")
        return None

    mock_gi.require_version.side_effect = side_effect

    try:
        import src.ui.gtk_init

        importlib.reload(src.ui.gtk_init)
        from src.ui import gtk_init

        assert gtk_init.HAS_ADW is False
    finally:
        # Restore
        mock_gi.require_version.side_effect = original_side_effect

        # Cleanup: remove module so other tests aren't affected
        if "src.ui.gtk_init" in sys.modules:
            del sys.modules["src.ui.gtk_init"]
