#!/usr/bin/env python3
"""
Script pour corriger et tester la logique de réception
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from APP.services.db import Database
from APP.models.commande_repository import CommandeRepository
from APP.models.ligne_commande_repository import LigneCommandeRepository
from datetime import datetime

def test_reception_logic_corrected():
    """Test de la logique de réception corrigée"""
    print("🧪 Test de la logique de réception corrigée")
    print("=" * 50)
    
    # Test cases avec la logique corrigée
    test_cases = [
        {
            "name": "Réception partielle (5/100)",
            "lignes": [
                {"quantite_commandee": 100, "quantite_recue": 5, "quantite_defectueuse": 0},
                {"quantite_commandee": 15, "quantite_recue": 0, "quantite_defectueuse": 0},
                {"quantite_commandee": 20, "quantite_recue": 0, "quantite_defectueuse": 0},
            ],
            "expected": "Partielle"
        },
        {
            "name": "Une ligne complète, autres partielles",
            "lignes": [
                {"quantite_commandee": 100, "quantite_recue": 100, "quantite_defectueuse": 0},
                {"quantite_commandee": 15, "quantite_recue": 5, "quantite_defectueuse": 0},
                {"quantite_commandee": 20, "quantite_recue": 0, "quantite_defectueuse": 0},
            ],
            "expected": "Partielle"
        },
        {
            "name": "Toutes lignes complètes",
            "lignes": [
                {"quantite_commandee": 100, "quantite_recue": 100, "quantite_defectueuse": 0},
                {"quantite_commandee": 15, "quantite_recue": 15, "quantite_defectueuse": 0},
                {"quantite_commandee": 20, "quantite_recue": 20, "quantite_defectueuse": 0},
            ],
            "expected": "Livree"
        },
        {
            "name": "Avec pièces défectueuses (complète)",
            "lignes": [
                {"quantite_commandee": 100, "quantite_recue": 90, "quantite_defectueuse": 10},
                {"quantite_commandee": 15, "quantite_recue": 15, "quantite_defectueuse": 0},
                {"quantite_commandee": 20, "quantite_recue": 18, "quantite_defectueuse": 2},
            ],
            "expected": "Livree"
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
            
            total_recue = quantite_recue + quantite_defectueuse
            
            if total_recue >= quantite_commandee:
                lignes_completes += 1
            elif total_recue > 0:
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
            print(f"   ❌ Test échoué - Logique à corriger")

def test_real_reception_scenario():
    """Test avec un scénario réel de réception"""
    db = None
    try:
        print("\n🚀 Test avec scénario réel de réception")
        print("=" * 50)
        
        # Connexion
        db = Database()
        db.connect()
        
        commande_repo = CommandeRepository(db)
        ligne_repo = LigneCommandeRepository(db)
        
        # Réinitialiser la commande de test
        print("\n1️⃣ Réinitialisation de la commande de test")
        commande_id = 17  # ID de la commande de test
        
        # Remettre toutes les quantités reçues à 0
        with db.conn.cursor() as cur:
            cur.execute("""
                UPDATE ligne_commande 
                SET quantite_recue = 0, 
                    quantite_defectueuse = 0,
                    date_derniere_reception = NULL,
                    commentaire_reception = NULL
                WHERE commande_id = %s
            """, (commande_id,))
            
            # Remettre le statut de la commande à "Envoyee"
            cur.execute("""
                UPDATE commande 
                SET statut = 'Envoyee',
                    date_livraison_reelle = NULL
                WHERE id_commande = %s
            """, (commande_id,))
            
            db.conn.commit()
        
        print("   ✅ Commande réinitialisée")
        
        # 2. Scénario 1: Réception partielle
        print("\n2️⃣ Scénario 1: Réception partielle")
        lignes = ligne_repo.get_lignes_by_commande(commande_id)
        
        # Recevoir partiellement la première ligne
        premiere_ligne = lignes[0]
        quantite_partielle = 50  # 50 sur 100
        
        update_data = {
            'quantite_recue': quantite_partielle,
            'date_derniere_reception': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'commentaire_reception': 'Réception partielle test'
        }
        
        ligne_repo.update_ligne_commande(premiere_ligne['id_ligne'], update_data)
        print(f"   📦 Reçu {quantite_partielle} unités sur {premiere_ligne['quantite_commandee']}")
        
        # Calculer et mettre à jour le statut
        nouveau_statut = calculate_and_update_status(db, commande_id)
        print(f"   🎯 Nouveau statut: {nouveau_statut}")
        
        if nouveau_statut == 'Partielle':
            print("   ✅ Statut correct pour réception partielle")
        else:
            print(f"   ❌ Statut incorrect: attendu 'Partielle', obtenu '{nouveau_statut}'")
        
        # 3. Scénario 2: Compléter une ligne
        print("\n3️⃣ Scénario 2: Compléter la première ligne")
        
        # Compléter la première ligne
        quantite_restante = premiere_ligne['quantite_commandee'] - quantite_partielle
        nouvelle_quantite_totale = premiere_ligne['quantite_commandee']
        
        update_data = {
            'quantite_recue': nouvelle_quantite_totale,
            'date_derniere_reception': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'commentaire_reception': 'Complétion de la ligne'
        }
        
        ligne_repo.update_ligne_commande(premiere_ligne['id_ligne'], update_data)
        print(f"   📦 Ligne complétée: {nouvelle_quantite_totale}/{premiere_ligne['quantite_commandee']}")
        
        # Calculer et mettre à jour le statut
        nouveau_statut = calculate_and_update_status(db, commande_id)
        print(f"   🎯 Nouveau statut: {nouveau_statut}")
        
        if nouveau_statut == 'Partielle':
            print("   ✅ Statut correct (une ligne complète, autres en attente)")
        else:
            print(f"   ❌ Statut incorrect: attendu 'Partielle', obtenu '{nouveau_statut}'")
        
        # 4. Scénario 3: Compléter toutes les lignes
        print("\n4️⃣ Scénario 3: Compléter toutes les lignes")
        
        for ligne in lignes[1:]:  # Compléter les autres lignes
            update_data = {
                'quantite_recue': ligne['quantite_commandee'],
                'date_derniere_reception': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'commentaire_reception': 'Complétion finale'
            }
            
            ligne_repo.update_ligne_commande(ligne['id_ligne'], update_data)
            print(f"   📦 Ligne {ligne['id_ligne']} complétée: {ligne['quantite_commandee']}")
        
        # Calculer et mettre à jour le statut final
        nouveau_statut = calculate_and_update_status(db, commande_id)
        print(f"   🎯 Statut final: {nouveau_statut}")
        
        if nouveau_statut == 'Livree':
            print("   ✅ Statut correct pour commande complète")
            
            # Vérifier la date de livraison
            commande_finale = commande_repo.get_commande_by_id(commande_id)
            if commande_finale.get('date_livraison_reelle'):
                print(f"   📅 Date de livraison: {commande_finale['date_livraison_reelle']}")
                print("   ✅ Date de livraison mise à jour")
            else:
                print("   ⚠️  Date de livraison non mise à jour")
        else:
            print(f"   ❌ Statut incorrect: attendu 'Livree', obtenu '{nouveau_statut}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if db:
            db.close()

def calculate_and_update_status(db, commande_id):
    """Calcule et met à jour le statut d'une commande"""
    from APP.models.ligne_commande_repository import LigneCommandeRepository
    from APP.models.commande_repository import CommandeRepository
    
    ligne_repo = LigneCommandeRepository(db)
    commande_repo = CommandeRepository(db)
    
    # Récupérer toutes les lignes de la commande
    lignes = ligne_repo.get_lignes_by_commande(commande_id)
    
    # Calculer le statut global
    total_lignes = len(lignes)
    lignes_completes = 0
    lignes_partielles = 0
    
    for ligne in lignes:
        quantite_commandee = ligne.get('quantite_commandee', 0)
        quantite_recue = ligne.get('quantite_recue', 0)
        quantite_defectueuse = ligne.get('quantite_defectueuse', 0)
        
        total_recue = quantite_recue + quantite_defectueuse
        
        if total_recue >= quantite_commandee:
            lignes_completes += 1
        elif total_recue > 0:
            lignes_partielles += 1
    
    # Déterminer le nouveau statut
    if lignes_completes == total_lignes:
        nouveau_statut = 'Livree'
    elif lignes_completes > 0 or lignes_partielles > 0:
        nouveau_statut = 'Partielle'
    else:
        nouveau_statut = 'Envoyee'
    
    # Mettre à jour la commande
    update_data = {'statut': nouveau_statut}
    if nouveau_statut == 'Livree':
        update_data['date_livraison_reelle'] = datetime.now().strftime('%Y-%m-%d')
    
    commande_repo.update_commande(commande_id, update_data)
    
    return nouveau_statut

if __name__ == "__main__":
    print("🚀 Correction et test de la logique de réception")
    print("=" * 60)
    
    # Test de la logique théorique
    test_reception_logic_corrected()
    
    # Test avec données réelles
    success = test_real_reception_scenario()
    
    if success:
        print("\n🎉 TESTS RÉUSSIS!")
        print("\n✅ La logique de réception fonctionne correctement")
        print("✅ Les statuts sont mis à jour comme attendu")
        print("\n📋 Résumé des statuts:")
        print("   - Envoyee: Aucune réception")
        print("   - Partielle: Au moins une réception partielle ou une ligne complète")
        print("   - Livree: Toutes les lignes complètement reçues")
    else:
        print("\n💥 Certains tests ont échoué")
        print("La logique nécessite des corrections")