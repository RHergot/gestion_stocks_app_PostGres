from APP.services.db import Database
from psycopg2.extras import RealDictCursor

class PieceCategoryRepository:
    def __init__(self, db: Database):
        self.db = db

    def list_categories(self):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM piece_category ORDER BY nom;")
            return cur.fetchall()

    def get_category_by_id(self, id):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM piece_category WHERE id = %s;", (id,))
            return cur.fetchone()

    def create_category(self, category):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO piece_category (nom, description) VALUES (%s, %s) RETURNING id;",
                (category["nom"], category.get("description"))
            )
            self.db.conn.commit()
            return cur.fetchone()["id"]

    def update_category(self, id, category):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "UPDATE piece_category SET nom=%s, description=%s WHERE id=%s;",
                (category["nom"], category.get("description"), id)
            )
            self.db.conn.commit()

    def delete_category(self, id):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("DELETE FROM piece_category WHERE id = %s;", (id,))
            self.db.conn.commit()
