#!/usr/bin/env python3
"""
Test du nouveau système de réception détaillée
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from APP.services.db import Database
from APP.services.commande_service import get_all_commandes_clean
from APP.views.commande_view import CommandeView

class TestReceptionWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test - Système de Réception Détaillée")
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
            print("\nCommandes disponibles pour test :")
            for cmd in commandes:
                statut = cmd['statut']
                if statut in ['Envoyee', 'Partielle']:
                    print(f"  🔄 {cmd['numero_commande']}: {statut} (peut être réceptionnée)")
                elif statut == 'Livree':
                    print(f"  ✅ {cmd['numero_commande']}: {statut} (terminée)")
                else:
                    print(f"  📝 {cmd['numero_commande']}: {statut}")
                
        except Exception as e:
            print(f"❌ Erreur lors du chargement des commandes: {e}")
            commandes = []
        
        # Création de la vue
        self.commande_view = CommandeView(commandes, self.db, self)
        self.setCentralWidget(self.commande_view)
        
        print("✅ Interface utilisateur initialisée")
        print("\n" + "="*60)
        print("INSTRUCTIONS POUR TESTER LE SYSTÈME DE RÉCEPTION")
        print("="*60)
        print("1. Sélectionnez une commande en statut 'Envoyee' ou 'Partielle'")
        print("2. Cliquez sur le bouton 'Livrer' (maintenant = 'Réceptionner')")
        print("3. Dans le dialog de réception :")
        print("   • Ajustez les quantités à réceptionner")
        print("   • Décochez 'Bon état' pour les pièces défectueuses")
        print("   • Ajoutez des commentaires si nécessaire")
        print("   • Cliquez 'Valider la réception'")
        print("4. Observez les changements de statut :")
        print("   • Partielle : si toutes les lignes ne sont pas complètes")
        print("   • Livree : si toutes les lignes sont complètes")
        print("5. Vous pouvez réceptionner plusieurs fois la même commande")
        print("="*60)

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
    
    window = TestReceptionWindow()
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    print("=== Test du système de réception détaillée ===\n")
    sys.exit(main())