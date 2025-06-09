class TypeMachineRepository:
    def __init__(self, db):
        self.db = db

    def get_all_type_machines(self):
        query = "SELECT * FROM TYPE_MACHINE ORDER BY id_type_machine"
        return self.db.execute(query)

    def add_type_machine(self, type_machine_data):
        query = """
            INSERT INTO TYPE_MACHINE (nom, description, categorie)
            VALUES (%s, %s, %s)
            RETURNING id_type_machine
        """
        values = [
            type_machine_data.get("nom"),
            type_machine_data.get("description"),
            type_machine_data.get("categorie"),
        ]
        return self.db.execute(query, values)

    def update_type_machine(self, type_machine_data):
        query = """
            UPDATE TYPE_MACHINE
            SET nom = %s, description = %s, categorie = %s
            WHERE id_type_machine = %s
        """
        values = [
            type_machine_data.get("nom"),
            type_machine_data.get("description"),
            type_machine_data.get("categorie"),
            int(type_machine_data.get("id_type_machine")),
        ]
        return self.db.execute(query, values)

    def delete_type_machine(self, id_type_machine):
        query = "DELETE FROM TYPE_MACHINE WHERE id_type_machine = %s"
        return self.db.execute(query, (int(id_type_machine),))
