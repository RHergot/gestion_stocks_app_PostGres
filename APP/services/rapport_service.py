"""Service de rapports et requêtes analytiques.

Extrait de main_window.py pour respecter la séparation MVC :
les vues ne doivent pas exécuter de SQL direct.
"""
import logging

logger = logging.getLogger(__name__)


class RapportService:
    """Fournit des rapports préformatés pour l'affichage dans les vues."""

    def __init__(self, db):
        self.db = db

    def get_stock_faible(self):
        """Pièces dont le stock est inférieur ou égal au seuil d'alerte."""
        with self.db.conn.cursor() as cur:
            cur.execute("""
                SELECT nom, reference, stock_actuel, stock_alerte
                FROM piece
                WHERE stock_actuel <= stock_alerte
                ORDER BY stock_actuel ASC;
            """)
            rows = cur.fetchall()
        msg = "\n".join([f"{r[0]} ({r[1]}): {r[2]}/{r[3]}" for r in rows]) or "No parts with low stock."
        return msg

    def get_pieces_by_machine(self):
        """Pièces groupées par machine."""
        with self.db.conn.cursor() as cur:
            cur.execute("""
                SELECT p.nom, p.reference, pe.machine_id, m.nom AS machine
                FROM piece p
                JOIN piece_extension pe ON p.id_piece = pe.id_piece
                JOIN machine m ON pe.machine_id = m.id_machine
                ORDER BY m.nom, p.nom;
            """)
            rows = cur.fetchall()
        msg = "\n".join([f"{r[0]} ({r[1]}): {r[3]}" for r in rows]) or "No parts linked to a machine."
        return msg

    def get_inventaire_categorie(self):
        """Inventaire regroupé par catégorie de pièce."""
        with self.db.conn.cursor() as cur:
            cur.execute("""
                SELECT c.nom, COUNT(*), SUM(p.stock_actuel)
                FROM piece p
                JOIN piece_extension pe ON p.id_piece = pe.id_piece
                JOIN piece_category c ON pe.categorie_id = c.id
                GROUP BY c.nom
                ORDER BY COUNT(*) DESC;
            """)
            rows = cur.fetchall()
        msg = "\n".join([f"{r[0]}: {r[1]} parts, {r[2]} in stock" for r in rows]) or "No category."
        return msg

    def get_emplacements_sous_utilises(self):
        """Emplacements avec moins de 5 pièces."""
        with self.db.conn.cursor() as cur:
            cur.execute("""
                SELECT e.nom, COUNT(p.id_piece) AS nb_pieces
                FROM emplacement e
                LEFT JOIN piece_extension pe ON pe.emplacement_id = e.id
                LEFT JOIN piece p ON pe.id_piece = p.id_piece
                GROUP BY e.nom
                HAVING COUNT(p.id_piece) < 5
                ORDER BY nb_pieces ASC;
            """)
            rows = cur.fetchall()
        msg = "\n".join([f"{r[0]}: {r[1]} parts" for r in rows]) or "No underused location."
        return msg

    def get_pieces_by_statut(self):
        """Pièces groupées par statut."""
        with self.db.conn.cursor() as cur:
            cur.execute("""
                SELECT s.nom, COUNT(*)
                FROM piece p
                JOIN piece_extension pe ON p.id_piece = pe.id_piece
                JOIN piece_statut s ON pe.statut_id = s.id
                GROUP BY s.nom
                ORDER BY COUNT(*) DESC;
            """)
            rows = cur.fetchall()
        msg = "\n".join([f"{r[0]}: {r[1]} parts" for r in rows]) or "No status."
        return msg
