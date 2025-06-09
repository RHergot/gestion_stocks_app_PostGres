from APP.services.db import Database
from APP.models.lot_reception_repository import LotReceptionRepository, MiseEnStockRepository
from APP.services.mouvement_service import MouvementService
from APP.services.emplacement_ext_service import EmplacementExtService
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ReceptionWorkflowService:
    """Service pour gérer le workflow réception -> mise en stock"""
    
    def __init__(self, db: Database):
        self.db = db
        self.lot_repo = LotReceptionRepository(db)
        self.mise_en_stock_repo = MiseEnStockRepository(db)
        self.mouvement_service = MouvementService(db)
        self.emplacement_service = EmplacementExtService(db)

    def creer_lot_reception(self, piece_id: int, quantite_recue: int, 
                           commande_id: int = None, ligne_commande_id: int = None,
                           utilisateur_id: int = None, commentaire: str = None,
                           bon_etat: bool = True) -> int:
        """Crée un lot de réception (sans impact sur le stock des emplacements)"""
        try:
            # Données du lot
            lot_data = {
                'piece_id': piece_id,
                'quantite_recue': quantite_recue,
                'commande_id': commande_id,
                'ligne_commande_id': ligne_commande_id,
                'statut_lot': 'EN_RECEPTION',
                'utilisateur_reception_id': utilisateur_id,
                'commentaire_reception': commentaire,
                'bon_etat': bon_etat
            }
            
            # Créer le lot
            lot_id = self.lot_repo.create_lot_reception(lot_data)
            
            # Créer un mouvement de réception (impact_stock = 0)
            types_mouvement = self.mouvement_service.get_all_types_mouvement()
            type_reception = next((t for t in types_mouvement if t['nom'] == 'RECEPTION_ACHAT'), None)
            
            if type_reception:
                # Récupérer l'emplacement de réception
                with self.db.conn.cursor() as cur:
                    cur.execute("SELECT get_emplacement_reception_defaut()")
                    emplacement_reception_id = cur.fetchone()[0]
                
                # Créer le mouvement de réception (n'impacte pas le stock des emplacements)
                mouvement_id = self.mouvement_service.creer_mouvement_reception(
                    piece_id=piece_id,
                    quantite=quantite_recue,
                    type_mouvement_id=type_reception['id'],
                    emplacement_destination_id=emplacement_reception_id,
                    utilisateur_id=utilisateur_id,
                    reference_document=f"LOT-{lot_id}",
                    commentaire=f"Réception lot - {commentaire or ''}",
                    statut_mouvement='EN_ATTENTE'  # Le mouvement est en attente de confirmation
                )
                
                logger.info(f"Lot de réception créé: {lot_id}, Mouvement: {mouvement_id}")
            
            return lot_id
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du lot de réception: {e}")
            raise

    def mettre_en_stock(self, lot_id: int, emplacement_destination_id: int, 
                       quantite_a_stocker: int = None, utilisateur_id: int = None,
                       commentaire: str = None) -> bool:
        """Met en stock une quantité depuis un lot de réception"""
        try:
            # Récupérer le lot
            lot = self.lot_repo.get_lot_by_id(lot_id)
            if not lot:
                raise ValueError(f"Lot {lot_id} non trouvé")
            
            # Vérifier la quantité disponible
            quantite_disponible = lot['quantite_restante']
            if quantite_a_stocker is None:
                quantite_a_stocker = quantite_disponible
            
            if quantite_a_stocker > quantite_disponible:
                raise ValueError(f"Quantité demandée ({quantite_a_stocker}) > disponible ({quantite_disponible})")
            
            if quantite_a_stocker <= 0:
                raise ValueError("La quantité à stocker doit être positive")
            
            # Créer le mouvement de mise en stock
            types_mouvement = self.mouvement_service.get_all_types_mouvement()
            type_mise_en_stock = next((t for t in types_mouvement if t['nom'] == 'MISE_EN_STOCK'), None)
            
            if not type_mise_en_stock:
                raise ValueError("Type de mouvement MISE_EN_STOCK non trouvé")
            
            # Récupérer l'emplacement de réception
            with self.db.conn.cursor() as cur:
                cur.execute("SELECT get_emplacement_reception_defaut()")
                emplacement_reception_id = cur.fetchone()[0]
            
            # Créer le mouvement de mise en stock (impacte le stock des emplacements)
            mouvement_id = self.mouvement_service.creer_mouvement_transfert(
                piece_id=lot['piece_id'],
                quantite=quantite_a_stocker,
                emplacement_source_id=emplacement_reception_id,
                emplacement_destination_id=emplacement_destination_id,
                utilisateur_id=utilisateur_id,
                reference_document=f"STOCK-{lot['numero_lot']}",
                commentaire=f"Mise en stock depuis réception - {commentaire or ''}"
            )
            
            # Enregistrer la mise en stock
            mise_en_stock_data = {
                'lot_reception_id': lot_id,
                'emplacement_destination_id': emplacement_destination_id,
                'quantite_stockee': quantite_a_stocker,
                'utilisateur_id': utilisateur_id,
                'mouvement_stock_id': mouvement_id[0] if isinstance(mouvement_id, list) else mouvement_id,
                'commentaire': commentaire
            }
            
            mise_en_stock_id = self.mise_en_stock_repo.create_mise_en_stock(mise_en_stock_data)
            
            logger.info(f"Mise en stock réussie: Lot {lot_id} -> Emplacement {emplacement_destination_id}, Quantité: {quantite_a_stocker}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise en stock: {e}")
            raise

    def get_stock_en_reception(self) -> List[Dict]:
        """Récupère le stock en attente de mise en stock"""
        try:
            return self.lot_repo.get_stock_reception_par_piece()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du stock en réception: {e}")
            return []

    def get_lots_en_attente(self) -> List[Dict]:
        """Récupère tous les lots en attente de mise en stock"""
        try:
            return self.lot_repo.get_lots_en_attente_stockage()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des lots en attente: {e}")
            return []

    def valider_lot_pour_stockage(self, lot_id: int, utilisateur_id: int = None,
                                 commentaire: str = None) -> bool:
        """Valide un lot pour le stockage (passe de EN_RECEPTION à PRET_STOCKAGE)"""
        try:
            success = self.lot_repo.update_statut_lot(lot_id, 'PRET_STOCKAGE', commentaire)
            
            if success:
                logger.info(f"Lot {lot_id} validé pour stockage")
            
            return success
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation du lot {lot_id}: {e}")
            return False

    def confirmer_reception_lot(self, lot_id: int, utilisateur_id: int = None,
                               commentaire_confirmation: str = None) -> bool:
        """Confirme la réception d'un lot et applique l'impact sur le stock"""
        try:
            # Récupérer le lot
            lot = self.lot_repo.get_lot_by_id(lot_id)
            if not lot:
                raise ValueError(f"Lot {lot_id} non trouvé")
            
            # Trouver le mouvement de réception associé
            with self.db.conn.cursor() as cur:
                cur.execute('''
                    SELECT id FROM mouvement_stock 
                    WHERE reference_document = %s 
                    AND statut_mouvement = 'EN_ATTENTE'
                    AND piece_id = %s
                    ORDER BY date_mouvement DESC
                    LIMIT 1;
                ''', (f"LOT-{lot_id}", lot['piece_id']))
                
                result = cur.fetchone()
                if not result:
                    raise ValueError(f"Aucun mouvement en attente trouvé pour le lot {lot_id}")
                
                mouvement_id = result[0]
            
            # Confirmer le mouvement de réception
            success = self.mouvement_service.confirmer_mouvement_reception(
                mouvement_id, utilisateur_id, commentaire_confirmation
            )
            
            if success:
                # Mettre à jour le statut du lot
                self.lot_repo.update_statut_lot(lot_id, 'PRET_STOCKAGE', 
                                               f"Réception confirmée - {commentaire_confirmation or ''}")
                logger.info(f"Réception du lot {lot_id} confirmée")
            
            return success
            
        except Exception as e:
            logger.error(f"Erreur lors de la confirmation de la réception du lot {lot_id}: {e}")
            return False

    def annuler_reception_lot(self, lot_id: int, utilisateur_id: int = None,
                             raison_annulation: str = None) -> bool:
        """Annule la réception d'un lot"""
        try:
            # Récupérer le lot
            lot = self.lot_repo.get_lot_by_id(lot_id)
            if not lot:
                raise ValueError(f"Lot {lot_id} non trouvé")
            
            # Trouver le mouvement de réception associé
            with self.db.conn.cursor() as cur:
                cur.execute('''
                    SELECT id FROM mouvement_stock 
                    WHERE reference_document = %s 
                    AND statut_mouvement = 'EN_ATTENTE'
                    AND piece_id = %s
                    ORDER BY date_mouvement DESC
                    LIMIT 1;
                ''', (f"LOT-{lot_id}", lot['piece_id']))
                
                result = cur.fetchone()
                if not result:
                    raise ValueError(f"Aucun mouvement en attente trouvé pour le lot {lot_id}")
                
                mouvement_id = result[0]
            
            # Annuler le mouvement de réception
            success = self.mouvement_service.annuler_mouvement_reception(
                mouvement_id, utilisateur_id, raison_annulation
            )
            
            if success:
                # Mettre à jour le statut du lot
                self.lot_repo.update_statut_lot(lot_id, 'QUARANTAINE', 
                                               f"Réception annulée - {raison_annulation or ''}")
                logger.info(f"Réception du lot {lot_id} annulée")
            
            return success
            
        except Exception as e:
            logger.error(f"Erreur lors de l'annulation de la réception du lot {lot_id}: {e}")
            return False

    def get_lots_en_attente_confirmation(self) -> List[Dict]:
        """Récupère les lots en attente de confirmation de réception"""
        try:
            with self.db.conn.cursor() as cur:
                cur.execute('''
                    SELECT DISTINCT
                        lr.id,
                        lr.numero_lot,
                        lr.piece_id,
                        p.reference as piece_reference,
                        p.nom as piece_nom,
                        lr.quantite_recue,
                        lr.date_reception,
                        lr.statut_lot,
                        lr.commentaire_reception,
                        ms.id as mouvement_id,
                        ms.statut_mouvement,
                        EXTRACT(EPOCH FROM (NOW() - lr.date_reception))/3600 as heures_en_attente
                    FROM lot_reception lr
                    JOIN piece p ON lr.piece_id = p.id_piece
                    JOIN mouvement_stock ms ON ms.reference_document = CONCAT('LOT-', lr.id)
                    WHERE lr.statut_lot = 'EN_RECEPTION'
                    AND ms.statut_mouvement = 'EN_ATTENTE'
                    ORDER BY lr.date_reception ASC;
                ''')
                
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des lots en attente: {e}")
            return []

    def get_dashboard_reception_detaille(self) -> Dict:
        """Récupère un tableau de bord détaillé de la réception"""
        try:
            dashboard = self.mouvement_service.get_dashboard_reception()
            
            # Ajouter des informations spécifiques aux lots
            lots_en_attente = self.get_lots_en_attente_confirmation()
            dashboard['LOTS_EN_ATTENTE_CONFIRMATION'] = {
                'valeur': len(lots_en_attente),
                'description': 'Lots en attente de confirmation de réception'
            }
            
            # Calculer le temps moyen d'attente
            if lots_en_attente:
                temps_moyen = sum(lot['heures_en_attente'] for lot in lots_en_attente) / len(lots_en_attente)
                dashboard['TEMPS_MOYEN_ATTENTE'] = {
                    'valeur': round(temps_moyen, 1),
                    'description': 'Temps moyen d\'attente en heures'
                }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du dashboard détaillé: {e}")
            return {}

    def mettre_en_quarantaine(self, lot_id: int, raison: str, utilisateur_id: int = None) -> bool:
        """Met un lot en quarantaine"""
        try:
            commentaire = f"Mis en quarantaine: {raison}"
            success = self.lot_repo.update_statut_lot(lot_id, 'QUARANTAINE', commentaire)
            
            if success:
                logger.info(f"Lot {lot_id} mis en quarantaine: {raison}")
            
            return success
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise en quarantaine du lot {lot_id}: {e}")
            return False

    def get_historique_lot(self, lot_id: int) -> Dict:
        """Récupère l'historique complet d'un lot"""
        try:
            lot = self.lot_repo.get_lot_by_id(lot_id)
            if not lot:
                return {}
            
            mises_en_stock = self.mise_en_stock_repo.get_mises_en_stock_by_lot(lot_id)
            
            return {
                'lot': lot,
                'mises_en_stock': mises_en_stock,
                'total_stocke': sum(m['quantite_stockee'] for m in mises_en_stock),
                'restant_a_stocker': lot['quantite_restante']
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'historique du lot {lot_id}: {e}")
            return {}

    def suggerer_emplacements_pour_stockage(self, piece_id: int, quantite: int) -> List[Dict]:
        """Suggère des emplacements pour le stockage d'une pièce"""
        try:
            return self.emplacement_service.suggerer_emplacement_pour_piece(piece_id, quantite)
        except Exception as e:
            logger.error(f"Erreur lors de la suggestion d'emplacements: {e}")
            return []

    def get_rapport_reception_stockage(self, date_debut: str = None, date_fin: str = None) -> Dict:
        """Génère un rapport sur les réceptions et mises en stock"""
        try:
            # Récupérer les lots de la période
            with self.db.conn.cursor() as cur:
                if date_debut and date_fin:
                    cur.execute("""
                        SELECT 
                            COUNT(*) as total_lots,
                            SUM(quantite_recue) as total_recu,
                            SUM(quantite_mise_en_stock) as total_stocke,
                            SUM(quantite_restante) as total_en_attente,
                            COUNT(CASE WHEN statut_lot = 'STOCKE' THEN 1 END) as lots_stockes,
                            COUNT(CASE WHEN statut_lot = 'QUARANTAINE' THEN 1 END) as lots_quarantaine
                        FROM lot_reception 
                        WHERE date_reception BETWEEN %s AND %s
                    """, (date_debut, date_fin))
                else:
                    cur.execute("""
                        SELECT 
                            COUNT(*) as total_lots,
                            SUM(quantite_recue) as total_recu,
                            SUM(quantite_mise_en_stock) as total_stocke,
                            SUM(quantite_restante) as total_en_attente,
                            COUNT(CASE WHEN statut_lot = 'STOCKE' THEN 1 END) as lots_stockes,
                            COUNT(CASE WHEN statut_lot = 'QUARANTAINE' THEN 1 END) as lots_quarantaine
                        FROM lot_reception
                    """)
                
                stats = cur.fetchone()
                
                return {
                    'total_lots': stats[0] or 0,
                    'total_recu': stats[1] or 0,
                    'total_stocke': stats[2] or 0,
                    'total_en_attente': stats[3] or 0,
                    'lots_stockes': stats[4] or 0,
                    'lots_quarantaine': stats[5] or 0,
                    'taux_stockage': (stats[2] / stats[1] * 100) if stats[1] and stats[1] > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport: {e}")
            return {}