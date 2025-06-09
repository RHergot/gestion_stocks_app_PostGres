from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QHBoxLayout
from PySide6.QtGui import QFont
import sys

# Association langue <-> clavier par défaut
LANG_KEYBOARD = {
    "Français": "AZERTY",
    "Anglais": "QWERTY",
    "Allemand": "QWERTZ",
    "Espagnol": "QWERTY",
    "Italien": "QWERTY"
}

class AccueilWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Page d'accueil - Services")
        self.setMinimumWidth(400)
        layout = QVBoxLayout()

        titre = QLabel("Bienvenue")
        titre.setFont(QFont("Segoe UI", 20, QFont.Bold))
        titre.setStyleSheet("color: #1A237E; margin-bottom: 16px;")
        layout.addWidget(titre)

        sous_titre = QLabel("Veuillez choisir un service :")
        sous_titre.setStyleSheet("color: #607d8b; margin-bottom: 24px;")
        layout.addWidget(sous_titre)

        # 1. Choix de la langue (le clavier est associé automatiquement)
        lang_layout = QHBoxLayout()
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["Français", "Anglais", "Allemand", "Espagnol", "Italien"])
        self.lang_combo.currentTextChanged.connect(self.update_keyboard)
        lang_layout.addWidget(QLabel("Langue :"))
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addWidget(QLabel("Clavier :"))
        self.kb_label = QLabel()
        lang_layout.addWidget(self.kb_label)
        layout.addLayout(lang_layout)
        self.update_keyboard(self.lang_combo.currentText())

        layout.addSpacing(20)

        # 2. Bouton Démarrage GMAO
        self.btn_gmao = QPushButton("Démarrer la GMAO")
        self.btn_gmao.setStyleSheet("background:#3f51b5; color:white; font-size:16px; padding:10px; border-radius:8px;")
        layout.addWidget(self.btn_gmao)
        self.btn_gmao.clicked.connect(self.start_gmao)

        # 3. Bouton Démarrage Gestion des stocks
        self.btn_stock = QPushButton("Démarrer la gestion des stocks")
        self.btn_stock.setStyleSheet("background:#3f51b5; color:white; font-size:16px; padding:10px; border-radius:8px;")
        layout.addWidget(self.btn_stock)
        self.btn_stock.clicked.connect(self.start_stock)

        self.setLayout(layout)

    def update_keyboard(self, lang):
        clavier = LANG_KEYBOARD.get(lang, "QWERTY")
        self.kb_label.setText(clavier)

    def get_selected_language(self):
        return self.lang_combo.currentText()

    def start_gmao(self):
        # Lance l'application GMAO dans un nouveau processus
        import subprocess
        import sys
        import os
        from PySide6.QtWidgets import QMessageBox
        lang = self.get_selected_language()
        # Chemin absolu vers le python du venv GMAO et le main.py
        gmao_python = r"C:\Users\Public\.vscode\Projets_Windsurf\gmao_app_PostGres\.venv\Scripts\python.exe"
        gmao_path = r"C:\Users\Public\.vscode\Projets_Windsurf\gmao_app_PostGres\main.py"
        if not os.path.isfile(gmao_python):
            QMessageBox.critical(self, "Erreur", f"Python du venv GMAO introuvable : {gmao_python}")
            return
        if not os.path.isfile(gmao_path):
            QMessageBox.critical(self, "Erreur", f"Fichier introuvable : {gmao_path}")
            return
        try:
            subprocess.Popen([gmao_python, gmao_path, "--lang", lang])
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de lancer la GMAO : {e}")
            return
        self.close()

    def start_stock(self):
        # Lance l'application Gestion de stock dans un nouveau processus
        import subprocess
        import sys
        import os
        from PySide6.QtWidgets import QMessageBox
        lang = self.get_selected_language()
        # Chemin absolu vers le python du venv Stock et le main.py
        stock_python = r"C:\Users\Public\.VSCode\Projets_Windsurf\Gestion_Stock_app_Postgres\.venv\Scripts\python.exe"
        stock_path = r"C:\Users\Public\.VSCode\Projets_Windsurf\Gestion_Stock_app_Postgres\src\main.py"
        if not os.path.isfile(stock_python):
            QMessageBox.critical(self, "Erreur", f"Python du venv Stock introuvable : {stock_python}")
            return
        if not os.path.isfile(stock_path):
            QMessageBox.critical(self, "Erreur", f"Fichier introuvable : {stock_path}")
            return
        try:
            subprocess.Popen([stock_python, stock_path, "--lang", lang])
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de lancer la gestion de stock : {e}")
            return
        self.close()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AccueilWindow()
    window.show()
    sys.exit(app.exec())
