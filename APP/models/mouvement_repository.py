from APP.services.db import Database
from psycopg2.extras import RealDictCursor
from datetime import datetime, date
from typing import List, Dict, Optional

class MouvementRepository:
    def __init__(self, db: Database):
        self.db = db

    def get_all_mouvements(self, limit: int = 1000, offset: int = 0) -> List[Dict]:
        """Récupère tous les mouvements avec pagination"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT * FROM v_historique_mouvements
                ORDER BY date_mouvement DESC
                LIMIT %s OFFSET %s;
            ''', (limit, offset))
            return cur.fetchall()

    def get_mouvement_by_id(self, mouvement_id: int) -> Optional[Dict]:
        """Récupère un mouvement par son ID"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT ms.*, p.reference as piece_reference, p.nom as piece_nom,
                       tm.nom as type_mouvement_nom, tm.impact_stock,
                       es.nom as emplacement_source_nom,
                       ed.nom as emplacement_destination_nom,
                       u.nom_complet as utilisateur_nom
                FROM mouvement_stock ms
                JOIN piece p ON ms.piece_id = p.id_piece
                JOIN type_mouvement tm ON ms.type_mouvement_id = tm.id
                LEFT JOIN emplacement es ON ms.emplacement_source_id = es.id
                LEFT JOIN emplacement ed ON ms.emplacement_destination_id = ed.id
                LEFT JOIN utilisateur u ON ms.utilisateur_id = u.id_utilisateur
                WHERE ms.id = %s;
            ''', (mouvement_id,))
            return cur.fetchone()

    def get_mouvements_by_piece(self, piece_id: int, limit: int = 100) -> List[Dict]:
        """Récupère l'historique des mouvements pour une pièce"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT * FROM v_historique_mouvements
                WHERE piece_reference IN (
                    SELECT reference FROM piece WHERE id_piece = %s
                )
                ORDER BY date_mouvement DESC
                LIMIT %s;
            ''', (piece_id, limit))
            return cur.fetchall()

    def get_mouvements_by_date_range(self, date_debut: date, date_fin: date) -> List[Dict]:
        """Récupère les mouvements dans une plage de dates"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT * FROM v_historique_mouvements
                WHERE DATE(date_mouvement) BETWEEN %s AND %s
                ORDER BY date_mouvement DESC;
            ''', (date_debut, date_fin))
            return cur.fetchall()

    def get_mouvements_by_type(self, type_mouvement_id: int) -> List[Dict]:
        """Récupère les mouvements par type"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT * FROM v_historique_mouvements
                WHERE type_mouvement IN (
                    SELECT nom FROM type_mouvement WHERE id = %s
                )
                ORDER BY date_mouvement DESC;
            ''', (type_mouvement_id,))
            return cur.fetchall()

    def add_mouvement(self, mouvement: Dict) -> int:
        """Ajoute un nouveau mouvement de stock"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                INSERT INTO mouvement_stock (
                    piece_id, type_mouvement_id, quantite, 
                    emplacement_source_id, emplacement_destination_id,
                    utilisateur_id, date_mouvement, reference_document,
                    commentaire, cout_unitaire, stock_avant, stock_apres,
                    statut_mouvement
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id;
            ''', (
                mouvement['piece_id'],
                mouvement['type_mouvement_id'],
                mouvement['quantite'],
                mouvement.get('emplacement_source_id'),
                mouvement.get('emplacement_destination_id'),
                mouvement.get('utilisateur_id'),
                mouvement.get('date_mouvement', datetime.now()),
                mouvement.get('reference_document'),
                mouvement.get('commentaire'),
                mouvement.get('cout_unitaire'),
                mouvement['stock_avant'],
                mouvement['stock_apres'],
                mouvement.get('statut_mouvement', 'CONFIRME')
            ))
            self.db.conn.commit()
            return cur.fetchone()['id']

    def update_mouvement(self, mouvement_id: int, mouvement: Dict) -> None:
        """Met à jour un mouvement existant"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                UPDATE mouvement_stock SET
                    piece_id = %s,
                    type_mouvement_id = %s,
                    quantite = %s,
                    emplacement_source_id = %s,
                    emplacement_destination_id = %s,
                    utilisateur_id = %s,
                    date_mouvement = %s,
                    reference_document = %s,
                    commentaire = %s,
                    cout_unitaire = %s,
                    stock_avant = %s,
                    stock_apres = %s,
                    updated_at = NOW()
                WHERE id = %s;
            ''', (
                mouvement['piece_id'],
                mouvement['type_mouvement_id'],
                mouvement['quantite'],
                mouvement.get('emplacement_source_id'),
                mouvement.get('emplacement_destination_id'),
                mouvement.get('utilisateur_id'),
                mouvement.get('date_mouvement'),
                mouvement.get('reference_document'),
                mouvement.get('commentaire'),
                mouvement.get('cout_unitaire'),
                mouvement['stock_avant'],
                mouvement['stock_apres'],
                mouvement_id
            ))
            self.db.conn.commit()

    def delete_mouvement(self, mouvement_id: int) -> None:
        """Supprime un mouvement (marque comme invalide)"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                UPDATE mouvement_stock SET valide = FALSE, updated_at = NOW()
                WHERE id = %s;
            ''', (mouvement_id,))
            self.db.conn.commit()

    def get_stock_actuel_piece(self, piece_id: int) -> int:
        """Récupère le stock actuel d'une pièce"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT stock_actuel FROM piece WHERE id_piece = %s;
            ''', (piece_id,))
            result = cur.fetchone()
            return result['stock_actuel'] if result else 0

    def get_statistiques_mouvements(self, piece_id: int = None) -> List[Dict]:
        """Récupère les statistiques des mouvements"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            if piece_id:
                cur.execute('''
                    SELECT * FROM v_mouvement_stats
                    WHERE id_piece = %s
                    ORDER BY dernier_mouvement DESC;
                ''', (piece_id,))
            else:
                cur.execute('''
                    SELECT * FROM v_mouvement_stats
                    ORDER BY dernier_mouvement DESC
                    LIMIT 100;
                ''')
            return cur.fetchall()


class TypeMouvementRepository:
    def __init__(self, db: Database):
        self.db = db

    def get_all_types_mouvement(self) -> List[Dict]:
        """Récupère tous les types de mouvement actifs"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT * FROM type_mouvement 
                WHERE actif = TRUE 
                ORDER BY nom;
            ''')
            return cur.fetchall()

    def get_type_mouvement_by_id(self, type_id: int) -> Optional[Dict]:
        """Récupère un type de mouvement par son ID"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT * FROM type_mouvement WHERE id = %s;
            ''', (type_id,))
            return cur.fetchone()

    def get_types_entree(self) -> List[Dict]:
        """Récupère les types de mouvement d'entrée"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT * FROM type_mouvement 
                WHERE impact_stock = 1 AND actif = TRUE 
                ORDER BY nom;
            ''')
            return cur.fetchall()

    def get_types_sortie(self) -> List[Dict]:
        """Récupère les types de mouvement de sortie"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT * FROM type_mouvement 
                WHERE impact_stock = -1 AND actif = TRUE 
                ORDER BY nom;
            ''')
            return cur.fetchall()

    def get_types_neutre(self) -> List[Dict]:
        """Récupère les types de mouvement neutres (impact_stock = 0)"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT * FROM type_mouvement 
                WHERE impact_stock = 0 AND actif = TRUE 
                ORDER BY nom;
            ''')
            return cur.fetchall()

    def add_type_mouvement(self, type_mouvement: Dict) -> int:
        """Ajoute un nouveau type de mouvement"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                INSERT INTO type_mouvement (nom, description, impact_stock, actif)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
            ''', (
                type_mouvement['nom'],
                type_mouvement.get('description'),
                type_mouvement['impact_stock'],
                type_mouvement.get('actif', True)
            ))
            self.db.conn.commit()
            return cur.fetchone()['id']

    def update_type_mouvement(self, type_id: int, type_mouvement: Dict) -> None:
        """Met à jour un type de mouvement"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                UPDATE type_mouvement SET
                    nom = %s,
                    description = %s,
                    impact_stock = %s,
                    actif = %s
                WHERE id = %s;
            ''', (
                type_mouvement['nom'],
                type_mouvement.get('description'),
                type_mouvement['impact_stock'],
                type_mouvement.get('actif', True),
                type_id
            ))
            self.db.conn.commit()

    def delete_type_mouvement(self, type_id: int) -> None:
        """Désactive un type de mouvement"""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                UPDATE type_mouvement SET actif = FALSE WHERE id = %s;
            ''', (type_id,))
            self.db.conn.commit()