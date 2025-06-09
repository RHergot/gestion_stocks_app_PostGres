from APP.services.db import Database
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional

class EmplacementExtRepository:
    """Repository pour la gestion des extensions d'emplacements"""
    
    def __init__(self, db: Database):
        self.db = db

    def get_emplacement_ext_by_id(self, emplacement_id: int) -> Optional[Dict]:
        """Récupère les données étendues d'un emplacement"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM emplacement_ext 
                WHERE emplacement_id = %s
            """, (emplacement_id,))
            return cur.fetchone()

    def create_emplacement_ext(self, emplacement_id: int, data: Dict) -> bool:
        """Crée les données étendues pour un emplacement"""
        with self.db.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO emplacement_ext (
                    emplacement_id, longueur_cm, hauteur_cm, profondeur_cm,
                    capacite_max_kg, temperature_min_c, temperature_max_c,
                    humidite_max_pct, conditions_speciales, actif
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                emplacement_id,
                data.get('longueur_cm'),
                data.get('hauteur_cm'), 
                data.get('profondeur_cm'),
                data.get('capacite_max_kg'),
                data.get('temperature_min_c'),
                data.get('temperature_max_c'),
                data.get('humidite_max_pct'),
                data.get('conditions_speciales'),
                data.get('actif', True)
            ))
            self.db.conn.commit()
            return True

    def update_emplacement_ext(self, emplacement_id: int, data: Dict) -> bool:
        """Met à jour les données étendues d'un emplacement"""
        with self.db.conn.cursor() as cur:
            cur.execute("""
                UPDATE emplacement_ext SET
                    longueur_cm = %s,
                    hauteur_cm = %s,
                    profondeur_cm = %s,
                    capacite_max_kg = %s,
                    temperature_min_c = %s,
                    temperature_max_c = %s,
                    humidite_max_pct = %s,
                    conditions_speciales = %s,
                    actif = %s
                WHERE emplacement_id = %s
            """, (
                data.get('longueur_cm'),
                data.get('hauteur_cm'),
                data.get('profondeur_cm'),
                data.get('capacite_max_kg'),
                data.get('temperature_min_c'),
                data.get('temperature_max_c'),
                data.get('humidite_max_pct'),
                data.get('conditions_speciales'),
                data.get('actif', True),
                emplacement_id
            ))
            self.db.conn.commit()
            return cur.rowcount > 0

    def delete_emplacement_ext(self, emplacement_id: int) -> bool:
        """Supprime les données étendues d'un emplacement"""
        with self.db.conn.cursor() as cur:
            cur.execute("DELETE FROM emplacement_ext WHERE emplacement_id = %s", (emplacement_id,))
            self.db.conn.commit()
            return cur.rowcount > 0

    def get_all_emplacements_detail(self) -> List[Dict]:
        """Récupère tous les emplacements avec leurs détails étendus"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM v_emplacement_detail ORDER BY nom")
            return cur.fetchall()

    def get_emplacements_capacite(self) -> List[Dict]:
        """Récupère les emplacements avec leurs informations de capacité"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM v_emplacement_capacite ORDER BY nom")
            return cur.fetchall()

    def get_stock_by_emplacement(self, emplacement_id: int) -> List[Dict]:
        """Récupère le stock détaillé d'un emplacement"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM v_stock_par_emplacement 
                WHERE emplacement_id = %s 
                ORDER BY piece_reference
            """, (emplacement_id,))
            return cur.fetchall()

    def get_piece_emplacements(self, piece_id: int) -> List[Dict]:
        """Récupère tous les emplacements où se trouve une pièce"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM v_stock_par_emplacement 
                WHERE id_piece = %s 
                ORDER BY emplacement_nom
            """, (piece_id,))
            return cur.fetchall()

    def get_emplacement_stock_item(self, emplacement_id: int, piece_id: int) -> Optional[Dict]:
        """Récupère un item de stock spécifique"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM emplacement_stock 
                WHERE emplacement_id = %s AND piece_id = %s
            """, (emplacement_id, piece_id))
            return cur.fetchone()

    def update_stock_emplacement(self, emplacement_id: int, piece_id: int, 
                                quantite: int, commentaire: str = None) -> bool:
        """Met à jour ou crée un stock dans un emplacement"""
        with self.db.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO emplacement_stock (emplacement_id, piece_id, quantite, commentaire)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (emplacement_id, piece_id)
                DO UPDATE SET 
                    quantite = %s,
                    commentaire = COALESCE(%s, emplacement_stock.commentaire)
            """, (emplacement_id, piece_id, quantite, commentaire, quantite, commentaire))
            self.db.conn.commit()
            
            # Nettoyer si quantité = 0
            if quantite == 0:
                cur.execute("""
                    DELETE FROM emplacement_stock 
                    WHERE emplacement_id = %s AND piece_id = %s AND quantite = 0
                """, (emplacement_id, piece_id))
                self.db.conn.commit()
            
            return True

    def ajouter_stock_emplacement(self, emplacement_id: int, piece_id: int, 
                                 quantite: int, commentaire: str = None) -> bool:
        """Ajoute du stock à un emplacement (incrémente)"""
        with self.db.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO emplacement_stock (emplacement_id, piece_id, quantite, commentaire)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (emplacement_id, piece_id)
                DO UPDATE SET 
                    quantite = emplacement_stock.quantite + %s,
                    commentaire = COALESCE(%s, emplacement_stock.commentaire)
            """, (emplacement_id, piece_id, quantite, commentaire, quantite, commentaire))
            self.db.conn.commit()
            return True

    def retirer_stock_emplacement(self, emplacement_id: int, piece_id: int, 
                                 quantite: int, commentaire: str = None) -> bool:
        """Retire du stock d'un emplacement (décrémente)"""
        with self.db.conn.cursor() as cur:
            # Vérifier le stock disponible
            cur.execute("""
                SELECT quantite FROM emplacement_stock 
                WHERE emplacement_id = %s AND piece_id = %s
            """, (emplacement_id, piece_id))
            
            result = cur.fetchone()
            if not result or result[0] < quantite:
                raise ValueError(f"Stock insuffisant dans l'emplacement (disponible: {result[0] if result else 0}, demandé: {quantite})")
            
            # Décrémenter le stock
            cur.execute("""
                UPDATE emplacement_stock 
                SET quantite = quantite - %s,
                    commentaire = COALESCE(%s, commentaire)
                WHERE emplacement_id = %s AND piece_id = %s
            """, (quantite, commentaire, emplacement_id, piece_id))
            
            # Nettoyer si quantité = 0
            cur.execute("""
                DELETE FROM emplacement_stock 
                WHERE emplacement_id = %s AND piece_id = %s AND quantite = 0
            """, (emplacement_id, piece_id))
            
            self.db.conn.commit()
            return True

    def deplacer_stock(self, piece_id: int, emplacement_source_id: int, 
                      emplacement_destination_id: int, quantite: int, 
                      commentaire: str = None) -> bool:
        """Déplace du stock entre emplacements"""
        with self.db.conn.cursor() as cur:
            cur.execute("""
                SELECT deplacer_stock(%s, %s, %s, %s, %s)
            """, (piece_id, emplacement_source_id, emplacement_destination_id, quantite, commentaire))
            self.db.conn.commit()
            return True

    def nettoyer_stocks_zero(self) -> int:
        """Nettoie tous les stocks à zéro"""
        with self.db.conn.cursor() as cur:
            cur.execute("SELECT nettoyer_stocks_zero()")
            result = cur.fetchone()
            self.db.conn.commit()
            return result[0] if result else 0

    def get_emplacements_libres(self, capacite_min: float = None) -> List[Dict]:
        """Récupère les emplacements avec de la capacité libre"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT * FROM v_emplacement_capacite 
                WHERE capacite_restante IS NULL OR capacite_restante > 0
            """
            params = []
            
            if capacite_min is not None:
                query += " AND (capacite_restante IS NULL OR capacite_restante >= %s)"
                params.append(capacite_min)
            
            query += " ORDER BY capacite_restante DESC NULLS FIRST"
            
            cur.execute(query, params)
            return cur.fetchall()

    def get_statistiques_emplacement(self, emplacement_id: int) -> Dict:
        """Récupère les statistiques d'un emplacement"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) as nb_pieces_differentes,
                    SUM(quantite) as quantite_totale,
                    AVG(quantite) as quantite_moyenne,
                    MIN(date_derniere_maj) as plus_ancien_mouvement,
                    MAX(date_derniere_maj) as plus_recent_mouvement
                FROM emplacement_stock 
                WHERE emplacement_id = %s AND quantite > 0
            """, (emplacement_id,))
            
            stats = cur.fetchone()
            
            # Ajouter les informations de l'emplacement
            cur.execute("""
                SELECT * FROM v_emplacement_detail 
                WHERE id = %s
            """, (emplacement_id,))
            
            emplacement_info = cur.fetchone()
            
            if stats and emplacement_info:
                return {**dict(emplacement_info), **dict(stats)}
            
            return emplacement_info or {}

    def rechercher_piece_dans_emplacements(self, terme_recherche: str) -> List[Dict]:
        """Recherche une pièce dans tous les emplacements"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM v_stock_par_emplacement 
                WHERE piece_reference ILIKE %s 
                   OR piece_nom ILIKE %s
                ORDER BY emplacement_nom, piece_reference
            """, (f"%{terme_recherche}%", f"%{terme_recherche}%"))
            return cur.fetchall()