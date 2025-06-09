from APP.services.db import Database
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class LotReceptionRepository:
    """Repository pour la gestion des lots de réception"""
    
    def __init__(self, db: Database):
        self.db = db

    def create_lot_reception(self, data: Dict) -> int:
        """Crée un nouveau lot de réception"""
        try:
            with self.db.conn.cursor() as cur:
                # Générer un numéro de lot automatiquement si non fourni
                if 'numero_lot' not in data or not data['numero_lot']:
                    cur.execute("SELECT generer_numero_lot()")
                    data['numero_lot'] = cur.fetchone()[0]
                
                # Récupérer l'emplacement de réception par défaut si non spécifié
                if 'emplacement_reception_id' not in data or not data['emplacement_reception_id']:
                    cur.execute("SELECT get_emplacement_reception_defaut()")
                    result = cur.fetchone()
                    if result and result[0]:
                        data['emplacement_reception_id'] = result[0]
                
                cur.execute("""
                    INSERT INTO lot_reception (
                        numero_lot, commande_id, ligne_commande_id, piece_id,
                        quantite_recue, emplacement_reception_id, statut_lot,
                        utilisateur_reception_id, commentaire_reception, bon_etat
                    ) VALUES (
                        %(numero_lot)s, %(commande_id)s, %(ligne_commande_id)s, %(piece_id)s,
                        %(quantite_recue)s, %(emplacement_reception_id)s, %(statut_lot)s,
                        %(utilisateur_reception_id)s, %(commentaire_reception)s, %(bon_etat)s
                    ) RETURNING id
                """, data)
                
                lot_id = cur.fetchone()[0]
                self.db.conn.commit()
                
                logger.info(f"Lot de réception créé: ID={lot_id}, Numéro={data['numero_lot']}")
                return lot_id
                
        except Exception as e:
            self.db.conn.rollback()
            logger.error(f"Erreur lors de la création du lot de réception: {e}")
            raise

    def get_lot_by_id(self, lot_id: int) -> Optional[Dict]:
        """Récupère un lot de réception par son ID"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM v_lots_reception WHERE id = %s", (lot_id,))
            return cur.fetchone()

    def get_lots_by_piece(self, piece_id: int) -> List[Dict]:
        """Récupère tous les lots d'une pièce"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM v_lots_reception 
                WHERE piece_id = %s 
                ORDER BY date_reception DESC
            """, (piece_id,))
            return cur.fetchall()

    def get_lots_en_attente_stockage(self) -> List[Dict]:
        """Récupère tous les lots en attente de mise en stock"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM v_lots_reception 
                WHERE quantite_restante > 0 
                AND statut_lot IN ('EN_RECEPTION', 'EN_CONTROLE', 'PRET_STOCKAGE')
                ORDER BY date_reception ASC
            """)
            return cur.fetchall()

    def get_lots_by_commande(self, commande_id: int) -> List[Dict]:
        """Récupère tous les lots d'une commande"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM v_lots_reception 
                WHERE commande_id = %s 
                ORDER BY date_reception DESC
            """, (commande_id,))
            return cur.fetchall()

    def update_statut_lot(self, lot_id: int, nouveau_statut: str, commentaire: str = None) -> bool:
        """Met à jour le statut d'un lot"""
        try:
            with self.db.conn.cursor() as cur:
                if commentaire:
                    cur.execute("""
                        UPDATE lot_reception 
                        SET statut_lot = %s, commentaire_reception = %s
                        WHERE id = %s
                    """, (nouveau_statut, commentaire, lot_id))
                else:
                    cur.execute("""
                        UPDATE lot_reception 
                        SET statut_lot = %s
                        WHERE id = %s
                    """, (nouveau_statut, lot_id))
                
                success = cur.rowcount > 0
                self.db.conn.commit()
                
                if success:
                    logger.info(f"Statut du lot {lot_id} mis à jour: {nouveau_statut}")
                
                return success
                
        except Exception as e:
            self.db.conn.rollback()
            logger.error(f"Erreur lors de la mise à jour du statut du lot {lot_id}: {e}")
            return False

    def get_stock_reception_par_piece(self) -> List[Dict]:
        """Récupère le stock en réception par pièce"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM v_stock_reception ORDER BY plus_ancienne_reception ASC")
            return cur.fetchall()

class MiseEnStockRepository:
    """Repository pour la gestion des mises en stock"""
    
    def __init__(self, db: Database):
        self.db = db

    def create_mise_en_stock(self, data: Dict) -> int:
        """Crée un enregistrement de mise en stock"""
        try:
            with self.db.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO mise_en_stock_detail (
                        lot_reception_id, emplacement_destination_id, quantite_stockee,
                        utilisateur_id, mouvement_stock_id, commentaire
                    ) VALUES (
                        %(lot_reception_id)s, %(emplacement_destination_id)s, %(quantite_stockee)s,
                        %(utilisateur_id)s, %(mouvement_stock_id)s, %(commentaire)s
                    ) RETURNING id
                """, data)
                
                mise_en_stock_id = cur.fetchone()[0]
                self.db.conn.commit()
                
                logger.info(f"Mise en stock créée: ID={mise_en_stock_id}")
                return mise_en_stock_id
                
        except Exception as e:
            self.db.conn.rollback()
            logger.error(f"Erreur lors de la création de la mise en stock: {e}")
            raise

    def get_mises_en_stock_by_lot(self, lot_id: int) -> List[Dict]:
        """Récupère toutes les mises en stock d'un lot"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM v_mise_en_stock_detail 
                WHERE lot_reception_id = %s 
                ORDER BY date_stockage DESC
            """, (lot_id,))
            return cur.fetchall()

    def get_mises_en_stock_by_emplacement(self, emplacement_id: int) -> List[Dict]:
        """Récupère toutes les mises en stock vers un emplacement"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM v_mise_en_stock_detail 
                WHERE emplacement_destination_id = %s 
                ORDER BY date_stockage DESC
            """, (emplacement_id,))
            return cur.fetchall()

    def get_historique_mise_en_stock(self, limit: int = 100) -> List[Dict]:
        """Récupère l'historique des mises en stock"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM v_mise_en_stock_detail 
                ORDER BY date_stockage DESC 
                LIMIT %s
            """, (limit,))
            return cur.fetchall()