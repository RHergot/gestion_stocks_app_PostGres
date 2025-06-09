#!/usr/bin/env python3
"""
Debug détaillé du problème de réception
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from APP.services.db import Database
from APP.models.commande_repository import CommandeRepository
from APP.models.ligne_commande_repository import LigneCommandeRepository

def debug_reception_detailed():
    """Debug détaillé du problème"""
    db = None
    try:
        print("🔍 Debug détaillé du problème de réception")
        print("=" * 50)
        
        # Connexion
        db = Database()
        db.connect()
        
        commande_repo = CommandeRepository(db)
        ligne_repo = LigneCommandeRepository(db)
        
        commande_id = 17
        
        # 1. Vérifier l'état actuel
        print("\n1️⃣ État actuel de la commande")
        commande = commande_repo.get_commande_by_id(commande_id)
        print(f"   📦 Commande #{commande['numero_commande']}")
        print(f"   📊 Statut: {commande['statut']}")
        
        lignes = ligne_repo.get_lignes_by_commande(commande_id)
        print(f"   📋 {len(lignes)} ligne(s)")
        
        for i, ligne in enumerate(lignes):
            print(f"     Ligne {i+1} (ID {ligne['id_ligne']}):")
            print(f"       - Commandée: {ligne.get('quantite_commandee', 0)}")
            print(f"       - Reçue: {ligne.get('quantite_recue', 0)}")
            print(f"       - Défectueuse: {ligne.get('quantite_defectueuse', 0)}")
            print(f"       - Total reçu: {ligne.get('quantite_recue', 0) + ligne.get('quantite_defectueuse', 0)}")
        
        # 2. Calculer le statut selon la logique
        print("\n2️⃣ Calcul du statut selon la logique")
        
        total_lignes = len(lignes)
        lignes_completes = 0
        lignes_partielles = 0
        
        for ligne in lignes:
            quantite_commandee = ligne.get('quantite_commandee', 0)
            quantite_recue = ligne.get('quantite_recue', 0)
            quantite_defectueuse = ligne.get('quantite_defectueuse', 0)
            
            total_recue = quantite_recue + quantite_defectueuse
            
            print(f"   Ligne {ligne['id_ligne']}: {total_recue}/{quantite_commandee}", end="")
            
            if total_recue >= quantite_commandee:
                lignes_completes += 1
                print(" → Complète")
            elif total_recue > 0:
                lignes_partielles += 1
                print(" → Partielle")
            else:
                print(" → En attente")
        
        print(f"\n   📊 Résumé:")
        print(f"     - Total lignes: {total_lignes}")
        print(f"     - Lignes complètes: {lignes_completes}")
        print(f"     - Lignes partielles: {lignes_partielles}")
        
        # Déterminer le statut
        if lignes_completes == total_lignes:
            statut_theorique = 'Livree'
        elif lignes_completes > 0 or lignes_partielles > 0:
            statut_theorique = 'Partielle'
        else:
            statut_theorique = 'Envoyee'
        
        print(f"   🎯 Statut théorique: {statut_theorique}")
        print(f"   📊 Statut actuel: {commande['statut']}")
        
        if statut_theorique != commande['statut']:
            print(f"   ⚠️  INCOHÉRENCE DÉTECTÉE!")
            
            # 3. Tester la mise à jour
            print("\n3️�� Test de mise à jour du statut")
            
            update_data = {'statut': statut_theorique}
            if statut_theorique == 'Livree':
                from datetime import datetime
                update_data['date_livraison_reelle'] = datetime.now().strftime('%Y-%m-%d')
            
            print(f"   🔧 Tentative de mise à jour vers '{statut_theorique}'")
            
            success = commande_repo.update_commande(commande_id, update_data)
            print(f"   {'✅' if success else '❌'} Résultat: {success}")
            
            if success:
                # Vérifier la mise à jour
                commande_updated = commande_repo.get_commande_by_id(commande_id)
                print(f"   🔍 Nouveau statut: {commande_updated['statut']}")
                
                if commande_updated['statut'] == statut_theorique:
                    print(f"   ✅ Mise à jour réussie!")
                else:
                    print(f"   ❌ Mise à jour échouée")
                    
                    # Debug plus poussé
                    print("\n4️⃣ Debug de la mise à jour")
                    
                    # Vérifier directement en SQL
                    with db.conn.cursor() as cur:
                        cur.execute("SELECT statut FROM commande WHERE id_commande = %s", (commande_id,))
                        result = cur.fetchone()
                        if result:
                            print(f"   🔍 Statut direct SQL: {result[0]}")
                        
                        # Tester une mise à jour directe
                        cur.execute("""
                            UPDATE commande 
                            SET statut = %s, updated_at = NOW() 
                            WHERE id_commande = %s
                            RETURNING statut
                        """, (statut_theorique, commande_id))
                        
                        result = cur.fetchone()
                        if result:
                            print(f"   ✅ Mise à jour SQL directe: {result[0]}")
                            db.conn.commit()
                        else:
                            print(f"   ❌ Échec mise à jour SQL directe")
        else:
            print(f"   ✅ Statut cohérent")
        
        # 5. Vérifier les contraintes
        print("\n5️⃣ Vérification des contraintes")
        
        with db.conn.cursor() as cur:
            # Vérifier les valeurs possibles pour le statut
            cur.execute("""
                SELECT DISTINCT statut 
                FROM commande 
                ORDER BY statut
            """)
            statuts_existants = [row[0] for row in cur.fetchall()]
            print(f"   📋 Statuts existants: {statuts_existants}")
            
            # Vérifier s'il y a des contraintes CHECK
            cur.execute("""
                SELECT conname, consrc 
                FROM pg_constraint 
                WHERE conrelid = 'commande'::regclass 
                AND contype = 'c'
            """)
            constraints = cur.fetchall()
            
            if constraints:
                print(f"   🔒 Contraintes CHECK trouvées:")
                for name, src in constraints:
                    print(f"     - {name}: {src}")
            else:
                print(f"   ℹ️  Aucune contrainte CHECK sur la table commande")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du debug: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if db:
            db.close()

if __name__ == "__main__":
    debug_reception_detailed()