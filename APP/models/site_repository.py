class SiteRepository:
    def __init__(self, db):
        self.db = db

    def get_all_sites(self):
        query = "SELECT * FROM SITE ORDER BY id_site"
        return self.db.execute(query)

    def add_site(self, site_data):
        query = """
            INSERT INTO SITE (nom, adresse, ville, pays, contact_principal)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id_site
        """
        values = [
            site_data.get("nom"),
            site_data.get("adresse"),
            site_data.get("ville"),
            site_data.get("pays"),
            site_data.get("contact_principal"),
        ]
        return self.db.execute(query, values)

    def update_site(self, site_data):
        query = """
            UPDATE SITE
            SET nom = %s, adresse = %s, ville = %s, pays = %s, contact_principal = %s
            WHERE id_site = %s
        """
        values = [
            site_data.get("nom"),
            site_data.get("adresse"),
            site_data.get("ville"),
            site_data.get("pays"),
            site_data.get("contact_principal"),
            int(site_data.get("id_site")),
        ]
        return self.db.execute(query, values)

    def delete_site(self, id_site):
        query = "DELETE FROM SITE WHERE id_site = %s"
        return self.db.execute(query, (int(id_site),))
