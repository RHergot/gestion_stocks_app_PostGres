#!/usr/bin/env python3
"""
Script automatique pour préparer une commande de test pour la réception
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from APP.services.db import Database
from APP.models.commande_repository import CommandeRepository

def prepare_test_reception():
    """Prépare automatiquement une commande pour tester la réception"""
    
    print("=== Préparation automatique d'une commande de test ===\n")
    
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
        
        # Prendre la première commande disponible
        commande_test = commandes[0]
        
        print(f"Commande sélectionnée: {commande_test['numero_commande']} (Statut: {commande_test['statut']})")
        
        # Effectuer les modifications
        with db.conn.cursor() as cur:
            # 1. Remettre la commande en statut Envoyee
            cur.execute("""
                UPDATE commande 
                SET statut = 'Envoyee', date_livraison_reelle = NULL 
                WHERE id_commande = %s
            """, (commande_test['id_commande'],))
            
            # 2. Remettre à zéro les quantités reçues des lignes
            cur.execute("""
                UPDATE ligne_commande 
                SET quantite_recue = 0, 
                    quantite_defectueuse = 0,
                    date_derniere_reception = NULL,
                    commentaire_reception = NULL,
                    statut_ligne = 'Attente'
                WHERE commande_id = %s
            """, (commande_test['id_commande'],))
            
            # 3. Supprimer l'historique des réceptions
            cur.execute("""
                DELETE FROM reception_detail 
                WHERE ligne_commande_id IN (
                    SELECT id_ligne FROM ligne_commande 
                    WHERE commande_id = %s
                )
            """, (commande_test['id_commande'],))
            
            db.conn.commit()
        
        print(f"✅ Commande {commande_test['numero_commande']} remise en statut 'Envoyee'")
        print("✅ Quantités reçues remises à zéro")
        print("✅ Historique des réceptions supprimé")
        print("\n🎯 La commande est maintenant prête pour tester la réception !")
        
        # Afficher les lignes de la commande
        with db.conn.cursor() as cur:
            cur.execute("""
                SELECT lc.*, p.reference, p.nom 
                FROM ligne_commande lc
                LEFT JOIN piece p ON lc.piece_id = p.id_piece
                WHERE lc.commande_id = %s
            """, (commande_test['id_commande'],))
            lignes = cur.fetchall()
            
            print(f"\nLignes de la commande {commande_test['numero_commande']}:")
            for ligne in lignes:
                print(f"  - {ligne[6] or 'N/A'} ({ligne[7] or 'N/A'}): {ligne[4]} pièces à {ligne[5]}€")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    finally:
        if db.conn:
            db.conn.close()

if __name__ == "__main__":
    prepare_test_reception()