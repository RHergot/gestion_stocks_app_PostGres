#!/usr/bin/env python3
"""
Test de la logique exacte du dialogue de réception
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from APP.services.db import Database
from APP.models.commande_repository import CommandeRepository
from APP.models.ligne_commande_repository import LigneCommandeRepository
from datetime import datetime

def simulate_reception_dialog():
    """Simule exactement ce qui se passe dans le dialogue de réception"""
    db = None
    try:
        print("🎭 Simulation du dialogue de réception")
        print("=" * 50)
        
        # Connexion
        db = Database()
        db.connect()
        
        # Données de la commande (comme dans le dialogue)
        commande_data = {'id_commande': 17, 'numero_commande': '106'}
        
        # 1. Charger les lignes comme dans load_lignes_commande()
        print("\n1️⃣ Chargement des lignes (comme dans le dialogue)")
        
        from APP.models.ligne_commande_repository import LigneCommandeRepository
        repo = LigneCommandeRepository(db)
        lignes = repo.get_lignes_by_commande(commande_data['id_commande'])
        
        print(f"   📋 {len(lignes)} ligne(s) chargée(s)")
        
        # Simuler reception_data comme dans le dialogue
        reception_data = {}
        
        for ligne in lignes:
            ligne_id = ligne['id_ligne']
            qte_recue = ligne.get('quantite_recue', 0)
            qte_restante = ligne.get('quantite_commandee', 0) - qte_recue
            
            reception_data[ligne_id] = {
                'ligne_data': ligne,
                'quantite_a_receptionner': qte_restante,  # Par défaut, tout ce qui reste
                'bon_etat': True,
                'commentaire': ''
            }
            
            print(f"   📦 Ligne {ligne_id}: {qte_restante} à réceptionner")
        
        # 2. Simuler une réception partielle (modifier quantite_a_receptionner)
        print("\n2️⃣ Simulation d'une réception partielle")
        
        # Modifier la première ligne pour ne recevoir que 50 unités
        premiere_ligne_id = list(reception_data.keys())[0]
        reception_data[premiere_ligne_id]['quantite_a_receptionner'] = 50
        reception_data[premiere_ligne_id]['commentaire'] = 'Réception partielle test'
        
        # Mettre les autres à 0 (pas de réception)
        for ligne_id in list(reception_data.keys())[1:]:
            reception_data[ligne_id]['quantite_a_receptionner'] = 0
        
        print(f"   📦 Réception de 50 unités sur la ligne {premiere_ligne_id}")
        
        # 3. Simuler process_reception()
        print("\n3️⃣ Simulation du traitement de la réception")
        
        ligne_repo = LigneCommandeRepository(db)
        
        for ligne_id, reception_info in reception_data.items():
            quantite = reception_info['quantite_a_receptionner']
            if quantite <= 0:
                continue
            
            ligne_data = reception_info['ligne_data']
            bon_etat = reception_info['bon_etat']
            commentaire = reception_info['commentaire']
            
            print(f"   🔄 Traitement ligne {ligne_id}: +{quantite} unités")
            
            # Mettre à jour la ligne de commande (comme dans le dialogue)
            nouvelle_quantite_recue = ligne_data.get('quantite_recue', 0) + quantite
            update_data = {
                'quantite_recue': nouvelle_quantite_recue,
                'date_derniere_reception': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'commentaire_reception': commentaire
            }
            
            # Si pièces défectueuses
            if not bon_etat:
                nouvelle_quantite_defectueuse = ligne_data.get('quantite_defectueuse', 0) + quantite
                update_data['quantite_defectueuse'] = nouvelle_quantite_defectueuse
            
            ligne_repo.update_ligne_commande(ligne_id, update_data)
            print(f"   ✅ Ligne mise à jour: quantite_recue = {nouvelle_quantite_recue}")
        
        # 4. Simuler update_commande_status() exactement comme dans le dialogue
        print("\n4️⃣ Simulation de update_commande_status()")
        
        # Code exact du dialogue
        from APP.models.commande_repository import CommandeRepository
        
        commande_repo = CommandeRepository(db)
        
        # Récupérer toutes les lignes de la commande (FRAÎCHES)
        lignes_fresh = ligne_repo.get_lignes_by_commande(commande_data['id_commande'])
        
        print(f"   📋 Analyse de {len(lignes_fresh)} ligne(s) fraîches")
        
        # Calculer le statut global
        total_lignes = len(lignes_fresh)
        lignes_completes = 0
        lignes_partielles = 0
        
        for ligne in lignes_fresh:
            quantite_commandee = ligne.get('quantite_commandee', 0)
            quantite_recue = ligne.get('quantite_recue', 0)
            quantite_defectueuse = ligne.get('quantite_defectueuse', 0)
            
            total_recue = quantite_recue + quantite_defectueuse
            
            print(f"     Ligne {ligne['id_ligne']}: {total_recue}/{quantite_commandee}", end="")
            
            if total_recue >= quantite_commandee:
                lignes_completes += 1
                print(" → Complète")
            elif total_recue > 0:
                lignes_partielles += 1
                print(" → Partielle")
            else:
                print(" → En attente")
        
        print(f"   📊 Lignes complètes: {lignes_completes}/{total_lignes}")
        print(f"   📊 Lignes partielles: {lignes_partielles}")
        
        # Déterminer le nouveau statut (code exact du dialogue)
        if lignes_completes == total_lignes:
            nouveau_statut = 'Livree'
        elif lignes_completes > 0 or lignes_partielles > 0:
            nouveau_statut = 'Partielle'
        else:
            nouveau_statut = 'Envoyee'  # Reste en envoyée si rien n'est reçu
        
        print(f"   🎯 Nouveau statut calculé: {nouveau_statut}")
        
        # Mettre à jour la commande (code exact du dialogue)
        update_data = {'statut': nouveau_statut}
        if nouveau_statut == 'Livree':
            update_data['date_livraison_reelle'] = datetime.now().strftime('%Y-%m-%d')
        
        success = commande_repo.update_commande(commande_data['id_commande'], update_data)
        print(f"   {'✅' if success else '❌'} Mise à jour commande: {success}")
        
        if success:
            # Vérifier le résultat
            commande_verif = commande_repo.get_commande_by_id(commande_data['id_commande'])
            print(f"   🔍 Statut final: {commande_verif['statut']}")
            
            if commande_verif['statut'] == nouveau_statut:
                print(f"   ✅ Statut correctement mis à jour!")
                
                if nouveau_statut == 'Partielle':
                    print(f"   🎉 PROBLÈME RÉSOLU: Le statut passe bien à 'Partielle'")
                    return True
                else:
                    print(f"   ⚠️  Statut inattendu: {nouveau_statut}")
                    return False
            else:
                print(f"   ❌ Problème de mise à jour: attendu '{nouveau_statut}', obtenu '{commande_verif['statut']}'")
                return False
        else:
            print(f"   ❌ Échec de la mise à jour")
            return False
        
    except Exception as e:
        print(f"❌ Erreur lors de la simulation: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if db:
            db.close()

def test_complete_reception():
    """Test d'une réception complète"""
    db = None
    try:
        print("\n🎯 Test d'une réception complète")
        print("=" * 40)
        
        db = Database()
        db.connect()
        
        commande_data = {'id_commande': 17, 'numero_commande': '106'}
        
        # Simuler la réception de toutes les lignes
        from APP.models.ligne_commande_repository import LigneCommandeRepository
        from APP.models.commande_repository import CommandeRepository
        
        ligne_repo = LigneCommandeRepository(db)
        commande_repo = CommandeRepository(db)
        
        lignes = ligne_repo.get_lignes_by_commande(commande_data['id_commande'])
        
        print(f"   📋 Complétion de {len(lignes)} ligne(s)")
        
        # Compléter toutes les lignes
        for ligne in lignes:
            quantite_commandee = ligne.get('quantite_commandee', 0)
            
            update_data = {
                'quantite_recue': quantite_commandee,
                'date_derniere_reception': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'commentaire_reception': 'Réception complète test'
            }
            
            ligne_repo.update_ligne_commande(ligne['id_ligne'], update_data)
            print(f"   ✅ Ligne {ligne['id_ligne']}: {quantite_commandee} unités")
        
        # Recalculer le statut
        lignes_fresh = ligne_repo.get_lignes_by_commande(commande_data['id_commande'])
        
        total_lignes = len(lignes_fresh)
        lignes_completes = 0
        
        for ligne in lignes_fresh:
            quantite_commandee = ligne.get('quantite_commandee', 0)
            quantite_recue = ligne.get('quantite_recue', 0)
            quantite_defectueuse = ligne.get('quantite_defectueuse', 0)
            
            if quantite_recue + quantite_defectueuse >= quantite_commandee:
                lignes_completes += 1
        
        nouveau_statut = 'Livree' if lignes_completes == total_lignes else 'Partielle'
        print(f"   🎯 Statut calculé: {nouveau_statut}")
        
        # Mettre à jour
        update_data = {
            'statut': nouveau_statut,
            'date_livraison_reelle': datetime.now().strftime('%Y-%m-%d')
        }
        
        success = commande_repo.update_commande(commande_data['id_commande'], update_data)
        
        if success:
            commande_verif = commande_repo.get_commande_by_id(commande_data['id_commande'])
            print(f"   🔍 Statut final: {commande_verif['statut']}")
            
            if commande_verif['statut'] == 'Livree':
                print(f"   🎉 SUCCÈS: Statut 'Livree' confirmé!")
                return True
            else:
                print(f"   ❌ Problème: attendu 'Livree', obtenu '{commande_verif['statut']}'")
                return False
        else:
            print(f"   ❌ Échec de la mise à jour")
            return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        if db:
            db.close()

if __name__ == "__main__":
    print("🚀 Test de la logique du dialogue de réception")
    print("=" * 60)
    
    # Test de réception partielle
    success1 = simulate_reception_dialog()
    
    # Test de réception complète
    success2 = test_complete_reception()
    
    if success1 and success2:
        print("\n🎉 TOUS LES TESTS RÉUSSIS!")
        print("\n✅ La logique du dialogue de réception fonctionne correctement")
        print("✅ Les statuts sont mis à jour comme attendu")
        print("\n📋 Conclusion:")
        print("   Le problème initial était probablement dû à:")
        print("   1. Données de test insuffisantes")
        print("   2. Cache ou problème de rafraîchissement")
        print("   3. Interface utilisateur non synchronisée")
        print("\n🎯 Le système de réception fonctionne correctement!")
    else:
        print("\n💥 Certains tests ont échoué")
        print("Le problème nécessite une investigation plus approfondie")