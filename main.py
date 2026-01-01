"""Point d'entrée de l'application."""

import os
import subprocess
import sys
from typing import NoReturn

from src.core.setup import get_application_container
from src.ui.app import GrubApp
from src.utils.logger import setup_logging


def _relaunch_with_pkexec(argv: list[str]) -> NoReturn:
    """Relance l'application via pkexec pour obtenir les privilèges admin.

    Args:
        argv: Arguments de ligne de commande.

    """
    env_keys = (
        "DISPLAY",
        "WAYLAND_DISPLAY",
        "XDG_RUNTIME_DIR",
        "DBUS_SESSION_BUS_ADDRESS",
        "XAUTHORITY",
        "LANG",
        "LC_ALL",
    )
    env_args = [f"{key}={os.environ[key]}" for key in env_keys if key in os.environ]

    # Marqueur pour éviter une boucle de relance.
    env_args.append("GRUB_UTILS_ELEVATED=1")

    cmd = [
        "pkexec",
        "env",
        *env_args,
        sys.executable,
        os.path.abspath(__file__),
        *argv[1:],
    ]

    raise SystemExit(subprocess.call(cmd))


if __name__ == "__main__":
    if os.geteuid() != 0 and os.environ.get("GRUB_UTILS_ELEVATED") != "1":
        _relaunch_with_pkexec(sys.argv)

    # Initialiser le logging
    setup_logging()

    # Initialiser le conteneur DI
    container = get_application_container()

    # Obtenir l'app depuis le conteneur
    app = GrubApp()
    sys.exit(app.run(sys.argv))
