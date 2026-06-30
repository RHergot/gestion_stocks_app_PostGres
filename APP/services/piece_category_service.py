from APP.models.piece_category_repository import PieceCategoryRepository

class PieceCategoryService:
    def __init__(self, db):
        self.repo = PieceCategoryRepository(db)

    def list_categories(self):
        return self.repo.list_categories()

    def get_category_by_id(self, id):
        return self.repo.get_category_by_id(id)

    def create_category(self, category):
        return self.repo.create_category(category)

    def update_category(self, id, category):
        self.repo.update_category(id, category)

    def delete_category(self, id):
        self.repo.delete_category(id)
