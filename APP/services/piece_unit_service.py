from APP.models.piece_unit_repository import PieceUnitRepository

class PieceUnitService:
    def __init__(self, db):
        self.repo = PieceUnitRepository(db)

    def list_units(self):
        return self.repo.list_units()

    def get_unit_by_id(self, id):
        return self.repo.get_unit_by_id(id)

    def create_unit(self, unit):
        return self.repo.create_unit(unit)

    def update_unit(self, id, unit):
        self.repo.update_unit(id, unit)

    def delete_unit(self, id):
        self.repo.delete_unit(id)
