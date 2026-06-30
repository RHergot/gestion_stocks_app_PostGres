"""
Point d'entrée principal de l'application Gestion de Stock/GMAO (MVC).
Lance la fenêtre principale avec PySide6.
"""
import sys
import os
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTranslator

# Configuration centralisée du logging (un seul point de config pour toute l'app)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

# Ajoute le dossier parent au PYTHONPATH si nécessaire
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from APP.main_window import MainWindow
from APP.services.db import Database
from PySide6.QtWidgets import QMessageBox
from APP.utils.i18n import AppConfig, Language, tr_mod

def main():
    app = QApplication(sys.argv)
    # Configure language and load translators if needed
    app_config = AppConfig()
    translators = []
    if app_config.language != Language.ENGLISH:
        lang_dir = f"{app_config.language.value}_translations"
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        translations_path = os.path.join(project_root, lang_dir)
        if os.path.isdir(translations_path):
            # Load every .qm file found in the language directory
            for name in sorted(os.listdir(translations_path)):
                if name.lower().endswith('.qm'):
                    translator = QTranslator()
                    qm_path = os.path.join(translations_path, name)
                    loaded = translator.load(qm_path)
                    # Optionally log via print (can be replaced by logger)
                    print(f"Loading translation: {qm_path} => {loaded}")
                    if loaded:
                        app.installTranslator(translator)
                        translators.append(translator)
        else:
            print(f"Translation directory not found: {translations_path}")
    # Prevent translators from being GC'ed
    app._translators = translators
    # Connexion à la base
    try:
        db = Database()
        db.connect()
    except Exception as e:
        # Affiche une erreur bloquante
        QMessageBox.critical(
            None,
            tr_mod("Main", "Database Error"),
            tr_mod("Main", "Could not connect to the database:\n{error}").format(error=e),
        )
        sys.exit(1)
    window = MainWindow(db=db)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
