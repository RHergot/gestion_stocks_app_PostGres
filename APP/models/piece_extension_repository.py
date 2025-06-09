from APP.services.db import Database
from psycopg2.extras import RealDictCursor

class PieceExtensionRepository:
    def __init__(self, db: Database):
        self.db = db

    def get_by_piece_id(self, id_piece):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM piece_extension WHERE id_piece = %s;", (id_piece,))
            return cur.fetchone()

    def add_or_update_extension(self, id_piece, extension):
        # Si extension existe, update, sinon insert
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT 1 FROM piece_extension WHERE id_piece = %s;", (id_piece,))
            if cur.fetchone():
                cur.execute(
                    "UPDATE piece_extension SET unite_id=%s, categorie_id=%s, emplacement_id=%s, statut_id=%s, machine_id=%s WHERE id_piece=%s;",
                    (
                        extension.get("unite_id"),
                        extension.get("categorie_id"),
                        extension.get("emplacement_id"),
                        extension.get("statut_id"),
                        extension.get("machine_id"),
                        id_piece
                    )
                )
            else:
                cur.execute(
                    "INSERT INTO piece_extension (id_piece, unite_id, categorie_id, emplacement_id, statut_id, machine_id) VALUES (%s, %s, %s, %s, %s, %s);",
                    (
                        id_piece,
                        extension.get("unite_id"),
                        extension.get("categorie_id"),
                        extension.get("emplacement_id"),
                        extension.get("statut_id"),
                        extension.get("machine_id")
                    )
                )
            self.db.conn.commit()

    def delete_extension(self, id_piece):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("DELETE FROM piece_extension WHERE id_piece = %s;", (id_piece,))
            self.db.conn.commit()
