from APP.models.machine_repository import MachineRepository

class MachineService:
    def __init__(self, db):
        self.repo = MachineRepository(db)

    def list_machines(self):
        return self.repo.get_all_machines()

    def get_machine_by_id(self, id_machine):
        return self.repo.get_machine_by_id(id_machine)

    def create_machine(self, machine_data):
        return self.repo.add_machine(machine_data)

    def update_machine(self, machine_data):
        return self.repo.update_machine(machine_data)

    def delete_machine(self, id_machine):
        return self.repo.delete_machine(id_machine)
