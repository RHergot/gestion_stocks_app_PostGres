from APP.models.fabricant_repository import FabricantRepository

class FabricantService:
    def __init__(self, db):
        self.repo = FabricantRepository(db)

    def list_fabricants(self):
        return self.repo.get_all_fabricants()

    def create_fabricant(self, fabricant_data):
        return self.repo.add_fabricant(fabricant_data)

    def update_fabricant(self, fabricant_data):
        return self.repo.update_fabricant(fabricant_data)

    def delete_fabricant(self, id_fabricant):
        return self.repo.delete_fabricant(id_fabricant)
