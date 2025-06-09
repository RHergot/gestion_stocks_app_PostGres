#!/usr/bin/env python3
"""
Script pour appliquer la migration des statuts de mouvement
et tester le nouveau workflow de réception
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from APP.services.db import Database
from APP.services.mouvement_service import MouvementService
from APP.services.reception_workflow_service import ReceptionWorkflowService
from APP.services.piece_service import PieceService
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def apply_migration():
    """Applique la migration des statuts de mouvement"""
    try:
        db = Database()
        db.connect()  # Établir la connexion explicitement
        
        logger.info("=== Application de la migration des statuts de mouvement ===")
        
        # Lire et exécuter le script de migration
        with open('database/mouvement_statut_migration.sql', 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        with db.conn.cursor() as cur:
            # Exécuter la migration
            cur.execute(migration_sql)
            db.conn.commit()
            
        logger.info("✅ Migration appliquée avec succès")
        
        # Vérifier que la colonne a été ajoutée
        with db.conn.cursor() as cur:
            cur.execute("""
                SELECT column_name, data_type, column_default 
                FROM information_schema.columns 
                WHERE table_name = 'mouvement_stock' 
                AND column_name = 'statut_mouvement';
            """)
            result = cur.fetchone()
            
            if result:
                logger.info(f"✅ Colonne statut_mouvement créée: {result}")
            else:
                logger.error("❌ Colonne statut_mouvement non trouvée")
                return False
        
        # Vérifier les nouvelles vues
        with db.conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.views 
                WHERE table_name IN ('v_mouvements_en_attente', 'v_dashboard_reception');
            """)
            vues = cur.fetchall()
            logger.info(f"✅ Vues créées: {[v[0] for v in vues]}")
        
        # Vérifier les nouvelles fonctions
        with db.conn.cursor() as cur:
            cur.execute("""
                SELECT routine_name 
                FROM information_schema.routines 
                WHERE routine_name IN ('confirmer_mouvement_en_attente', 'annuler_mouvement_en_attente')
                AND routine_type = 'FUNCTION';
            """)
            fonctions = cur.fetchall()
            logger.info(f"✅ Fonctions créées: {[f[0] for f in fonctions]}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'application de la migration: {e}")
        return False

def test_nouveau_workflow():
    """Teste le nouveau workflow avec les statuts"""
    try:
        db = Database()
        db.connect()  # Établir la connexion explicitement
        mouvement_service = MouvementService(db)
        reception_service = ReceptionWorkflowService(db)
        piece_service = PieceService(db)
        
        logger.info("\n=== Test du nouveau workflow de réception ===")
        
        # 1. Récupérer une pièce existante pour le test
        pieces = piece_service.get_all_pieces()
        if not pieces:
            logger.error("❌ Aucune pièce trouvée pour le test")
            return False
        
        piece = pieces[0]
        piece_id = piece['id_piece']
        stock_initial = piece['stock_actuel']
        
        logger.info(f"📦 Test avec la pièce: {piece['reference']} (Stock initial: {stock_initial})")
        
        # 2. Créer un lot de réception (mouvement EN_ATTENTE)
        logger.info("\n--- Étape 1: Création d'un lot de réception ---")
        lot_id = reception_service.creer_lot_reception(
            piece_id=piece_id,
            quantite_recue=5,
            utilisateur_id=1,
            commentaire="Test du nouveau workflow avec statuts"
        )
        logger.info(f"✅ Lot de réception créé: {lot_id}")
        
        # 3. Vérifier que le stock n'a pas changé
        stock_apres_reception = piece_service.get_piece_by_id(piece_id)['stock_actuel']
        logger.info(f"📊 Stock après réception: {stock_apres_reception} (doit être égal à {stock_initial})")
        
        if stock_apres_reception != stock_initial:
            logger.error(f"❌ ERREUR: Le stock a changé lors de la réception!")
            return False
        else:
            logger.info("✅ Correct: Le stock n'a pas changé lors de la réception")
        
        # 4. Vérifier les mouvements en attente
        logger.info("\n--- Étape 2: Vérification des mouvements en attente ---")
        mouvements_attente = mouvement_service.get_mouvements_en_attente()
        logger.info(f"📋 Mouvements en attente: {len(mouvements_attente)}")
        
        mouvement_test = None
        for mouvement in mouvements_attente:
            if mouvement['piece_reference'] == piece['reference']:
                mouvement_test = mouvement
                break
        
        if mouvement_test:
            logger.info(f"✅ Mouvement en attente trouvé: ID={mouvement_test['id']}")
        else:
            logger.error("❌ Mouvement en attente non trouvé")
            return False
        
        # 5. Confirmer la réception
        logger.info("\n--- Étape 3: Confirmation de la réception ---")
        success = reception_service.confirmer_reception_lot(
            lot_id=lot_id,
            utilisateur_id=1,
            commentaire_confirmation="Réception validée par le test"
        )
        
        if success:
            logger.info("✅ Réception confirmée avec succès")
        else:
            logger.error("❌ Erreur lors de la confirmation")
            return False
        
        # 6. Vérifier que le stock a été mis à jour
        stock_apres_confirmation = piece_service.get_piece_by_id(piece_id)['stock_actuel']
        logger.info(f"📊 Stock après confirmation: {stock_apres_confirmation} (doit être {stock_initial + 5})")
        
        if stock_apres_confirmation == stock_initial + 5:
            logger.info("✅ Correct: Le stock a été mis à jour après confirmation")
        else:
            logger.error(f"❌ ERREUR: Stock incorrect après confirmation!")
            return False
        
        # 7. Vérifier le dashboard
        logger.info("\n--- Étape 4: Vérification du dashboard ---")
        dashboard = reception_service.get_dashboard_reception_detaille()
        logger.info("📊 Dashboard de réception:")
        for indicateur, data in dashboard.items():
            logger.info(f"   {indicateur}: {data['valeur']} - {data['description']}")
        
        # 8. Test d'annulation (créer un nouveau lot pour tester)
        logger.info("\n--- Étape 5: Test d'annulation ---")
        lot_id_2 = reception_service.creer_lot_reception(
            piece_id=piece_id,
            quantite_recue=3,
            utilisateur_id=1,
            commentaire="Test d'annulation"
        )
        
        # Annuler immédiatement
        success_annulation = reception_service.annuler_reception_lot(
            lot_id=lot_id_2,
            utilisateur_id=1,
            raison_annulation="Test d'annulation du workflow"
        )
        
        if success_annulation:
            logger.info("✅ Annulation testée avec succès")
        else:
            logger.error("❌ Erreur lors du test d'annulation")
        
        # V��rifier que le stock n'a pas changé
        stock_final = piece_service.get_piece_by_id(piece_id)['stock_actuel']
        if stock_final == stock_apres_confirmation:
            logger.info("✅ Correct: Le stock n'a pas changé après annulation")
        else:
            logger.error("❌ ERREUR: Le stock a changé après annulation!")
        
        logger.info("\n🎉 Test du nouveau workflow terminé avec succès!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test: {e}")
        return False

def afficher_resume():
    """Affiche un résumé du nouveau système"""
    logger.info("\n" + "="*60)
    logger.info("RÉSUMÉ DU NOUVEAU SYSTÈME DE STATUTS DE MOUVEMENT")
    logger.info("="*60)
    logger.info("""
🔄 WORKFLOW DE RÉCEPTION AMÉLIORÉ:

1. RÉCEPTION INITIALE (Statut: EN_ATTENTE)
   - Création d'un lot de réception
   - Mouvement tracé mais SANS impact sur le stock
   - Les pièces sont "en réception" mais pas encore "en stock"

2. CONFIRMATION DE RÉCEPTION (Statut: CONFIRME)
   - Validation par le magasinier
   - Application de l'impact sur le stock de la pièce
   - Passage du lot en statut "PRET_STOCKAGE"

3. MISE EN STOCK PHYSIQUE
   - Transfert depuis la zone de réception vers l'emplacement final
   - Impact sur les stocks par emplacement
   - Passage du lot en statut "STOCKE"

✅ AVANTAGES:
   - Évite le double encodage
   - Traçabilité complète du processus
   - Séparation claire entre réception et stockage
   - Possibilité d'annulation avant confirmation
   - Dashboard de suivi en temps réel

📊 NOUVEAUX INDICATEURS:
   - Lots en attente de confirmation
   - Mouvements en attente
   - Temps moyen d'attente
   - Quantités en zone de réception
""")

def main():
    """Fonction principale"""
    try:
        logger.info("🚀 Démarrage de l'application de la migration des statuts de mouvement")
        
        # 1. Appliquer la migration
        if not apply_migration():
            logger.error("❌ Échec de l'application de la migration")
            return False
        
        # 2. Tester le nouveau workflow
        if not test_nouveau_workflow():
            logger.error("❌ Échec du test du nouveau workflow")
            return False
        
        # 3. Afficher le résumé
        afficher_resume()
        
        logger.info("\n🎉 Migration et tests terminés avec succès!")
        logger.info("Le système de statuts de mouvement est maintenant opérationnel.")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur générale: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)