from APP.models.user_repository import UserRepository

class UserService:
    def __init__(self, db):
        self.repo = UserRepository(db)

    def list_users(self):
        return self.repo.get_all_users()

    def create_user(self, user_data):
        # Ici, on pourrait ajouter des validations
        return self.repo.add_user(user_data)

    def update_user(self, user_data):
        return self.repo.update_user(user_data)

    def delete_user(self, user_id):
        return self.repo.delete_user(user_id)
