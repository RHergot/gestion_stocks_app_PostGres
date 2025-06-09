from APP.models.piece_repository import PieceRepository
from APP.services.piece_extension_service import PieceExtensionService
from APP.services.machine_service import MachineService

class PieceService:
    def __init__(self, db):
        self.db = db
        self.repo = PieceRepository(db)
        self.extension_service = PieceExtensionService(db)
        self.machine_service = MachineService(db)

    def get_all_pieces(self):
        return self.repo.get_all_pieces()

    def get_piece_by_id(self, id_piece):
        return self.repo.get_piece_by_id(id_piece)

    def add_piece(self, piece):
        # Séparer les champs extension
        extension = {
            "unite_id": piece.get("unite_id"),
            "categorie_id": piece.get("categorie_id"),
            "emplacement_id": piece.get("emplacement_id"),
            "statut_id": piece.get("statut_id"),
            "machine_id": piece.get("machine_id")
        }
        # Synchroniser les champs texte attendus dans piece
        # Récupérer les noms des entités sélectionnées
        piece["unite"] = self._get_nom_from_id(extension["unite_id"], self.parent_unit_list, "id", "nom")
        piece["categorie"] = self._get_nom_from_id(extension["categorie_id"], self.parent_category_list, "id", "nom")
        piece["emplacement_stockage"] = self._get_nom_from_id(extension["emplacement_id"], self.parent_emplacement_list, "id", "nom")
        piece["statut"] = self._get_nom_from_id(extension["statut_id"], self.parent_statut_list, "id", "nom")
        # Machine (spécifique)
        machine_nom = None
        if extension["machine_id"]:
            machines = self.machine_service.list_machines()
            for m in machines:
                if m["id_machine"] == extension["machine_id"]:
                    machine_nom = m["nom"]
                    break
        piece["machine"] = machine_nom or ""
        id_piece = self.repo.add_piece(piece)
        self.extension_service.add_or_update_extension(id_piece, extension)
        return id_piece

    def update_piece(self, id_piece, piece):
        extension = {
            "unite_id": piece.get("unite_id"),
            "categorie_id": piece.get("categorie_id"),
            "emplacement_id": piece.get("emplacement_id"),
            "statut_id": piece.get("statut_id"),
            "machine_id": piece.get("machine_id")
        }
        piece["unite"] = self._get_nom_from_id(extension["unite_id"], self.parent_unit_list, "id", "nom")
        piece["categorie"] = self._get_nom_from_id(extension["categorie_id"], self.parent_category_list, "id", "nom")
        piece["emplacement_stockage"] = self._get_nom_from_id(extension["emplacement_id"], self.parent_emplacement_list, "id", "nom")
        piece["statut"] = self._get_nom_from_id(extension["statut_id"], self.parent_statut_list, "id", "nom")
        machine_nom = None
        if extension["machine_id"]:
            machines = self.machine_service.list_machines()
            for m in machines:
                if m["id_machine"] == extension["machine_id"]:
                    machine_nom = m["nom"]
                    break
        piece["machine"] = machine_nom or ""
        self.repo.update_piece(id_piece, piece)
        self.extension_service.add_or_update_extension(id_piece, extension)

    # Utilitaire pour retrouver le nom d'une entité à partir de son id et d'une liste
    def _get_nom_from_id(self, id_value, entity_list, id_key, nom_key):
        if not id_value or not entity_list:
            return ""
        for entity in entity_list:
            if entity.get(id_key) == id_value:
                return entity.get(nom_key, "")
        return ""

    def delete_piece(self, id_piece):
        self.extension_service.delete_extension(id_piece)
        self.repo.delete_piece(id_piece)
