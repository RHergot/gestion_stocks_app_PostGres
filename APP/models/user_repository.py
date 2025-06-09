from APP.services.db import Database

class UserRepository:
    def __init__(self, db: Database):
        self.db = db

    def get_all_users(self):
        query = "SELECT * FROM UTILISATEUR ORDER BY id_utilisateur"
        return self.db.execute(query)

    def add_user(self, user_data):
        query = """
            INSERT INTO UTILISATEUR (login, mot_de_passe_hash, nom_complet, role, email, actif)
            VALUES (%(login)s, %(mot_de_passe_hash)s, %(nom_complet)s, %(role)s, %(email)s, %(actif)s)
            RETURNING id_utilisateur
        """
        return self.db.execute(query, user_data)

    def update_user(self, user_data):
        query = """
            UPDATE UTILISATEUR
            SET login = %(login)s,
                mot_de_passe_hash = %(mot_de_passe_hash)s,
                nom_complet = %(nom_complet)s,
                role = %(role)s,
                email = %(email)s,
                actif = %(actif)s
            WHERE id_utilisateur = %(id_utilisateur)s
        """
        return self.db.execute(query, user_data)

    def delete_user(self, user_id):
        query = "DELETE FROM UTILISATEUR WHERE id_utilisateur = %s"
        return self.db.execute(query, (user_id,))

    # Ajoutez ici update_user, delete_user si besoin
