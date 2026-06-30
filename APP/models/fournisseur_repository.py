from APP.services.db import Database
from psycopg2.extras import RealDictCursor

class FournisseurRepository:
    def __init__(self, db: Database):
        self.db = db

    def list_fournisseurs(self):
        try:
            with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM FOURNISSEUR ORDER BY nom;")
                return cur.fetchall() or []
        except Exception as e:
            self.db.conn.rollback()
            print(f"[ERREUR] Impossible de récupérer les fournisseurs: {str(e)}")
            return []

    def get_fournisseur_by_id(self, id_fournisseur):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM FOURNISSEUR WHERE id_fournisseur = %s;", (id_fournisseur,))
            return cur.fetchone()

    def create_fournisseur(self, fournisseur):
        try:
            with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO FOURNISSEUR (nom, contact, adresse, telephone, email, delai_livraison_moyen_j, devise, note_qualite)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id_fournisseur;
                    """,
                    (
                        fournisseur["nom"], 
                        fournisseur.get("contact"), 
                        fournisseur.get("adresse"), 
                        fournisseur.get("telephone"),
                        fournisseur.get("email"), 
                        fournisseur.get("delai_livraison_moyen_j"), 
                        fournisseur.get("devise", "EUR"), 
                        fournisseur.get("note_qualite")
                    )
                )
                result = cur.fetchone()
                self.db.conn.commit()
                if result and 'id_fournisseur' in result:
                    return result['id_fournisseur']
                return None
        except Exception as e:
            self.db.conn.rollback()  # Annule la transaction en cas d'erreur
            if 'unique constraint "fournisseur_nom_key"' in str(e):
                raise ValueError(f"Un fournisseur avec le nom '{fournisseur['nom']}' existe déjà.")
            raise  # Relance l'exception pour la gérer plus haut

    def update_fournisseur(self, id_fournisseur, fournisseur):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE FOURNISSEUR
                SET nom=%s, contact=%s, adresse=%s, telephone=%s, email=%s, delai_livraison_moyen_j=%s, devise=%s, note_qualite=%s, updated_at=NOW()
                WHERE id_fournisseur=%s;
                """,
                (
                    fournisseur["nom"], fournisseur.get("contact"), fournisseur.get("adresse"), fournisseur.get("telephone"),
                    fournisseur.get("email"), fournisseur.get("delai_livraison_moyen_j"), fournisseur.get("devise", "EUR"), fournisseur.get("note_qualite"),
                    id_fournisseur
                )
            )
            self.db.conn.commit()

    def delete_fournisseur(self, id_fournisseur):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("DELETE FROM FOURNISSEUR WHERE id_fournisseur = %s;", (id_fournisseur,))
            self.db.conn.commit()
