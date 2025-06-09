#!/usr/bin/env python3
"""
Script pour remettre une commande en statut Brouillon pour les tests
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from APP.services.db import Database
from APP.models.commande_repository import CommandeRepository

def reset_commande_status():
    """Remet une commande en statut Brouillon pour les tests"""
    
    print("=== Reset du statut d'une commande pour les tests ===\n")
    
    # Connexion à la base de données
    db = Database()
    try:
        db.connect()
        print("✅ Connexion à la base de données réussie")
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False
    
    try:
        commande_repo = CommandeRepository(db)
        
        # Récupérer toutes les commandes
        commandes = commande_repo.get_all_commandes()
        
        if not commandes:
            print("❌ Aucune commande trouvée")
            return False
        
        print("Commandes disponibles:")
        for i, cmd in enumerate(commandes[:10]):  # Afficher les 10 premières
            print(f"{i+1}. ID={cmd['id_commande']}, Numéro={cmd['numero_commande']}, Statut={cmd['statut']}")
        
        # Demander à l'utilisateur quelle commande modifier
        try:
            choix = input(f"\nQuelle commande voulez-vous remettre en statut 'Brouillon' ? (1-{min(10, len(commandes))}): ")
            index = int(choix) - 1
            
            if index < 0 or index >= len(commandes):
                print("❌ Choix invalide")
                return False
            
            commande_choisie = commandes[index]
            
        except (ValueError, KeyboardInterrupt):
            print("\n❌ Opération annulée")
            return False
        
        # Confirmer l'action
        print(f"\nCommande sélectionnée: {commande_choisie['numero_commande']} (Statut actuel: {commande_choisie['statut']})")
        confirmation = input("Confirmer la remise en statut 'Brouillon' ? (o/N): ")
        
        if confirmation.lower() not in ['o', 'oui', 'y', 'yes']:
            print("❌ Opération annulée")
            return False
        
        # Effectuer la modification
        success = commande_repo.update_commande(
            commande_choisie['id_commande'],
            {
                'statut': 'Brouillon',
                'date_livraison_reelle': None
            }
        )
        
        if success:
            print(f"✅ Commande {commande_choisie['numero_commande']} remise en statut 'Brouillon'")
            return True
        else:
            print("❌ Échec de la modification")
            return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    finally:
        if db.conn:
            db.conn.close()

if __name__ == "__main__":
    reset_commande_status()