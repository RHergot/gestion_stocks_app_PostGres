#!/usr/bin/env python3
"""
Test des boutons de statut dans la vue tableau des commandes
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
        self.setWindowTitle("Test - Boutons de Statut dans Vue Commandes")
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
            
            # Afficher les statuts des commandes
            print("\nCommandes disponibles :")
            for cmd in commandes[:5]:  # Afficher les 5 premières
                print(f"  - {cmd['numero_commande']}: {cmd['statut']}")
                
        except Exception as e:
            print(f"❌ Erreur lors du chargement des commandes: {e}")
            commandes = []
        
        # Création de la vue
        self.commande_view = CommandeView(commandes, self.db, self)
        self.setCentralWidget(self.commande_view)
        
        print("✅ Interface utilisateur initialisée")
        print("\nInstructions:")
        print("1. Sélectionnez une commande dans la liste")
        print("2. Observez les boutons de statut qui s'activent/désactivent")
        print("3. Testez les transitions de statut avec les boutons")
        print("4. Les boutons disponibles dépendent du statut actuel :")
        print("   - Brouillon: Confirmer, Copier, Annuler")
        print("   - Validée: Envoyer, Copier, Annuler")
        print("   - Envoyée: Livrer, Copier, Annuler")
        print("   - Livrée: Copier seulement")
        print("   - Annulée: Copier seulement")

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
            min-width: 80px;
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
        QLabel {
            font-size: 12px;
        }
    """)
    
    window = TestMainWindow()
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    print("=== Test des boutons de statut dans la vue commandes ===\n")
    sys.exit(main())