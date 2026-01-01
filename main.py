"""Point d'entrée de l'application."""

import argparse
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


def main(argv: list[str] | None = None) -> int:
    """Point d'entrée principal.

    Args:
        argv: Arguments de ligne de commande.

    Returns:
        Code de sortie.

    """
    if argv is None:
        argv = sys.argv

    # Parser les arguments
    parser = argparse.ArgumentParser(description="GRUB Customizer")
    parser.add_argument("--verbose", action="store_true", help="Activer les logs d'information")
    parser.add_argument("--debug", action="store_true", help="Activer les logs de débogage détaillés")
    args, remaining = parser.parse_known_args(argv[1:])

    if os.geteuid() != 0 and os.environ.get("GRUB_UTILS_ELEVATED") != "1":
        _relaunch_with_pkexec(argv)

    # Déterminer le niveau de log (debug > verbose > normal)
    if args.debug:
        log_level = "debug"
    elif args.verbose:
        log_level = "verbose"
    else:
        log_level = "normal"

    # Initialiser le logging avec le niveau approprié
    setup_logging(log_level=log_level)

    # Initialiser le conteneur DI
    container = get_application_container()
    _ = container

    # Obtenir l'app depuis le conteneur
    app = GrubApp()
    # Passer seulement les arguments restants à GTK
    return app.run([argv[0]] + remaining)


if __name__ == "__main__":
    raise SystemExit(main())
