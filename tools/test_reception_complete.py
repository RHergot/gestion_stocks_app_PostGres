#!/usr/bin/env python3
"""
Test complet du processus de réception pour identifier le problème de statut
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from APP.services.db import Database
from APP.models.commande_repository import CommandeRepository
from APP.models.ligne_commande_repository import LigneCommandeRepository
from datetime import datetime

def test_reception_complete():
    """Test complet du processus de réception"""
    db = None
    try:
        print("🧪 Test complet du processus de réception")
        print("=" * 50)
        
        # Connexion
        db = Database()
        db.connect()
        
        commande_repo = CommandeRepository(db)
        ligne_repo = LigneCommandeRepository(db)
        
        # 1. Trouver une commande avec statut "Envoyee"
        print("\n1️⃣ Recherche d'une commande de test")
        commandes_envoyees = commande_repo.get_commandes_by_statut('Envoyee')
        
        if not commandes_envoyees:
            print("   ❌ Aucune commande 'Envoyee' trouvée")
            return False
        
        commande_test = commandes_envoyees[0]
        print(f"   ✅ Commande de test: #{commande_test['numero_commande']} (ID: {commande_test['id_commande']})")
        
        # 2. Récupérer les lignes de commande
        print("\n2️⃣ Analyse des lignes de commande")
        lignes = ligne_repo.get_lignes_by_commande(commande_test['id_commande'])
        print(f"   📋 {len(lignes)} ligne(s) trouvée(s)")
        
        for i, ligne in enumerate(lignes):
            print(f"     Ligne {i+1}: ID={ligne['id_ligne']}, Qté={ligne.get('quantite_commandee', 0)}, Reçue={ligne.get('quantite_recue', 0)}")
        
        if not lignes:
            print("   ❌ Aucune ligne de commande trouvée")
            return False
        
        # 3. Simuler une réception partielle sur la première ligne
        print("\n3️⃣ Simulation d'une réception partielle")
        premiere_ligne = lignes[0]
        quantite_commandee = premiere_ligne.get('quantite_commandee', 0)
        quantite_a_recevoir = min(5, quantite_commandee // 2)  # Recevoir la moitié ou 5, le plus petit
        
        if quantite_a_recevoir <= 0:
            quantite_a_recevoir = 1
        
        print(f"   📦 Réception de {quantite_a_recevoir} unités sur la ligne {premiere_ligne['id_ligne']}")
        
        # Mettre à jour la ligne
        nouvelle_quantite_recue = premiere_ligne.get('quantite_recue', 0) + quantite_a_recevoir
        update_data = {
            'quantite_recue': nouvelle_quantite_recue,
            'date_derniere_reception': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'commentaire_reception': 'Test de réception automatique'
        }
        
        ligne_repo.update_ligne_commande(premiere_ligne['id_ligne'], update_data)
        print(f"   ✅ Ligne mise à jour: {premiere_ligne.get('quantite_recue', 0)} → {nouvelle_quantite_recue}")
        
        # 4. Calculer le nouveau statut selon la logique de réception
        print("\n4️⃣ Calcul du nouveau statut")
        lignes_mises_a_jour = ligne_repo.get_lignes_by_commande(commande_test['id_commande'])
        
        total_lignes = len(lignes_mises_a_jour)
        lignes_completes = 0
        lignes_partielles = 0
        
        for ligne in lignes_mises_a_jour:
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
        
        print(f"   📊 Lignes complètes: {lignes_completes}/{total_lignes}")
        print(f"   📊 Lignes partielles: {lignes_partielles}")
        print(f"   🎯 Nouveau statut calculé: {nouveau_statut}")
        
        # 5. Mettre à jour le statut de la commande
        print("\n5️⃣ Mise à jour du statut de la commande")
        statut_avant = commande_test['statut']
        
        update_commande_data = {'statut': nouveau_statut}
        if nouveau_statut == 'Livree':
            update_commande_data['date_livraison_reelle'] = datetime.now().strftime('%Y-%m-%d')
        
        success = commande_repo.update_commande(commande_test['id_commande'], update_commande_data)
        
        if success:
            print(f"   ✅ Statut mis à jour: '{statut_avant}' → '{nouveau_statut}'")
            
            # Vérifier la mise à jour
            commande_verif = commande_repo.get_commande_by_id(commande_test['id_commande'])
            print(f"   🔍 Vérification: Statut actuel = '{commande_verif['statut']}'")
            
            if commande_verif['statut'] == nouveau_statut:
                print(f"   ✅ Mise à jour confirmée")
            else:
                print(f"   ❌ Problème: Statut attendu '{nouveau_statut}', trouvé '{commande_verif['statut']}'")
        else:
            print(f"   ❌ Échec de la mise à jour du statut")
        
        # 6. Test avec réception complète
        print("\n6️⃣ Test avec réception complète")
        
        # Compléter toutes les lignes
        for ligne in lignes_mises_a_jour:
            quantite_commandee = ligne.get('quantite_commandee', 0)
            quantite_recue = ligne.get('quantite_recue', 0)
            quantite_manquante = quantite_commandee - quantite_recue
            
            if quantite_manquante > 0:
                print(f"   📦 Complétion ligne {ligne['id_ligne']}: +{quantite_manquante} unités")
                
                update_data = {
                    'quantite_recue': quantite_commandee,
                    'date_derniere_reception': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'commentaire_reception': 'Test de réception complète automatique'
                }
                
                ligne_repo.update_ligne_commande(ligne['id_ligne'], update_data)
        
        # Recalculer le statut
        lignes_finales = ligne_repo.get_lignes_by_commande(commande_test['id_commande'])
        
        total_lignes = len(lignes_finales)
        lignes_completes = 0
        
        for ligne in lignes_finales:
            quantite_commandee = ligne.get('quantite_commandee', 0)
            quantite_recue = ligne.get('quantite_recue', 0)
            quantite_defectueuse = ligne.get('quantite_defectueuse', 0)
            
            if quantite_recue + quantite_defectueuse >= quantite_commandee:
                lignes_completes += 1
        
        statut_final = 'Livree' if lignes_completes == total_lignes else 'Partielle'
        print(f"   🎯 Statut final calculé: {statut_final}")
        
        # Mettre à jour vers "Livree"
        update_final_data = {
            'statut': statut_final,
            'date_livraison_reelle': datetime.now().strftime('%Y-%m-%d')
        }
        
        success_final = commande_repo.update_commande(commande_test['id_commande'], update_final_data)
        
        if success_final:
            print(f"   ✅ Statut final mis à jour vers '{statut_final}'")
            
            # Vérification finale
            commande_finale = commande_repo.get_commande_by_id(commande_test['id_commande'])
            print(f"   🔍 Vérification finale: Statut = '{commande_finale['statut']}'")
            print(f"   📅 Date livraison: {commande_finale.get('date_livraison_reelle', 'N/A')}")
            
            if commande_finale['statut'] == statut_final:
                print(f"   🎉 Test complet réussi!")
                return True
            else:
                print(f"   ❌ Problème final: Attendu '{statut_final}', trouvé '{commande_finale['statut']}'")
                return False
        else:
            print(f"   ❌ Échec de la mise à jour finale")
            return False
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if db:
            db.close()

def test_update_commande_status_function():
    """Test de la fonction update_commande_status du dialogue de réception"""
    print("\n🔧 Test de la fonction update_commande_status")
    print("=" * 50)
    
    try:
        db = Database()
        db.connect()
        
        # Simuler les données d'une commande
        commande_data = {'id_commande': 17}  # ID de la commande de test
        
        # Importer et tester la logique du dialogue
        from APP.models.ligne_commande_repository import LigneCommandeRepository
        from APP.models.commande_repository import CommandeRepository
        
        ligne_repo = LigneCommandeRepository(db)
        commande_repo = CommandeRepository(db)
        
        # Récupérer toutes les lignes de la commande
        lignes = ligne_repo.get_lignes_by_commande(commande_data['id_commande'])
        
        print(f"   📋 Analyse de {len(lignes)} ligne(s)")
        
        # Calculer le statut global
        total_lignes = len(lignes)
        lignes_completes = 0
        lignes_partielles = 0
        
        for ligne in lignes:
            quantite_commandee = ligne.get('quantite_commandee', 0)
            quantite_recue = ligne.get('quantite_recue', 0)
            quantite_defectueuse = ligne.get('quantite_defectueuse', 0)
            
            print(f"     Ligne: Cmd={quantite_commandee}, Reçue={quantite_recue}, Déf={quantite_defectueuse}")
            
            if quantite_recue + quantite_defectueuse >= quantite_commandee:
                lignes_completes += 1
            elif quantite_recue + quantite_defectueuse > 0:
                lignes_partielles += 1
        
        # Déterminer le nouveau statut
        if lignes_completes == total_lignes:
            nouveau_statut = 'Livree'
        elif lignes_completes > 0 or lignes_partielles > 0:
            nouveau_statut = 'Partielle'
        else:
            nouveau_statut = 'Envoyee'
        
        print(f"   📊 Lignes complètes: {lignes_completes}/{total_lignes}")
        print(f"   📊 Lignes partielles: {lignes_partielles}")
        print(f"   🎯 Statut calculé: {nouveau_statut}")
        
        # Mettre à jour la commande
        update_data = {'statut': nouveau_statut}
        if nouveau_statut == 'Livree':
            update_data['date_livraison_reelle'] = datetime.now().strftime('%Y-%m-%d')
        
        success = commande_repo.update_commande(commande_data['id_commande'], update_data)
        print(f"   {'✅' if success else '❌'} Mise à jour: {success}")
        
        return success
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    print("🚀 Test complet du processus de réception")
    print("=" * 60)
    
    # Test de la fonction de mise à jour
    success1 = test_update_commande_status_function()
    
    # Test complet du processus
    success2 = test_reception_complete()
    
    if success1 and success2:
        print("\n🎉 TOUS LES TESTS RÉUSSIS!")
        print("\n✅ Le processus de réception fonctionne correctement")
        print("✅ La mise à jour du statut est opérationnelle")
        print("\n📋 Le problème pourrait venir de:")
        print("1. Données de test insuffisantes")
        print("2. Interface utilisateur non synchronisée")
        print("3. Cache ou rafraîchissement de l'affichage")
    else:
        print("\n💥 Certains tests ont échoué")
        print("Le problème nécessite une investigation plus approfondie")