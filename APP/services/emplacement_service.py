from APP.models.emplacement_repository import EmplacementRepository
from APP.services.emplacement_ext_service import EmplacementExtService

class EmplacementService:
    def __init__(self, db):
        self.db = db
        self.repo = EmplacementRepository(db)
        self.ext_service = EmplacementExtService(db)

    def get_all_emplacements(self):
        return self.repo.get_all_emplacements()

    def get_all_warehouses(self):
        """Récupère tous les magasins (entrepôts)."""
        try:
            # This will call a new method in EmplacementRepository
            return self.repo.get_all_warehouses()
        except Exception as e:
            print(f"[ERREUR] Impossible de récupérer les magasins: {e}")
            return [] # Return an empty list in case of error

    def get_emplacement_by_id(self, id):
        return self.repo.get_emplacement_by_id(id)

    def add_emplacement(self, emplacement_data):
        """Ajoute un emplacement avec support des extensions"""
        try:
            # Vérifier si les données viennent du nouveau dialogue (avec base/extension)
            if isinstance(emplacement_data, dict) and 'base' in emplacement_data:
                # Nouveau format avec extensions
                base_data = emplacement_data['base']
                extension_data = emplacement_data.get('extension', {})
                
                # Créer l'emplacement de base
                emplacement_id = self.repo.add_emplacement(base_data)
                
                # Ajouter les extensions si présentes
                if extension_data and emplacement_id:
                    self.ext_service.creer_ou_modifier_emplacement_ext(emplacement_id, extension_data)
                
                return emplacement_id
            else:
                # Ancien format - compatibilité descendante
                return self.repo.add_emplacement(emplacement_data)
                
        except Exception as e:
            print(f"[ERREUR] Impossible d'ajouter l'emplacement: {e}")
            raise

    def update_emplacement(self, id, emplacement_data):
        """Met à jour un emplacement avec support des extensions"""
        try:
            # Vérifier si les données viennent du nouveau dialogue (avec base/extension)
            if isinstance(emplacement_data, dict) and 'base' in emplacement_data:
                # Nouveau format avec extensions
                base_data = emplacement_data['base']
                extension_data = emplacement_data.get('extension', {})
                
                # Mettre à jour l'emplacement de base
                self.repo.update_emplacement(id, base_data)
                
                # Mettre à jour les extensions
                if extension_data:
                    self.ext_service.creer_ou_modifier_emplacement_ext(id, extension_data)
            else:
                # Ancien format - compatibilité descendante
                self.repo.update_emplacement(id, emplacement_data)
                
        except Exception as e:
            print(f"[ERREUR] Impossible de mettre à jour l'emplacement: {e}")
            raise

    def delete_emplacement(self, id):
        """Supprime un emplacement et ses extensions"""
        try:
            # Supprimer les extensions (cascade automatique via FK)
            self.repo.delete_emplacement(id)
        except Exception as e:
            print(f"[ERREUR] Impossible de supprimer l'emplacement: {e}")
            raise

    def get_emplacement_complet(self, id):
        """Récupère un emplacement avec ses extensions"""
        try:
            return self.ext_service.get_emplacement_complet(id)
        except Exception as e:
            print(f"[ERREUR] Impossible de récupérer l'emplacement complet: {e}")
            return self.repo.get_emplacement_by_id(id)
