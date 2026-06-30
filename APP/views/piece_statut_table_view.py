from APP.views.base_crud import BaseCRUDTableView
from APP.views.piece_statut_dialog import PieceStatutDialog

class PieceStatutTableView(BaseCRUDTableView):
    DIALOG_CLASS = PieceStatutDialog
    SERVICE_ATTR = "statut"
    WINDOW_TITLE = "Part Statuses"
    ENTITY_NAME = "status"
    ENTITY_NAME_CAP = "Status"
    ID_FIELD = "id"
    COLUMNS = [
        ("id", "ID"),
        ("nom", "Name"),
        ("description", "Description"),
    ]
