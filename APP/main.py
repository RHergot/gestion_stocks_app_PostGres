"""
Point d'entrée principal de l'application Gestion de Stock/GMAO (MVC).
Lance la fenêtre principale avec PySide6.
"""
import sys
import os
from PySide6.QtWidgets import QApplication

# Ajoute le dossier parent au PYTHONPATH si nécessaire
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from APP.main_window import MainWindow
from APP.services.db import Database
from PySide6.QtWidgets import QMessageBox

def main():
    app = QApplication(sys.argv)
    # Connexion à la base
    try:
        db = Database()
        db.connect()
    except Exception as e:
        # Affiche une erreur bloquante
        QMessageBox.critical(None, "Database Error", f"Could not connect to the database:\n{e}")
        sys.exit(1)
    window = MainWindow(db=db)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
