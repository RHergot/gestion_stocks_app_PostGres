from APP.models.fournisseur_repository import FournisseurRepository

class FournisseurService:
    def __init__(self, db):
        self.repo = FournisseurRepository(db)

    def list_fournisseurs(self):
        return self.repo.list_fournisseurs()

    def get_fournisseur_by_id(self, id_fournisseur):
        return self.repo.get_fournisseur_by_id(id_fournisseur)

    def create_fournisseur(self, fournisseur):
        return self.repo.create_fournisseur(fournisseur)

    def update_fournisseur(self, id_fournisseur, fournisseur):
        self.repo.update_fournisseur(id_fournisseur, fournisseur)

    def delete_fournisseur(self, id_fournisseur):
        self.repo.delete_fournisseur(id_fournisseur)
