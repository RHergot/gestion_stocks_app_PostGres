#!/usr/bin/env python3
"""
Script de test simple pour vérifier l'affichage des boutons dans le dialog
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QPushButton
from APP.services.db import Database
from APP.models.commande_repository import CommandeRepository
from APP.views.commande_dialog import CommandeDialog

def test_dialog_buttons():
    """Test simple pour vérifier l'affichage des boutons"""
    
    app = QApplication(sys.argv)
    
    # Connexion à la base de données
    db = Database()
    try:
        db.connect()
        print("✅ Connexion à la base de données réussie")
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return
    
    # Récupérer une commande existante
    repo = CommandeRepository(db)
    commandes = repo.get_all_commandes()
    
    if not commandes:
        print("❌ Aucune commande trouvée")
        return
    
    commande_test = commandes[0]  # Prendre la première commande
    print(f"✅ Commande de test: ID={commande_test['id_commande']}, Statut={commande_test['statut']}")
    
    # Test 1: Dialog en mode création (nouvelle commande)
    print("\n=== Test 1: Mode création ===")
    dialog_creation = CommandeDialog(db, parent=None)
    print(f"is_editing = {dialog_creation.is_editing}")
    print(f"Boutons de statut créés: {hasattr(dialog_creation, 'status_widget')}")
    if hasattr(dialog_creation, 'status_widget'):
        print(f"Widget de statut visible: {dialog_creation.status_widget.isVisible()}")
    
    # Test 2: Dialog en mode édition (commande existante)
    print("\n=== Test 2: Mode édition ===")
    dialog_edition = CommandeDialog(db, commande_test, parent=None)
    print(f"is_editing = {dialog_edition.is_editing}")
    print(f"Boutons de statut créés: {hasattr(dialog_edition, 'status_widget')}")
    if hasattr(dialog_edition, 'status_widget'):
        print(f"Widget de statut visible: {dialog_edition.status_widget.isVisible()}")
        print(f"Nombre de boutons dans le layout: {dialog_edition.status_layout.count()}")
        
        # Vérifier chaque bouton
        boutons = ['confirmer_btn', 'envoyer_btn', 'livrer_btn', 'copier_btn', 'annuler_btn']
        for nom_bouton in boutons:
            if hasattr(dialog_edition, nom_bouton):
                bouton = getattr(dialog_edition, nom_bouton)
                print(f"  - {nom_bouton}: Existe={True}, Enabled={bouton.isEnabled()}, Visible={bouton.isVisible()}")
            else:
                print(f"  - {nom_bouton}: Existe={False}")
    
    # Afficher le dialog pour test visuel
    print(f"\n=== Affichage du dialog en mode édition ===")
    print("Vérifiez visuellement si les boutons de statut apparaissent...")
    dialog_edition.show()
    
    # Attendre que l'utilisateur ferme le dialog
    result = dialog_edition.exec()
    print(f"Dialog fermé avec le résultat: {result}")
    
    db.conn.close()

if __name__ == "__main__":
    test_dialog_buttons()