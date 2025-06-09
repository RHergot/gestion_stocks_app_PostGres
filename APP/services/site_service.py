from APP.models.site_repository import SiteRepository

class SiteService:
    def __init__(self, db):
        self.repo = SiteRepository(db)

    def list_sites(self):
        return self.repo.get_all_sites()

    def create_site(self, site_data):
        return self.repo.add_site(site_data)

    def update_site(self, site_data):
        return self.repo.update_site(site_data)

    def delete_site(self, id_site):
        return self.repo.delete_site(id_site)
