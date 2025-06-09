from APP.models.piece_extension_repository import PieceExtensionRepository

class PieceExtensionService:
    def __init__(self, db):
        self.repo = PieceExtensionRepository(db)

    def get_by_piece_id(self, id_piece):
        return self.repo.get_by_piece_id(id_piece)

    def add_or_update_extension(self, id_piece, extension):
        self.repo.add_or_update_extension(id_piece, extension)

    def delete_extension(self, id_piece):
        self.repo.delete_extension(id_piece)
