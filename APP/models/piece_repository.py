from APP.services.db import Database
from psycopg2.extras import RealDictCursor

class PieceRepository:
    def __init__(self, db: Database):
        self.db = db

    def get_all_pieces(self):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT p.*, m.nom AS machine
                FROM piece p
                LEFT JOIN piece_extension pe ON p.id_piece = pe.id_piece
                LEFT JOIN machine m ON pe.machine_id = m.id_machine
                ORDER BY p.nom;
            ''')
            return cur.fetchall()

    def get_piece_by_id(self, id_piece):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM PIECE WHERE id_piece = %s;", (id_piece,))
            return cur.fetchone()

    def add_piece(self, piece):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO PIECE (reference, nom, fournisseur_pref_id, prix_unitaire, stock_alerte, stock_actuel, stock_reserve, unite, categorie, emplacement_stockage, statut)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id_piece;
                """,
                (
                    piece["reference"], piece["nom"], piece.get("fournisseur_pref_id"), piece.get("prix_unitaire", 0.0),
                    piece.get("stock_alerte", 0), piece.get("stock_actuel", 0), piece.get("stock_reserve", 0),
                    piece["unite"], piece.get("categorie"), piece.get("emplacement_stockage"), piece.get("statut", "Actif")
                )
            )
            self.db.conn.commit()
            return cur.fetchone()["id_piece"]

    def update_piece(self, id_piece, piece):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE PIECE SET reference=%s, nom=%s, fournisseur_pref_id=%s, prix_unitaire=%s, stock_alerte=%s, stock_actuel=%s, stock_reserve=%s, unite=%s, categorie=%s, emplacement_stockage=%s, statut=%s, updated_at=NOW()
                WHERE id_piece=%s;
                """,
                (
                    piece["reference"], piece["nom"], piece.get("fournisseur_pref_id"), piece.get("prix_unitaire", 0.0),
                    piece.get("stock_alerte", 0), piece.get("stock_actuel", 0), piece.get("stock_reserve", 0),
                    piece["unite"], piece.get("categorie"), piece.get("emplacement_stockage"), piece.get("statut", "Actif"),
                    id_piece
                )
            )
            self.db.conn.commit()

    def delete_piece(self, id_piece):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("DELETE FROM PIECE WHERE id_piece = %s;", (id_piece,))
            self.db.conn.commit()

    def set_statut(self, id_piece: int, statut: str):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE piece
                SET statut = %s, updated_at = NOW()
                WHERE id_piece = %s;
                """,
                (statut, id_piece)
            )
            self.db.conn.commit()
