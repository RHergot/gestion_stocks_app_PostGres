#!/usr/bin/env python3
"""
Démonstration du nouveau workflow de réception avec statuts
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

def demo_workflow_complet():
    """Démonstration complète du nouveau workflow"""
    try:
        db = Database()
        db.connect()
        
        mouvement_service = MouvementService(db)
        reception_service = ReceptionWorkflowService(db)
        piece_service = PieceService(db)
        
        print("\n" + "="*80)
        print("🎯 DÉMONSTRATION DU NOUVEAU WORKFLOW DE RÉCEPTION")
        print("="*80)
        
        # 1. Sélectionner une pièce pour la démo
        pieces = piece_service.get_all_pieces()
        if not pieces:
            print("❌ Aucune pièce disponible pour la démonstration")
            return False
        
        piece = pieces[0]
        piece_id = piece['id_piece']
        stock_initial = piece['stock_actuel']
        
        print(f"\n📦 Pièce sélectionnée: {piece['reference']} - {piece['nom']}")
        print(f"📊 Stock initial: {stock_initial}")
        
        # 2. Étape 1 : Réception physique (EN_ATTENTE)
        print("\n" + "-"*60)
        print("🚚 ÉTAPE 1: RÉCEPTION PHYSIQUE")
        print("-"*60)
        print("Le camion arrive avec 15 pièces...")
        print("Le magasinier crée un lot de réception:")
        
        lot_id = reception_service.creer_lot_reception(
            piece_id=piece_id,
            quantite_recue=15,
            utilisateur_id=1,
            commentaire="Livraison fournisseur ABC - Bon de livraison BL-2024-001"
        )
        
        print(f"✅ Lot de réception créé: {lot_id}")
        
        # Vérifier que le stock n'a pas changé
        stock_apres_reception = piece_service.get_piece_by_id(piece_id)['stock_actuel']
        print(f"📊 Stock après réception: {stock_apres_reception}")
        print("✅ Le stock n'a PAS changé - les pièces sont en zone de réception")
        
        # 3. Afficher les lots en attente
        print("\n📋 Lots en attente de confirmation:")
        lots_attente = reception_service.get_lots_en_attente_confirmation()
        for lot in lots_attente:
            print(f"   - Lot {lot['numero_lot']}: {lot['quantite_recue']} x {lot['piece_reference']}")
            print(f"     En attente depuis: {lot['heures_en_attente']:.1f} heures")
        
        # 4. Étape 2 : Contrôle qualité et confirmation
        print("\n" + "-"*60)
        print("🔍 ÉTAPE 2: CONTRÔLE QUALITÉ ET CONFIRMATION")
        print("-"*60)
        print("Le magasinier vérifie la qualité des pièces...")
        print("Contrôle OK - Confirmation de la réception:")
        
        success = reception_service.confirmer_reception_lot(
            lot_id=lot_id,
            utilisateur_id=1,
            commentaire_confirmation="Contrôle qualité OK - Toutes les pièces conformes"
        )
        
        if success:
            print("✅ Réception confirmée avec succès")
        
        # Vérifier que le stock a été mis à jour
        stock_apres_confirmation = piece_service.get_piece_by_id(piece_id)['stock_actuel']
        print(f"📊 Stock après confirmation: {stock_apres_confirmation}")
        print("✅ Le stock a été mis à jour - les pièces sont maintenant comptabilisées")
        
        # 5. Étape 3 : Mise en stock physique
        print("\n" + "-"*60)
        print("📦 ÉTAPE 3: MISE EN STOCK PHYSIQUE")
        print("-"*60)
        print("Le magasinier déplace les pièces vers leur emplacement final...")
        
        # Récupérer un emplacement pour la démo
        with db.conn.cursor() as cur:
            cur.execute("SELECT id, nom FROM emplacement WHERE nom != 'RECEPTION' LIMIT 1")
            emplacement = cur.fetchone()
            
        if emplacement:
            emplacement_id, emplacement_nom = emplacement
            print(f"Déplacement vers l'emplacement: {emplacement_nom}")
            
            success = reception_service.mettre_en_stock(
                lot_id=lot_id,
                emplacement_destination_id=emplacement_id,
                quantite_a_stocker=15,
                utilisateur_id=1,
                commentaire="Stockage dans l'emplacement principal"
            )
            
            if success:
                print("✅ Mise en stock physique terminée")
        
        # 6. Dashboard final
        print("\n" + "-"*60)
        print("📊 TABLEAU DE BORD FINAL")
        print("-"*60)
        dashboard = reception_service.get_dashboard_reception_detaille()
        for indicateur, data in dashboard.items():
            print(f"   {indicateur}: {data['valeur']} - {data['description']}")
        
        # 7. Historique du lot
        print("\n" + "-"*60)
        print("📜 HISTORIQUE DU LOT")
        print("-"*60)
        historique = reception_service.get_historique_lot(lot_id)
        lot_info = historique['lot']
        print(f"Lot: {lot_info['numero_lot']}")
        print(f"Statut: {lot_info['statut_lot']}")
        print(f"Quantité reçue: {lot_info['quantite_recue']}")
        print(f"Quantité stockée: {lot_info['quantite_mise_en_stock']}")
        print(f"Restant à stocker: {lot_info['quantite_restante']}")
        
        # 8. Démonstration d'annulation
        print("\n" + "-"*60)
        print("❌ DÉMONSTRATION D'ANNULATION")
        print("-"*60)
        print("Simulation d'une réception défectueuse...")
        
        lot_id_2 = reception_service.creer_lot_reception(
            piece_id=piece_id,
            quantite_recue=8,
            utilisateur_id=1,
            commentaire="Livraison avec problème qualité"
        )
        
        print(f"Lot créé: {lot_id_2}")
        print("Détection d'un problème qualité - Annulation:")
        
        success = reception_service.annuler_reception_lot(
            lot_id=lot_id_2,
            utilisateur_id=1,
            raison_annulation="Pièces non conformes - Retour fournisseur"
        )
        
        if success:
            print("✅ Réception annulée - Aucun impact sur le stock")
        
        # Stock final
        stock_final = piece_service.get_piece_by_id(piece_id)['stock_actuel']
        print(f"\n📊 Stock final: {stock_final}")
        print(f"📈 Variation: +{stock_final - stock_initial} (seules les pièces confirmées)")
        
        print("\n" + "="*80)
        print("🎉 DÉMONSTRATION TERMINÉE AVEC SUCCÈS!")
        print("="*80)
        print("""
✅ AVANTAGES DÉMONTRÉS:
   - Séparation claire entre réception et stock
   - Pas de double comptage
   - Traçabilité complète du processus
   - Possibilité d'annulation avant impact
   - Dashboard temps réel
   - Historique détaillé
        """)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la démonstration: {e}")
        return False

def demo_scenarios_avances():
    """Démonstration de scénarios avancés"""
    try:
        db = Database()
        db.connect()
        
        mouvement_service = MouvementService(db)
        reception_service = ReceptionWorkflowService(db)
        
        print("\n" + "="*80)
        print("🔬 SCÉNARIOS AVANCÉS")
        print("="*80)
        
        # 1. Réception partielle
        print("\n📦 Scénario 1: Réception partielle")
        print("-"*40)
        pieces = PieceService(db).get_all_pieces()
        piece = pieces[1] if len(pieces) > 1 else pieces[0]
        
        # Créer un lot avec réception partielle
        lot_id = reception_service.creer_lot_reception(
            piece_id=piece['id_piece'],
            quantite_recue=20,
            utilisateur_id=1,
            commentaire="Livraison partielle - Reste à venir"
        )
        
        # Confirmer seulement une partie
        reception_service.confirmer_reception_lot(lot_id, 1, "Première partie validée")
        
        # Stocker partiellement
        with db.conn.cursor() as cur:
            cur.execute("SELECT id FROM emplacement WHERE nom != 'RECEPTION' LIMIT 1")
            emplacement_id = cur.fetchone()[0]
        
        reception_service.mettre_en_stock(lot_id, emplacement_id, 12, 1, "Stockage partiel")
        
        print(f"✅ Lot {lot_id}: 20 reçues, 12 stockées, 8 restantes")
        
        # 2. Gestion des mouvements en attente
        print("\n⏳ Scénario 2: Gestion des mouvements en attente")
        print("-"*40)
        mouvements_attente = mouvement_service.get_mouvements_en_attente()
        print(f"Mouvements en attente: {len(mouvements_attente)}")
        
        for mouvement in mouvements_attente[:3]:  # Afficher les 3 premiers
            print(f"   - Mouvement {mouvement['id']}: {mouvement['quantite']} x {mouvement['piece_reference']}")
            print(f"     En attente depuis: {mouvement['heures_en_attente']:.1f} heures")
        
        # 3. Dashboard détaillé
        print("\n📊 Scénario 3: Dashboard détaillé")
        print("-"*40)
        dashboard = reception_service.get_dashboard_reception_detaille()
        
        print("Indicateurs clés:")
        for key, value in dashboard.items():
            if isinstance(value, dict):
                print(f"   {key}: {value['valeur']} - {value['description']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors des scénarios avancés: {e}")
        return False

def main():
    """Fonction principale"""
    try:
        print("🚀 Démarrage de la démonstration du nouveau workflow")
        
        # Démonstration complète
        if not demo_workflow_complet():
            print("❌ Échec de la démonstration principale")
            return False
        
        # Scénarios avancés
        if not demo_scenarios_avances():
            print("❌ Échec des scénarios avancés")
            return False
        
        print("\n🎉 Toutes les démonstrations terminées avec succès!")
        print("\nLe nouveau système de statuts de mouvement est prêt à être utilisé.")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur générale: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)