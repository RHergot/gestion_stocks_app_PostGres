from APP.services.db import Database
from psycopg2.extras import RealDictCursor

class PieceStatutRepository:
    def __init__(self, db: Database):
        self.db = db

    def list_statuts(self):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM piece_statut ORDER BY nom;")
            return cur.fetchall()

    def get_statut_by_id(self, id):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM piece_statut WHERE id = %s;", (id,))
            return cur.fetchone()

    def create_statut(self, statut):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO piece_statut (nom, description) VALUES (%s, %s) RETURNING id;",
                (statut["nom"], statut.get("description"))
            )
            self.db.conn.commit()
            return cur.fetchone()["id"]

    def update_statut(self, id, statut):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "UPDATE piece_statut SET nom=%s, description=%s WHERE id=%s;",
                (statut["nom"], statut.get("description"), id)
            )
            self.db.conn.commit()

    def delete_statut(self, id):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("DELETE FROM piece_statut WHERE id = %s;", (id,))
            self.db.conn.commit()
