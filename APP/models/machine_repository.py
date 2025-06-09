class MachineRepository:
    def __init__(self, db):
        self.db = db

    def get_all_machines(self):
        query = "SELECT * FROM MACHINE ORDER BY id_machine"
        return self.db.execute(query)

    def add_machine(self, machine_data):
        query = """
            INSERT INTO MACHINE (
                nom, serial, modele, date_installation, localisation, etat, informations_techniques,
                type_machine_id, site_id, fabricant_id, parent_machine_id, criticite, garantie_fin
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_machine
        """
        values = [
            machine_data.get("nom"),
            machine_data.get("serial"),
            machine_data.get("modele"),
            machine_data.get("date_installation"),
            machine_data.get("localisation"),
            machine_data.get("etat"),
            machine_data.get("informations_techniques"),
            int(machine_data.get("type_machine_id")) if machine_data.get("type_machine_id") else None,
            int(machine_data.get("site_id")) if machine_data.get("site_id") else None,
            int(machine_data.get("fabricant_id")) if machine_data.get("fabricant_id") else None,
            int(machine_data.get("parent_machine_id")) if machine_data.get("parent_machine_id") else None,
            machine_data.get("criticite"),
            machine_data.get("garantie_fin"),
        ]
        return self.db.execute(query, values)

    def update_machine(self, machine_data):
        query = """
            UPDATE MACHINE
            SET nom = %s,
                serial = %s,
                modele = %s,
                date_installation = %s,
                localisation = %s,
                etat = %s,
                informations_techniques = %s,
                type_machine_id = %s,
                site_id = %s,
                fabricant_id = %s,
                parent_machine_id = %s,
                criticite = %s,
                garantie_fin = %s
            WHERE id_machine = %s
        """
        def _to_int(val):
            if val in (None, '', 'None'):
                return None
            try:
                return int(val)
            except Exception:
                return None
        values = [
            machine_data.get("nom"),
            machine_data.get("serial"),
            machine_data.get("modele"),
            machine_data.get("date_installation"),
            machine_data.get("localisation"),
            machine_data.get("etat"),
            machine_data.get("informations_techniques"),
            _to_int(machine_data.get("type_machine_id")),
            _to_int(machine_data.get("site_id")),
            _to_int(machine_data.get("fabricant_id")),
            _to_int(machine_data.get("parent_machine_id")),
            machine_data.get("criticite"),
            machine_data.get("garantie_fin"),
            _to_int(machine_data.get("id_machine")),
        ]
        return self.db.execute(query, values)

    def delete_machine(self, id_machine):
        query = "DELETE FROM MACHINE WHERE id_machine = %s"
        return self.db.execute(query, (id_machine,))
