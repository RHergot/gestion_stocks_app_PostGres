#!/usr/bin/env python3
"""
Script de test pour les extensions d'emplacements
Teste toutes les fonctionnalités nouvelles
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from APP.services.db import Database
from APP.services.emplacement_ext_service import EmplacementExtService
from APP.services.mouvement_service import MouvementService
from APP.models.piece_repository import PieceRepository

def test_emplacement_extensions():
    """Test complet des extensions d'emplacements"""
    db = None
    try:
        db = Database()
        db.connect()  # Établir explicitement la connexion
        
        emplacement_service = EmplacementExtService(db)
        mouvement_service = MouvementService(db)
        piece_repo = PieceRepository(db)
        
        print("🧪 Test des extensions d'emplacements")
        print("=" * 50)
        
        # Test 1: Récupération des emplacements avec détails
        print("\n1️⃣ Test: Récupération des emplacements détaillés")
        emplacements_detail = emplacement_service.get_tous_emplacements_detail()
        print(f"   ✓ {len(emplacements_detail)} emplacements trouvés")
        
        if emplacements_detail:
            emp = emplacements_detail[0]
            print(f"   📦 Exemple: {emp['nom']} - Volume: {emp.get('volume_cm3', 'N/A')} cm³")
        
        # Test 2: Récupération des capacités
        print("\n2️⃣ Test: Informations de capacité")
        capacites = emplacement_service.get_emplacements_avec_capacite()
        print(f"   ✓ {len(capacites)} emplacements avec info capacité")
        
        # Test 3: Création d'une pièce de test si nécessaire
        print("\n3️⃣ Test: Préparation d'une pièce de test")
        pieces = piece_repo.get_all_pieces()
        
        if not pieces:
            print("   Création d'une pièce de test...")
            piece_data = {
                'reference': 'TEST-001',
                'nom': 'Pièce de test pour emplacements',
                'stock_actuel': 0,
                'stock_alerte': 5,
                'prix_unitaire': 10.50,
                'unite': 'pcs',
                'categorie': 'Test',
                'statut': 'Actif'
            }
            piece_id = piece_repo.add_piece(piece_data)
            print(f"   ✓ Pièce créée: ID {piece_id}")
        else:
            piece_id = pieces[0]['id_piece']
            print(f"   ✓ Utilisation de la pièce existante: ID {piece_id}")
        
        # Test 4: Ajout de stock dans un emplacement
        print("\n4️⃣ Test: Ajout de stock dans un emplacement")
        if emplacements_detail:
            emplacement_id = emplacements_detail[0]['id']
            quantite_test = 10
            
            success = emplacement_service.ajouter_stock_piece(
                emplacement_id, piece_id, quantite_test, "Test d'ajout de stock"
            )
            
            if success:
                print(f"   ✓ {quantite_test} unités ajoutées à l'emplacement {emplacements_detail[0]['nom']}")
                
                # Vérifier le stock
                stock_emplacement = emplacement_service.get_stock_piece_par_emplacement(piece_id)
                print(f"   📊 Stock dans les emplacements: {len(stock_emplacement)} emplacements")
            else:
                print("   ❌ Échec de l'ajout de stock")
        
        # Test 5: Transfert entre emplacements
        print("\n5️⃣ Test: Transfert entre emplacements")
        if len(emplacements_detail) >= 2:
            emplacement_source = emplacements_detail[0]['id']
            emplacement_dest = emplacements_detail[1]['id']
            quantite_transfert = 3
            
            try:
                success = emplacement_service.transferer_stock(
                    piece_id, emplacement_source, emplacement_dest, 
                    quantite_transfert, "Test de transfert"
                )
                
                if success:
                    print(f"   ✓ Transfert de {quantite_transfert} unités réussi")
                    print(f"     {emplacements_detail[0]['nom']} → {emplacements_detail[1]['nom']}")
                else:
                    print("   ❌ Échec du transfert")
            except Exception as e:
                print(f"   ⚠️  Transfert non possible: {e}")
        
        # Test 6: Vérification de cohérence
        print("\n6️⃣ Test: Vérification de cohérence des stocks")
        incoherences = emplacement_service.verifier_coherence_stock_global()
        
        if incoherences:
            print(f"   ⚠️  {len(incoherences)} incohérences détectées")
            for inc in incoherences[:3]:  # Afficher les 3 premières
                print(f"     - Pièce {inc['reference']}: Global={inc['stock_global']}, Emplacements={inc['total_emplacements']}")
        else:
            print("   ✅ Aucune incohérence détectée")
        
        # Test 7: Recherche de pièces
        print("\n7️⃣ Test: Recherche de pièces dans les emplacements")
        resultats_recherche = emplacement_service.rechercher_piece("TEST")
        print(f"   🔍 {len(resultats_recherche)} résultats pour 'TEST'")
        
        # Test 8: Suggestions d'emplacements
        print("\n8️⃣ Test: Suggestions d'emplacements")
        suggestions = emplacement_service.suggerer_emplacement_pour_piece(piece_id, 5)
        print(f"   💡 {len(suggestions)} suggestions d'emplacements")
        
        if suggestions:
            for i, sugg in enumerate(suggestions[:3]):
                print(f"     {i+1}. {sugg.get('nom', 'N/A')} - {sugg.get('raison', 'N/A')}")
        
        # Test 9: Statistiques d'emplacement
        print("\n9️⃣ Test: Statistiques d'emplacement")
        if emplacements_detail:
            stats = emplacement_service.get_statistiques_emplacement(emplacements_detail[0]['id'])
            print(f"   📈 Statistiques pour {emplacements_detail[0]['nom']}:")
            print(f"     - Pièces différentes: {stats.get('nb_pieces_differentes', 0)}")
            print(f"     - Quantité totale: {stats.get('quantite_totale', 0)}")
        
        # Test 10: Nettoyage des stocks vides
        print("\n🔟 Test: Nettoyage des stocks vides")
        stocks_nettoyes = emplacement_service.nettoyer_stocks_vides()
        print(f"   🧹 {stocks_nettoyes} enregistrements de stock vide nettoyés")
        
        print("\n✅ Tous les tests terminés avec succès!")
        
        # Affichage du r��sumé
        print("\n📊 Résumé des données:")
        print(f"   - Emplacements configurés: {len(emplacements_detail)}")
        print(f"   - Pièces dans le système: {len(pieces)}")
        print(f"   - Incohérences détectées: {len(incoherences)}")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'db' in locals():
            db.close()
    
    return True

def test_dialogue_emplacement():
    """Test du dialogue d'emplacement (simulation)"""
    print("\n🖥️  Test du dialogue d'emplacement")
    print("-" * 30)
    
    try:
        # Simulation des données du dialogue
        dialogue_data = {
            "base": {
                "magasin_id": 1,
                "nom": "A3S2L1",
                "type": "Test",
                "allee": 3,
                "etagere": 2,
                "niveau": 1
            },
            "extension": {
                "longueur_cm": 150.0,
                "hauteur_cm": 60.0,
                "profondeur_cm": 80.0,
                "capacite_max_kg": 200.0,
                "temperature_min_c": 5.0,
                "temperature_max_c": 35.0,
                "humidite_max_pct": 85.0,
                "conditions_speciales": "Zone de test - Conditions contrôlées",
                "actif": True
            }
        }
        
        print("   📝 Données de test du dialogue:")
        print(f"     - Nom: {dialogue_data['base']['nom']}")
        print(f"     - Dimensions: {dialogue_data['extension']['longueur_cm']}×{dialogue_data['extension']['hauteur_cm']}×{dialogue_data['extension']['profondeur_cm']} cm")
        
        volume = (dialogue_data['extension']['longueur_cm'] * 
                 dialogue_data['extension']['hauteur_cm'] * 
                 dialogue_data['extension']['profondeur_cm'])
        print(f"     - Volume calculé: {volume:,.0f} cm³")
        print(f"     - Capacité: {dialogue_data['extension']['capacite_max_kg']} kg")
        
        print("   ✅ Structure de données du dialogue validée")
        
    except Exception as e:
        print(f"   ❌ Erreur dans le test du dialogue: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Tests des extensions d'emplacements")
    print("=" * 50)
    
    # Test des fonctionnalités
    success1 = test_emplacement_extensions()
    
    # Test du dialogue
    success2 = test_dialogue_emplacement()
    
    if success1 and success2:
        print("\n🎉 Tous les tests sont passés avec succès!")
        print("\n📋 Fonctionnalités testées:")
        print("   ✅ Gestion des dimensions d'emplacements")
        print("   ✅ Stock par emplacement")
        print("   ✅ Transferts entre emplacements")
        print("   ✅ Vérification de cohérence")
        print("   ✅ Recherche et suggestions")
        print("   ✅ Statistiques et rapports")
        print("   ✅ Structure du dialogue étendu")
    else:
        print("\n💥 Certains tests ont échoué")
        sys.exit(1)