"""Base class for custom dialogs."""

from src.ui.gtk_init import Gtk


class BaseDialog(Gtk.Window):
    """Base class for custom dialogs with common initialization."""

    def __init__(
        self,
        parent: Gtk.Window,
        title: str,
        default_size: tuple[int, int] = (400, 250),
    ) -> None:
        """Initialize base dialog.

        Args:
            parent: Parent window
            title: Dialog title
            default_size: Default window size (width, height)

        """
        super().__init__()
        self.set_title(title)
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_destroy_with_parent(True)
        self.set_default_size(*default_size)

    def create_main_box(self, spacing: int = 15) -> Gtk.Box:
        """Create and configure main vertical box.

        Args:
            spacing: Spacing between elements

        Returns:
            Configured vertical box with standard margins

        """
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=spacing)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        return main_box

    def create_message_label(self, message: str) -> Gtk.Label:
        """Create and configure message label.

        Args:
            message: Label text

        Returns:
            Configured label with wrapping

        """
        label = Gtk.Label(label=message)
        label.set_wrap(True)
        label.set_natural_wrap_mode(Gtk.NaturalWrapMode.WORD)
        return label

    def create_button_box(self, orientation: Gtk.Orientation = Gtk.Orientation.HORIZONTAL) -> Gtk.Box:
        """Create and configure button box.

        Args:
            orientation: Box orientation

        Returns:
            Configured button box

        """
        button_box = Gtk.Box(orientation=orientation, spacing=10)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(10)
        return button_box

    def finalize_dialog(self, main_box: Gtk.Box) -> None:
        """Set main box as child and display dialog.

        Args:
            main_box: Main content box

        """
        self.set_child(main_box)
        self.present()
