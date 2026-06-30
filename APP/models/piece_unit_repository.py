from APP.services.db import Database
from psycopg2.extras import RealDictCursor

class PieceUnitRepository:
    def __init__(self, db: Database):
        self.db = db

    def list_units(self):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM piece_unit ORDER BY nom;")
            return cur.fetchall()

    def get_unit_by_id(self, id):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM piece_unit WHERE id = %s;", (id,))
            return cur.fetchone()

    def create_unit(self, unit):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO piece_unit (nom, description) VALUES (%s, %s) RETURNING id;",
                (unit["nom"], unit.get("description"))
            )
            self.db.conn.commit()
            return cur.fetchone()["id"]

    def update_unit(self, id, unit):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "UPDATE piece_unit SET nom=%s, description=%s WHERE id=%s;",
                (unit["nom"], unit.get("description"), id)
            )
            self.db.conn.commit()

    def delete_unit(self, id):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("DELETE FROM piece_unit WHERE id = %s;", (id,))
            self.db.conn.commit()
