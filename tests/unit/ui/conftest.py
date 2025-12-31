import sys
from unittest.mock import MagicMock

# Base class for mocked Gtk widgets to avoid MagicMock inheritance issues
class MockWidget:
    def __init__(self, *args, **kwargs):
        self._mocks = {}
    def __getattr__(self, name):
        if name in self._mocks:
            return self._mocks[name]
        
        if name == "get_selected":
            res = lambda: 0
        elif name == "get_buffer":
            res = lambda: MagicMock()
        else:
            res = MagicMock()
        
        self._mocks[name] = res
        return res
    def connect(self, *args, **kwargs):
        return 0
    @classmethod
    def new_from_strings(cls, *args, **kwargs):
        return MockWidget()

    @classmethod
    def new_for_filename(cls, *args, **kwargs):
        return MockWidget()

class MockApplication:
    def __init__(self, application_id=None, flags=0, **kwargs):
        self.application_id = application_id
        self.flags = flags
    
    def connect(self, signal, handler):
        return 0
    
    def run(self, args):
        return 0

    def quit(self):
        pass

    def add_window(self, window):
        pass

    def set_accels_for_action(self, action, accels):
        pass

class MockLibrary(MagicMock):
    def __getattr__(self, name):
        if name[0].isupper():
            return MockWidget
        return super().__getattr__(name)

mock_gtk = MockLibrary()
mock_gtk.Application = MockApplication
mock_gtk.Orientation = MagicMock()
mock_gtk.Orientation.VERTICAL = 1
mock_gtk.Orientation.HORIZONTAL = 0
mock_gtk.Align = MagicMock()
mock_gtk.Align.START = 1
mock_gtk.Align.CENTER = 2
mock_gtk.StackTransitionType = MagicMock()
mock_gtk.StackTransitionType.SLIDE_LEFT_RIGHT = 1
mock_gtk.RevealerTransitionType = MagicMock()
mock_gtk.RevealerTransitionType.SLIDE_DOWN = 1
mock_gtk.ResponseType = MagicMock()
mock_gtk.ResponseType.OK = -5
mock_gtk.ResponseType.CANCEL = -6
mock_gtk.ResponseType.YES = -8
mock_gtk.ResponseType.NO = -9
mock_gtk.NaturalWrapMode = MagicMock()
mock_gtk.NaturalWrapMode.WORD = 1
mock_gtk.SelectionMode = MagicMock()
mock_gtk.SelectionMode.SINGLE = 1
mock_gtk.PolicyType = MagicMock()
mock_gtk.PolicyType.NEVER = 0
mock_gtk.PolicyType.AUTOMATIC = 1
mock_gtk.PolicyType.ALWAYS = 2
mock_gtk.STYLE_PROVIDER_PRIORITY_APPLICATION = 600

# Setup Adw mocks
mock_adw = MockLibrary()
mock_adw.Application = MockApplication

# Setup Gio mocks
mock_gio = MagicMock()
mock_gio.ApplicationFlags = MagicMock()
mock_gio.ApplicationFlags.FLAGS_NONE = 0
mock_gio.SimpleAction = MagicMock

# Setup GLib mocks
mock_glib = MagicMock()
mock_glib.idle_add = MagicMock()
mock_glib.timeout_add = MagicMock()
mock_glib.Error = Exception

# Register mocks
mock_gi = MagicMock()
mock_gi_repo = MagicMock()
mock_gi.repository = mock_gi_repo

mock_gi_repo.Gtk = mock_gtk
mock_gi_repo.Adw = mock_adw
mock_gi_repo.Gio = mock_gio
mock_gi_repo.GLib = mock_glib
mock_gi_repo.Gdk = MagicMock()

sys.modules["gi"] = mock_gi
sys.modules["gi.repository"] = mock_gi_repo
sys.modules["gi.repository.Gtk"] = mock_gtk
sys.modules["gi.repository.Adw"] = mock_adw
sys.modules["gi.repository.Gio"] = mock_gio
sys.modules["gi.repository.GLib"] = mock_glib
sys.modules["gi.repository.Gdk"] = MagicMock()
