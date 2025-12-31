"""Point d'entrée de l'application."""
import sys
from src.ui.app import GrubApp
from src.utils.logger import setup_logging

if __name__ == "__main__":
    # Initialiser le logging
    setup_logging()
    app = GrubApp()
    sys.exit(app.run(sys.argv))
