class FabricantRepository:
    def __init__(self, db):
        self.db = db

    def get_all_fabricants(self):
        query = "SELECT * FROM FABRICANT ORDER BY id_fabricant"
        return self.db.execute(query)

    def add_fabricant(self, fabricant_data):
        query = """
            INSERT INTO FABRICANT (nom, contact, site_web, support_technique)
            VALUES (%s, %s, %s, %s)
            RETURNING id_fabricant
        """
        values = [
            fabricant_data.get("nom"),
            fabricant_data.get("contact"),
            fabricant_data.get("site_web"),
            fabricant_data.get("support_technique"),
        ]
        return self.db.execute(query, values)

    def update_fabricant(self, fabricant_data):
        query = """
            UPDATE FABRICANT
            SET nom = %s, contact = %s, site_web = %s, support_technique = %s
            WHERE id_fabricant = %s
        """
        values = [
            fabricant_data.get("nom"),
            fabricant_data.get("contact"),
            fabricant_data.get("site_web"),
            fabricant_data.get("support_technique"),
            int(fabricant_data.get("id_fabricant")),
        ]
        return self.db.execute(query, values)

    def delete_fabricant(self, id_fabricant):
        query = "DELETE FROM FABRICANT WHERE id_fabricant = %s"
        return self.db.execute(query, (int(id_fabricant),))
