e #!/usr/bin/env python3
"""
Test rapide pour vérifier les boutons
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from APP.services.db import Database
from APP.models.commande_repository import CommandeRepository
from APP.views.commande_dialog import CommandeDialog

def test_quick():
    # Connexion à la base de données
    db = Database()
    try:
        db.connect()
        print("✅ Connexion réussie")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return
    
    # Récupérer une commande
    repo = CommandeRepository(db)
    commandes = repo.get_all_commandes()
    
    if not commandes:
        print("❌ Aucune commande")
        return
    
    commande = commandes[0]
    print(f"✅ Commande: {commande['numero_commande']} - {commande['statut']}")
    
    # Créer le dialog
    dialog = CommandeDialog(db, commande)
    
    # Vérifier les attributs
    print(f"is_editing: {dialog.is_editing}")
    print(f"status_widget existe: {hasattr(dialog, 'status_widget')}")
    print(f"status_label existe: {hasattr(dialog, 'status_label')}")
    print(f"confirmer_btn existe: {hasattr(dialog, 'confirmer_btn')}")
    
    if hasattr(dialog, 'status_widget'):
        print(f"status_widget visible: {dialog.status_widget.isVisible()}")
    
    if hasattr(dialog, 'confirmer_btn'):
        print(f"confirmer_btn visible: {dialog.confirmer_btn.isVisible()}")
    
    db.conn.close()

if __name__ == "__main__":
    test_quick()