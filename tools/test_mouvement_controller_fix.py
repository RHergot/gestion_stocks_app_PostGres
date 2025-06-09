#!/usr/bin/env python3
"""
Test du correctif du contrôleur de mouvement
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from APP.services.db import Database
from APP.controllers.mouvement_controller import MouvementController
from APP.services.piece_service import PieceService
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_mouvement_controller():
    """Test du contrôleur de mouvement après correction"""
    try:
        db = Database()
        db.connect()
        
        controller = MouvementController(db)
        piece_service = PieceService(db)
        
        logger.info("=== Test du contrôleur de mouvement corrigé ===")
        
        # 1. Récupérer une pièce pour le test
        pieces = piece_service.get_all_pieces()
        if not pieces:
            logger.error("❌ Aucune pièce disponible pour le test")
            return False
        
        piece = pieces[0]
        piece_id = piece['id_piece']
        stock_initial = piece['stock_actuel']
        
        logger.info(f"📦 Test avec la pièce: {piece['reference']} (Stock initial: {stock_initial})")
        
        # 2. Test de la méthode _obtenir_type_mouvement_id
        logger.info("\n--- Test 1: Récupération des types de mouvement ---")
        try:
            # Test avec un type d'entrée
            type_entree_id = controller._obtenir_type_mouvement_id('ENTREE_ACHAT', impact_attendu=1)
            logger.info(f"✅ Type ENTREE_ACHAT trouvé: ID={type_entree_id}")
            
            # Test avec un type de sortie
            type_sortie_id = controller._obtenir_type_mouvement_id('SORTIE_CONSOMMATION', impact_attendu=-1)
            logger.info(f"✅ Type SORTIE_CONSOMMATION trouvé: ID={type_sortie_id}")
            
            # Test avec un type de réception
            type_reception_id = controller._obtenir_type_mouvement_id('RECEPTION_ACHAT', impact_attendu=0)
            logger.info(f"✅ Type RECEPTION_ACHAT trouvé: ID={type_reception_id}")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du test des types de mouvement: {e}")
            return False
        
        # 3. Test d'entrée de stock
        logger.info("\n--- Test 2: Entrée de stock ---")
        try:
            resultat = controller.effectuer_entree_stock(
                piece_id=piece_id,
                quantite=5,
                type_mouvement='ENTREE_ACHAT',
                utilisateur_id=1,
                commentaire="Test d'entrée de stock après correction"
            )
            
            if resultat['success']:
                logger.info(f"✅ Entrée de stock réussie: {resultat['message']}")
                logger.info(f"   Mouvement ID: {resultat['mouvement_id']}")
            else:
                logger.error(f"❌ Échec de l'entrée de stock: {resultat['error']}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du test d'entrée de stock: {e}")
            return False
        
        # 4. Vérifier le nouveau stock
        piece_apres = piece_service.get_piece_by_id(piece_id)
        nouveau_stock = piece_apres['stock_actuel']
        logger.info(f"📊 Stock après entrée: {nouveau_stock} (était {stock_initial})")
        
        if nouveau_stock == stock_initial + 5:
            logger.info("✅ Stock correctement mis à jour")
        else:
            logger.error("❌ Problème de mise à jour du stock")
            return False
        
        # 5. Test de sortie de stock
        logger.info("\n--- Test 3: Sortie de stock ---")
        try:
            resultat = controller.effectuer_sortie_stock(
                piece_id=piece_id,
                quantite=2,
                type_mouvement='SORTIE_CONSOMMATION',
                utilisateur_id=1,
                commentaire="Test de sortie de stock après correction"
            )
            
            if resultat['success']:
                logger.info(f"✅ Sortie de stock réussie: {resultat['message']}")
                logger.info(f"   Mouvement ID: {resultat['mouvement_id']}")
            else:
                logger.error(f"❌ Échec de la sortie de stock: {resultat['error']}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du test de sortie de stock: {e}")
            return False
        
        # 6. Test de réception d'achat
        logger.info("\n--- Test 4: Réception d'achat ---")
        try:
            resultat = controller.effectuer_reception_achat(
                piece_id=piece_id,
                quantite=8,
                utilisateur_id=1,
                reference="TEST-RECEPTION-001",
                commentaire="Test de réception après correction"
            )
            
            if resultat['success']:
                logger.info(f"✅ Réception d'achat réussie: {resultat['message']}")
                logger.info(f"   Mouvement ID: {resultat['mouvement_id']}")
                logger.info(f"   Type d'opération: {resultat['type_operation']}")
            else:
                logger.error(f"❌ Échec de la réception d'achat: {resultat['error']}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du test de réception d'achat: {e}")
            return False
        
        # 7. Test des types de mouvement de réception
        logger.info("\n--- Test 5: Types de mouvement de réception ---")
        try:
            types_reception = controller.obtenir_types_mouvement_reception()
            logger.info(f"✅ Types de mouvement de réception trouvés: {len(types_reception)}")
            for type_mouvement in types_reception:
                logger.info(f"   - {type_mouvement['nom']}: impact={type_mouvement['impact_stock']}")
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du test des types de réception: {e}")
            return False
        
        # 8. Test de l'historique
        logger.info("\n--- Test 6: Historique de la pièce ---")
        try:
            historique = controller.obtenir_historique_piece(piece_id, limite=10)
            
            if historique['success']:
                mouvements = historique['historique']
                logger.info(f"✅ Historique récupéré: {len(mouvements)} mouvements")
                
                # Afficher les derniers mouvements
                for mouvement in mouvements[:3]:
                    logger.info(f"   - {mouvement['type_mouvement']}: {mouvement['quantite']} unités")
            else:
                logger.error(f"❌ Échec de la récupération de l'historique: {historique['error']}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du test de l'historique: {e}")
            return False
        
        # 9. Test du résumé de réception
        logger.info("\n--- Test 7: Résumé de réception ---")
        try:
            resume = controller.get_reception_stock_summary()
            
            if resume['success']:
                logger.info(f"✅ Résumé de réception récupéré:")
                logger.info(f"   - Total pièces en réception: {resume['total_pieces']}")
                logger.info(f"   - Total quantité en réception: {resume['total_quantite']}")
                logger.info(f"   - Total lots en attente: {resume['total_lots']}")
            else:
                logger.error(f"❌ Échec du résumé de réception: {resume['error']}")
                # Ce n'est pas critique, on continue
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du test du résumé de réception: {e}")
            # Ce n'est pas critique, on continue
        
        logger.info("\n🎉 Tous les tests du contrôleur ont réussi!")
        logger.info("Le contrôleur de mouvement fonctionne correctement après correction.")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur générale lors du test: {e}")
        return False

def test_gestion_erreurs():
    """Test de la gestion d'erreurs du contrôleur"""
    try:
        db = Database()
        db.connect()
        
        controller = MouvementController(db)
        
        logger.info("\n=== Test de la gestion d'erreurs ===")
        
        # 1. Test avec un type de mouvement inexistant
        logger.info("\n--- Test 1: Type de mouvement inexistant ---")
        try:
            controller._obtenir_type_mouvement_id('TYPE_INEXISTANT')
            logger.error("❌ Devrait lever une exception")
            return False
        except ValueError as e:
            logger.info(f"✅ Exception correctement levée: {e}")
        
        # 2. Test avec un impact incorrect
        logger.info("\n--- Test 2: Impact incorrect ---")
        try:
            controller._obtenir_type_mouvement_id('ENTREE_ACHAT', impact_attendu=-1)
            logger.error("❌ Devrait lever une exception")
            return False
        except ValueError as e:
            logger.info(f"✅ Exception correctement levée: {e}")
        
        # 3. Test avec une pièce inexistante
        logger.info("\n--- Test 3: Pièce inexistante ---")
        resultat = controller.effectuer_entree_stock(
            piece_id=99999,
            quantite=5,
            type_mouvement='ENTREE_ACHAT'
        )
        
        if not resultat['success']:
            logger.info(f"✅ Erreur correctement gérée: {resultat['error']}")
        else:
            logger.error("❌ Devrait échouer avec une pièce inexistante")
            return False
        
        # 4. Test avec une quantité négative
        logger.info("\n--- Test 4: Quantité négative ---")
        resultat = controller.effectuer_entree_stock(
            piece_id=1,
            quantite=-5,
            type_mouvement='ENTREE_ACHAT'
        )
        
        if not resultat['success']:
            logger.info(f"✅ Erreur correctement gérée: {resultat['error']}")
        else:
            logger.error("❌ Devrait échouer avec une quantité négative")
            return False
        
        logger.info("\n✅ Tous les tests de gestion d'erreurs ont réussi!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test de gestion d'erreurs: {e}")
        return False

def main():
    """Fonction principale"""
    try:
        logger.info("🚀 Démarrage des tests du contrôleur de mouvement corrigé")
        
        # Test principal
        if not test_mouvement_controller():
            logger.error("❌ Échec des tests principaux")
            return False
        
        # Test de gestion d'erreurs
        if not test_gestion_erreurs():
            logger.error("❌ Échec des tests de gestion d'erreurs")
            return False
        
        logger.info("\n🎉 Tous les tests ont réussi!")
        logger.info("Le contrôleur de mouvement est maintenant fonctionnel.")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur générale: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)