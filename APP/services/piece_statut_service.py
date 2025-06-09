from APP.models.piece_statut_repository import PieceStatutRepository

class PieceStatutService:
    def __init__(self, db):
        self.repo = PieceStatutRepository(db)

    def get_all_statuts(self):
        return self.repo.get_all_statuts()

    def get_statut_by_id(self, id):
        return self.repo.get_statut_by_id(id)

    def add_statut(self, statut):
        return self.repo.add_statut(statut)

    def update_statut(self, id, statut):
        self.repo.update_statut(id, statut)

    def delete_statut(self, id):
        self.repo.delete_statut(id)
