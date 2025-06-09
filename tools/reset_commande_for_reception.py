#!/usr/bin/env python3
"""
Script pour remettre une commande en statut Envoyee pour tester la réception
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from APP.services.db import Database
from APP.models.commande_repository import CommandeRepository

def reset_commande_for_reception():
    """Remet une commande en statut Envoyee et remet à zéro les réceptions"""
    
    print("=== Reset d'une commande pour test de réception ===\n")
    
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
            choix = input(f"\nQuelle commande voulez-vous remettre en statut 'Envoyee' ? (1-{min(10, len(commandes))}): ")
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
        confirmation = input("Confirmer la remise en statut 'Envoyee' et reset des réceptions ? (o/N): ")
        
        if confirmation.lower() not in ['o', 'oui', 'y', 'yes']:
            print("❌ Opération annulée")
            return False
        
        # Effectuer les modifications
        with db.conn.cursor() as cur:
            # 1. Remettre la commande en statut Envoyee
            cur.execute("""
                UPDATE commande 
                SET statut = 'Envoyee', date_livraison_reelle = NULL 
                WHERE id_commande = %s
            """, (commande_choisie['id_commande'],))
            
            # 2. Remettre à zéro les quantités reçues des lignes
            cur.execute("""
                UPDATE ligne_commande 
                SET quantite_recue = 0, 
                    quantite_defectueuse = 0,
                    date_derniere_reception = NULL,
                    commentaire_reception = NULL,
                    statut_ligne = 'Attente'
                WHERE commande_id = %s
            """, (commande_choisie['id_commande'],))
            
            # 3. Supprimer l'historique des réceptions
            cur.execute("""
                DELETE FROM reception_detail 
                WHERE ligne_commande_id IN (
                    SELECT id_ligne FROM ligne_commande 
                    WHERE commande_id = %s
                )
            """, (commande_choisie['id_commande'],))
            
            db.conn.commit()
        
        print(f"✅ Commande {commande_choisie['numero_commande']} remise en statut 'Envoyee'")
        print("✅ Quantités reçues remises à zéro")
        print("✅ Historique des réceptions supprimé")
        print("\n🎯 La commande est maintenant prête pour tester la réception !")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    finally:
        if db.conn:
            db.conn.close()

if __name__ == "__main__":
    reset_commande_for_reception()