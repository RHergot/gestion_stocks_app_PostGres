#!/usr/bin/env python3
"""
Script de test pour l'interface utilisateur des commandes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from APP.services.db import Database
from APP.services.commande_service import get_all_commandes_clean
from APP.views.commande_view import CommandeView

class TestMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test - Gestion des Commandes")
        self.setGeometry(100, 100, 1400, 900)
        
        # Connexion à la base de données
        self.db = Database()
        try:
            self.db.connect()
            print("✅ Connexion à la base de données réussie")
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            sys.exit(1)
        
        # Récupération des données
        try:
            commandes = get_all_commandes_clean(self.db)
            print(f"✅ {len(commandes)} commandes chargées")
        except Exception as e:
            print(f"❌ Erreur lors du chargement des commandes: {e}")
            commandes = []
        
        # Création de la vue
        self.commande_view = CommandeView(commandes, self.db, self)
        self.setCentralWidget(self.commande_view)
        
        print("✅ Interface utilisateur initialisée")
        print("\nInstructions:")
        print("1. Sélectionnez une commande dans la liste")
        print("2. Cliquez sur 'Modifier' pour ouvrir le dialog")
        print("3. Testez les boutons de transition de statut")
        print("4. Testez la fonction de copie et d'annulation")

def main():
    app = QApplication(sys.argv)
    
    # Style de l'application
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f5f5f5;
        }
        QPushButton {
            padding: 8px 16px;
            border: 1px solid #ccc;
            border-radius: 4px;
            background-color: #fff;
        }
        QPushButton:hover {
            background-color: #e6f3ff;
            border-color: #0078d4;
        }
        QPushButton:pressed {
            background-color: #cce7ff;
        }
        QPushButton:disabled {
            background-color: #f0f0f0;
            color: #999;
            border-color: #ddd;
        }
        QTableView {
            border: 1px solid #ddd;
            background-color: white;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #ccc;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
    """)
    
    window = TestMainWindow()
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    print("=== Test de l'interface utilisateur des commandes ===\n")
    sys.exit(main())