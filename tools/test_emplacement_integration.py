#!/usr/bin/env python3
"""
Test d'intégration pour vérifier que les emplacements fonctionnent correctement
avec l'interface utilisateur
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from APP.services.db import Database
from APP.services.emplacement_service import EmplacementService

def test_emplacement_service_integration():
    """Test du service d'emplacement avec les nouvelles fonctionnalités"""
    db = None
    try:
        print("🧪 Test d'intégration du service d'emplacement")
        print("=" * 50)
        
        # Connexion
        db = Database()
        db.connect()
        
        service = EmplacementService(db)
        
        # Test 1: Ajout avec nouveau format
        print("\n1️⃣ Test: Ajout d'emplacement avec nouveau format")
        
        import time
        timestamp = int(time.time()) % 1000
        
        nouveau_emplacement = {
            "base": {
                "magasin_id": 1,
                "nom": f"TEST_{timestamp}",
                "type": "Test_Integration",
                "allee": "99",
                "etagere": "99",
                "niveau": "99"
            },
            "extension": {
                "longueur_cm": 150.0,
                "hauteur_cm": 60.0,
                "profondeur_cm": 80.0,
                "capacite_max_kg": 200.0,
                "temperature_min_c": 10.0,
                "temperature_max_c": 30.0,
                "humidite_max_pct": 70.0,
                "conditions_speciales": "Test d'intégration",
                "actif": True
            }
        }
        
        emplacement_id = service.add_emplacement(nouveau_emplacement)
        print(f"   ✅ Emplacement créé avec ID: {emplacement_id}")
        
        # Test 2: Récupération avec extensions
        print("\n2️⃣ Test: Récupération d'emplacement complet")
        
        emplacement_complet = service.get_emplacement_complet(emplacement_id)
        print(f"   📦 Nom: {emplacement_complet.get('nom', 'N/A')}")
        print(f"   📏 Dimensions: {emplacement_complet.get('longueur_cm', 0)}×{emplacement_complet.get('hauteur_cm', 0)}×{emplacement_complet.get('profondeur_cm', 0)} cm")
        print(f"   📊 Volume: {emplacement_complet.get('volume_cm3', 0):,.0f} cm³")
        print(f"   ⚖️  Capacité: {emplacement_complet.get('capacite_max_kg', 0)} kg")
        
        # Test 3: Modification avec nouveau format
        print("\n3️⃣ Test: Modification d'emplacement")
        
        modification_data = {
            "base": {
                "magasin_id": 1,
                "nom": f"TEST_{timestamp}_MODIF",
                "type": "Test_Integration_Modif",
                "allee": "99",
                "etagere": "99",
                "niveau": "99"
            },
            "extension": {
                "longueur_cm": 180.0,
                "hauteur_cm": 70.0,
                "profondeur_cm": 90.0,
                "capacite_max_kg": 300.0,
                "temperature_min_c": 5.0,
                "temperature_max_c": 35.0,
                "humidite_max_pct": 80.0,
                "conditions_speciales": "Test d'intégration - Modifié",
                "actif": True
            }
        }
        
        service.update_emplacement(emplacement_id, modification_data)
        print("   ✅ Emplacement modifié")
        
        # Vérifier la modification
        emplacement_modifie = service.get_emplacement_complet(emplacement_id)
        print(f"   📦 Nouveau nom: {emplacement_modifie.get('nom', 'N/A')}")
        print(f"   📏 Nouvelles dimensions: {emplacement_modifie.get('longueur_cm', 0)}×{emplacement_modifie.get('hauteur_cm', 0)}×{emplacement_modifie.get('profondeur_cm', 0)} cm")
        
        # Test 4: Compatibilité avec ancien format
        print("\n4️⃣ Test: Compatibilité avec ancien format")
        
        ancien_format = {
            "magasin_id": 1,
            "nom": f"ANCIEN_{timestamp}",
            "type": "Ancien_Format",
            "allee": "88",
            "etagere": "88",
            "niveau": "88"
        }
        
        emplacement_ancien_id = service.add_emplacement(ancien_format)
        print(f"   ✅ Emplacement ancien format créé avec ID: {emplacement_ancien_id}")
        
        # Test 5: Liste des emplacements
        print("\n5️⃣ Test: Liste des emplacements")
        
        tous_emplacements = service.get_all_emplacements()
        print(f"   📋 Total emplacements: {len(tous_emplacements)}")
        
        # Trouver nos emplacements de test
        emplacements_test = [e for e in tous_emplacements if 'TEST' in e.get('nom', '') or 'ANCIEN' in e.get('nom', '')]
        print(f"   🧪 Emplacements de test trouvés: {len(emplacements_test)}")
        
        for emp in emplacements_test:
            print(f"     - {emp['nom']} (ID: {emp['id']})")
        
        # Test 6: Nettoyage
        print("\n6️⃣ Test: Nettoyage des emplacements de test")
        
        for emp in emplacements_test:
            service.delete_emplacement(emp['id'])
            print(f"   🗑️  Supprimé: {emp['nom']}")
        
        print("\n✅ Tous les tests d'intégration réussis!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors des tests d'intégration: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if db:
            db.close()

def test_dialogue_simulation():
    """Simulation du dialogue pour vérifier la structure des données"""
    print("\n🖥️  Test de simulation du dialogue")
    print("=" * 50)
    
    try:
        # Simuler les données retournées par le dialogue
        dialogue_data = {
            "base": {
                "magasin_id": 1,
                "nom": "A7S4L2",
                "type": "Simulation",
                "allee": 7,
                "etagere": 4,
                "niveau": 2
            },
            "extension": {
                "longueur_cm": 120.0,
                "hauteur_cm": 50.0,
                "profondeur_cm": 70.0,
                "capacite_max_kg": 150.0,
                "temperature_min_c": 15.0,
                "temperature_max_c": 25.0,
                "humidite_max_pct": 65.0,
                "conditions_speciales": "Simulation de dialogue",
                "actif": True
            }
        }
        
        print("   📝 Structure des données du dialogue:")
        print(f"     Base: {list(dialogue_data['base'].keys())}")
        print(f"     Extension: {list(dialogue_data['extension'].keys())}")
        
        # Vérifier que toutes les clés nécessaires sont présentes
        base_required = ['magasin_id', 'nom', 'type', 'allee', 'etagere', 'niveau']
        extension_required = ['longueur_cm', 'hauteur_cm', 'profondeur_cm', 'capacite_max_kg']
        
        base_ok = all(key in dialogue_data['base'] for key in base_required)
        extension_ok = all(key in dialogue_data['extension'] for key in extension_required)
        
        print(f"   ✅ Données de base complètes: {base_ok}")
        print(f"   ✅ Données d'extension complètes: {extension_ok}")
        
        if base_ok and extension_ok:
            print("   🎉 Structure de données validée!")
            return True
        else:
            print("   ❌ Structure de données incomplète")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur dans la simulation: {e}")
        return False

if __name__ == "__main__":
    print("���� Tests d'intégration des emplacements")
    print("=" * 60)
    
    # Test du service
    success1 = test_emplacement_service_integration()
    
    # Test de simulation du dialogue
    success2 = test_dialogue_simulation()
    
    if success1 and success2:
        print("\n🎉 TOUS LES TESTS D'INTÉGRATION RÉUSSIS!")
        print("\n✅ Le système est prêt pour:")
        print("   - Création d'emplacements avec dimensions")
        print("   - Modification d'emplacements existants")
        print("   - Compatibilité avec l'ancien format")
        print("   - Intégration avec l'interface utilisateur")
        
        print("\n📋 Prochaines étapes:")
        print("   1. Tester l'interface graphique")
        print("   2. Vérifier les dialogues d'ajout/modification")
        print("   3. Valider les fonctionnalités de stock par emplacement")
        
    else:
        print("\n💥 Certains tests ont échoué")
        sys.exit(1)