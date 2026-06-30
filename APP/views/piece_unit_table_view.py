from APP.views.base_crud import BaseCRUDTableView
from APP.views.piece_unit_dialog import PieceUnitDialog

class PieceUnitTableView(BaseCRUDTableView):
    DIALOG_CLASS = PieceUnitDialog
    SERVICE_ATTR = "unit"
    WINDOW_TITLE = "Units of Measure"
    ENTITY_NAME = "unit"
    ENTITY_NAME_CAP = "Unit"
    ID_FIELD = "id"
    COLUMNS = [
        ("id", "ID"),
        ("nom", "Name"),
        ("description", "Description"),
    ]
