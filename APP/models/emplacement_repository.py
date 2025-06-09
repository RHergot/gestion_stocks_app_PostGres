from APP.services.db import Database
from psycopg2.extras import RealDictCursor

class EmplacementRepository:
    def __init__(self, db: Database):
        self.db = db

    def get_all_emplacements(self):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM emplacement ORDER BY nom;")
            return cur.fetchall()

    def get_all_warehouses(self):
        """Récupère tous les magasins (entrepôts) depuis la base de données."""
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, nom FROM inventory_warehouses ORDER BY nom;")
            return cur.fetchall()

    def get_emplacement_by_id(self, id):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM emplacement WHERE id = %s;", (id,))
            return cur.fetchone()

    def add_emplacement(self, emplacement):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO emplacement (magasin_id, nom, type, allee, etagere, niveau)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (
                    emplacement["magasin_id"], emplacement["nom"], emplacement.get("type"),
                    emplacement.get("allee"), emplacement.get("etagere"), emplacement.get("niveau")
                )
            )
            self.db.conn.commit()
            return cur.fetchone()["id"]

    def update_emplacement(self, id, emplacement):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE emplacement SET magasin_id=%s, nom=%s, type=%s, allee=%s, etagere=%s, niveau=%s WHERE id=%s;
                """,
                (
                    emplacement["magasin_id"], emplacement["nom"], emplacement.get("type"),
                    emplacement.get("allee"), emplacement.get("etagere"), emplacement.get("niveau"), id
                )
            )
            self.db.conn.commit()

    def delete_emplacement(self, id):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("DELETE FROM emplacement WHERE id = %s;", (id,))
            self.db.conn.commit()
