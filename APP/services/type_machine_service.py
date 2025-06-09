from APP.models.type_machine_repository import TypeMachineRepository

class TypeMachineService:
    def __init__(self, db):
        self.repo = TypeMachineRepository(db)

    def list_type_machines(self):
        return self.repo.get_all_type_machines()

    def create_type_machine(self, type_machine_data):
        return self.repo.add_type_machine(type_machine_data)

    def update_type_machine(self, type_machine_data):
        return self.repo.update_type_machine(type_machine_data)

    def delete_type_machine(self, id_type_machine):
        return self.repo.delete_type_machine(id_type_machine)
