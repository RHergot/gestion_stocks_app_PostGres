#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test du workflow de réception complet
Démontre l'utilisation des nouveaux types de mouvements de réception
"""

import os
from dotenv import load_dotenv
from APP.services.db import Database
from APP.controllers.mouvement_controller import MouvementController

def test_reception_workflow():
    """Test complet du workflow de réception"""
    load_dotenv()
    
    print("=== Test du Workflow de Réception ===\n")
    
    # Initialiser la base de données et le contrôleur
    db = Database()
    db.connect()
    
    mouvement_controller = MouvementController(db)
    
    try:
        # Données de test
        piece_id = 1  # Utiliser une pièce existante
        quantite_recue = 50
        emplacement_reception_id = 1  # Zone de réception
        emplacement_stockage_id = 2   # Zone de stockage
        utilisateur_id = 1
        reference_document = "CMD-2025-001"
        
        print("📦 Étape 1: Réception d'achat (zone de réception)")
        print(f"   Pièce ID: {piece_id}, Quantité: {quantite_recue}")
        
        # 1. Réception d'achat (impact neutre)
        result_reception = mouvement_controller.effectuer_reception_achat(
            piece_id=piece_id,
            quantite=quantite_recue,
            emplacement_reception_id=emplacement_reception_id,
            utilisateur_id=utilisateur_id,
            reference=reference_document,
            commentaire="Test workflow - Réception marchandises",
            cout_unitaire=15.50
        )
        
        if result_reception['success']:
            print(f"   ✅ {result_reception['message']}")
            print(f"   📝 Mouvement ID: {result_reception['mouvement_id']}")
        else:
            print(f"   ❌ Erreur: {result_reception['error']}")
            return
        
        print("\n🏪 Étape 2: Mise en stock (zone de stockage)")
        print(f"   Quantité mise en stock: {quantite_recue}")
        
        # 2. Mise en stock (impact positif)
        result_mise_en_stock = mouvement_controller.effectuer_mise_en_stock(
            piece_id=piece_id,
            quantite=quantite_recue,
            emplacement_stockage_id=emplacement_stockage_id,
            utilisateur_id=utilisateur_id,
            reference=reference_document,
            commentaire="Test workflow - Mise en stock depuis réception"
        )
        
        if result_mise_en_stock['success']:
            print(f"   ✅ {result_mise_en_stock['message']}")
            print(f"   📝 Mouvement ID: {result_mise_en_stock['mouvement_id']}")
        else:
            print(f"   ❌ Erreur: {result_mise_en_stock['error']}")
            return
        
        print("\n📊 Étape 3: Validation du workflow")
        
        # 3. Valider la cohérence du workflow
        validation = mouvement_controller.valider_workflow_reception(
            piece_id=piece_id,
            quantite_recue=quantite_recue,
            quantite_mise_en_stock=quantite_recue
        )
        
        if validation['success']:
            print("   ✅ Validation du workflow:")
            print(f"   📈 Total reçu: {validation['total_recu']}")
            print(f"   📦 Total mis en stock: {validation['total_mis_en_stock']}")
            print(f"   📤 Total sorti de réception: {validation['total_sorti_reception']}")
            print(f"   🏪 Quantité en réception: {validation['quantite_en_reception']}")
            print(f"   ✅ Cohérent: {'Oui' if validation['coherent'] else 'Non'}")
        else:
            print(f"   ❌ Erreur validation: {validation['error']}")
        
        print("\n🔄 Étape 4: Test de sortie de réception (optionnel)")
        print("   Simulation d'un retour fournisseur")
        
        # 4. Test de sortie de réception (pour retour fournisseur par exemple)
        quantite_retour = 5
        result_sortie = mouvement_controller.effectuer_sortie_reception(
            piece_id=piece_id,
            quantite=quantite_retour,
            emplacement_reception_id=emplacement_reception_id,
            utilisateur_id=utilisateur_id,
            reference=f"{reference_document}-RETOUR",
            commentaire="Test workflow - Retour fournisseur"
        )
        
        if result_sortie['success']:
            print(f"   ✅ {result_sortie['message']}")
            print(f"   📝 Mouvement ID: {result_sortie['mouvement_id']}")
        else:
            print(f"   ❌ Erreur: {result_sortie['error']}")
        
        print("\n📈 Étape 5: Historique de la pièce")
        
        # 5. Consulter l'historique
        historique = mouvement_controller.obtenir_historique_piece(piece_id, limite=10)
        
        if historique['success']:
            print(f"   📋 Derniers mouvements pour la pièce {piece_id}:")
            for mouvement in historique['historique'][:5]:  # Afficher les 5 derniers
                type_nom = mouvement.get('type_mouvement_nom', 'N/A')
                quantite = mouvement.get('quantite', 0)
                date_mouvement = mouvement.get('date_mouvement', 'N/A')
                commentaire = mouvement.get('commentaire', 'Aucun commentaire')
                print(f"   • {date_mouvement} - {type_nom} - Qté: {quantite}")
                print(f"     💬 {commentaire}")
        
        print("\n🎯 Étape 6: Types de mouvements de réception disponibles")
        
        # 6. Lister les types de mouvements de réception
        types_reception = mouvement_controller.obtenir_types_mouvement_reception()
        print("   📋 Types de mouvements pour le workflow de réception:")
        for type_mouvement in types_reception:
            nom = type_mouvement['nom']
            description = type_mouvement['description']
            impact = type_mouvement['impact_stock']
            impact_str = "Entrée (+)" if impact == 1 else "Sortie (-)" if impact == -1 else "Neutre (0)"
            print(f"   • {nom} - {impact_str}")
            print(f"     📝 {description}")
        
        print("\n✅ Test du workflow de réception terminé avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    test_reception_workflow()
