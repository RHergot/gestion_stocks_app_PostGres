#!/usr/bin/env python3
"""
Script de diagnostic pour identifier le problème de mise à jour du statut de commande
lors de la réception
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from APP.services.db import Database
from APP.models.commande_repository import CommandeRepository
from APP.models.ligne_commande_repository import LigneCommandeRepository

def debug_commande_status():
    """Diagnostique le problème de statut de commande"""
    db = None
    try:
        print("🔍 Diagnostic du problème de statut de commande")
        print("=" * 60)
        
        # Connexion
        db = Database()
        db.connect()
        
        commande_repo = CommandeRepository(db)
        ligne_repo = LigneCommandeRepository(db)
        
        # 1. Récupérer toutes les commandes avec statut "Envoyee"
        print("\n1️⃣ Commandes avec statut 'Envoyee':")
        commandes_envoyees = commande_repo.get_commandes_by_statut('Envoyee')
        
        if not commandes_envoyees:
            print("   ❌ Aucune commande avec statut 'Envoyee' trouvée")
            
            # Vérifier tous les statuts disponibles
            print("\n📊 Tous les statuts de commandes dans la base:")
            with db.conn.cursor() as cur:
                cur.execute("SELECT DISTINCT statut, COUNT(*) FROM commande GROUP BY statut ORDER BY statut")
                statuts = cur.fetchall()
                for statut, count in statuts:
                    print(f"   - {statut}: {count} commande(s)")
            
            return False
        
        print(f"   ✅ {len(commandes_envoyees)} commande(s) trouvée(s)")
        
        # 2. Analyser chaque commande
        for commande in commandes_envoyees[:3]:  # Limiter à 3 pour le diagnostic
            print(f"\n2️⃣ Analyse de la commande #{commande['numero_commande']} (ID: {commande['id_commande']})")
            print(f"   📅 Date: {commande['date_commande']}")
            print(f"   📦 Statut actuel: {commande['statut']}")
            
            # Récupérer les lignes de cette commande
            lignes = ligne_repo.get_lignes_by_commande(commande['id_commande'])
            print(f"   📋 {len(lignes)} ligne(s) de commande")
            
            # Analyser chaque ligne
            total_lignes = len(lignes)
            lignes_completes = 0
            lignes_partielles = 0
            
            for i, ligne in enumerate(lignes):
                quantite_commandee = ligne.get('quantite_commandee', 0)
                quantite_recue = ligne.get('quantite_recue', 0)
                quantite_defectueuse = ligne.get('quantite_defectueuse', 0)
                
                total_recue = quantite_recue + quantite_defectueuse
                
                print(f"     Ligne {i+1}: Commandée={quantite_commandee}, Reçue={quantite_recue}, Défectueuse={quantite_defectueuse}, Total={total_recue}")
                
                if total_recue >= quantite_commandee:
                    lignes_completes += 1
                    print(f"       ✅ Ligne complète")
                elif total_recue > 0:
                    lignes_partielles += 1
                    print(f"       🔶 Ligne partielle")
                else:
                    print(f"       ⏳ Ligne en attente")
            
            # Calculer le statut théorique
            if lignes_completes == total_lignes:
                statut_theorique = 'Livree'
            elif lignes_completes > 0 or lignes_partielles > 0:
                statut_theorique = 'Partielle'
            else:
                statut_theorique = 'Envoyee'
            
            print(f"   🎯 Statut théorique: {statut_theorique}")
            print(f"   📊 Lignes complètes: {lignes_completes}/{total_lignes}")
            print(f"   📊 Lignes partielles: {lignes_partielles}")
            
            # Vérifier si le statut devrait être mis à jour
            if statut_theorique != commande['statut']:
                print(f"   ⚠️  PROBLÈME: Statut devrait être '{statut_theorique}' mais est '{commande['statut']}'")
                
                # Tester la mise à jour
                print(f"   🔧 Test de mise à jour du statut...")
                try:
                    update_data = {'statut': statut_theorique}
                    if statut_theorique == 'Livree':
                        from datetime import datetime
                        update_data['date_livraison_reelle'] = datetime.now().strftime('%Y-%m-%d')
                    
                    success = commande_repo.update_commande(commande['id_commande'], update_data)
                    if success:
                        print(f"   ✅ Mise à jour réussie vers '{statut_theorique}'")
                    else:
                        print(f"   ❌ Échec de la mise à jour")
                        
                except Exception as e:
                    print(f"   ❌ Erreur lors de la mise à jour: {e}")
            else:
                print(f"   ✅ Statut correct")
        
        # 3. Vérifier la structure de la table
        print(f"\n3️⃣ Vérification de la structure de la table commande:")
        with db.conn.cursor() as cur:
            cur.execute("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'commande' 
                ORDER BY ordinal_position
            """)
            columns = cur.fetchall()
            
            for col_name, data_type, nullable in columns:
                print(f"   - {col_name}: {data_type} ({'NULL' if nullable == 'YES' else 'NOT NULL'})")
        
        # 4. Vérifier les contraintes sur le statut
        print(f"\n4️⃣ Vérification des contraintes sur le statut:")
        with db.conn.cursor() as cur:
            cur.execute("""
                SELECT constraint_name, constraint_type 
                FROM information_schema.table_constraints 
                WHERE table_name = 'commande' AND constraint_type = 'CHECK'
            """)
            constraints = cur.fetchall()
            
            if constraints:
                for constraint_name, constraint_type in constraints:
                    print(f"   - {constraint_name}: {constraint_type}")
            else:
                print("   ℹ️  Aucune contrainte CHECK trouvée")
        
        # 5. Test de mise à jour directe
        print(f"\n5️⃣ Test de mise à jour directe:")
        if commandes_envoyees:
            test_commande = commandes_envoyees[0]
            print(f"   🧪 Test sur commande #{test_commande['numero_commande']}")
            
            try:
                with db.conn.cursor() as cur:
                    cur.execute("""
                        UPDATE commande 
                        SET statut = 'Livree', updated_at = NOW() 
                        WHERE id_commande = %s
                        RETURNING statut
                    """, (test_commande['id_commande'],))
                    
                    result = cur.fetchone()
                    if result:
                        print(f"   ✅ Mise à jour directe réussie: {result[0]}")
                        
                        # Remettre l'ancien statut
                        cur.execute("""
                            UPDATE commande 
                            SET statut = %s 
                            WHERE id_commande = %s
                        """, (test_commande['statut'], test_commande['id_commande']))
                        
                        db.conn.commit()
                        print(f"   🔄 Statut restauré à '{test_commande['statut']}'")
                    else:
                        print(f"   ❌ Aucun résultat de la mise à jour")
                        
            except Exception as e:
                print(f"   ❌ Erreur lors du test direct: {e}")
                db.conn.rollback()
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du diagnostic: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if db:
            db.close()

def test_reception_logic():
    """Test de la logique de réception"""
    print("\n🧪 Test de la logique de réception")
    print("=" * 40)
    
    # Simuler des données de lignes
    test_cases = [
        {
            "name": "Toutes lignes complètes",
            "lignes": [
                {"quantite_commandee": 10, "quantite_recue": 10, "quantite_defectueuse": 0},
                {"quantite_commandee": 5, "quantite_recue": 5, "quantite_defectueuse": 0},
            ],
            "expected": "Livree"
        },
        {
            "name": "Lignes partielles",
            "lignes": [
                {"quantite_commandee": 10, "quantite_recue": 7, "quantite_defectueuse": 0},
                {"quantite_commandee": 5, "quantite_recue": 5, "quantite_defectueuse": 0},
            ],
            "expected": "Partielle"
        },
        {
            "name": "Avec pièces défectueuses",
            "lignes": [
                {"quantite_commandee": 10, "quantite_recue": 8, "quantite_defectueuse": 2},
                {"quantite_commandee": 5, "quantite_recue": 5, "quantite_defectueuse": 0},
            ],
            "expected": "Livree"
        },
        {
            "name": "Aucune réception",
            "lignes": [
                {"quantite_commandee": 10, "quantite_recue": 0, "quantite_defectueuse": 0},
                {"quantite_commandee": 5, "quantite_recue": 0, "quantite_defectueuse": 0},
            ],
            "expected": "Envoyee"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🔬 Test: {test_case['name']}")
        lignes = test_case['lignes']
        expected = test_case['expected']
        
        # Appliquer la logique de calcul
        total_lignes = len(lignes)
        lignes_completes = 0
        lignes_partielles = 0
        
        for ligne in lignes:
            quantite_commandee = ligne['quantite_commandee']
            quantite_recue = ligne['quantite_recue']
            quantite_defectueuse = ligne['quantite_defectueuse']
            
            if quantite_recue + quantite_defectueuse >= quantite_commandee:
                lignes_completes += 1
            elif quantite_recue + quantite_defectueuse > 0:
                lignes_partielles += 1
        
        # Déterminer le statut
        if lignes_completes == total_lignes:
            statut_calcule = 'Livree'
        elif lignes_completes > 0 or lignes_partielles > 0:
            statut_calcule = 'Partielle'
        else:
            statut_calcule = 'Envoyee'
        
        print(f"   📊 Lignes complètes: {lignes_completes}/{total_lignes}")
        print(f"   📊 Lignes partielles: {lignes_partielles}")
        print(f"   🎯 Statut calculé: {statut_calcule}")
        print(f"   ✅ Attendu: {expected}")
        
        if statut_calcule == expected:
            print(f"   ✅ Test réussi")
        else:
            print(f"   ❌ Test échoué")

if __name__ == "__main__":
    print("🚀 Diagnostic du problème de statut de réception")
    print("=" * 70)
    
    # Test de la logique
    test_reception_logic()
    
    # Diagnostic de la base de données
    success = debug_commande_status()
    
    if success:
        print("\n🎉 Diagnostic terminé")
        print("\n📋 Actions recommandées:")
        print("1. Vérifier les données de test avec une commande spécifique")
        print("2. Tester la réception avec le dialogue")
        print("3. Vérifier les logs de l'application")
        print("4. Examiner les contraintes de base de données")
    else:
        print("\n💥 Diagnostic échoué - Vérifier la configuration")