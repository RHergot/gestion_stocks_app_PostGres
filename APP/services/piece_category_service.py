from APP.models.piece_category_repository import PieceCategoryRepository

class PieceCategoryService:
    def __init__(self, db):
        self.repo = PieceCategoryRepository(db)

    def get_all_categories(self):
        return self.repo.get_all_categories()

    def get_category_by_id(self, id):
        return self.repo.get_category_by_id(id)

    def add_category(self, category):
        return self.repo.add_category(category)

    def update_category(self, id, category):
        self.repo.update_category(id, category)

    def delete_category(self, id):
        self.repo.delete_category(id)
