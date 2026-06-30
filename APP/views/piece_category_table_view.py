from APP.views.base_crud import BaseCRUDTableView
from APP.views.piece_category_dialog import PieceCategoryDialog

class PieceCategoryTableView(BaseCRUDTableView):
    DIALOG_CLASS = PieceCategoryDialog
    SERVICE_ATTR = "category"
    WINDOW_TITLE = "Part Categories"
    ENTITY_NAME = "category"
    ENTITY_NAME_CAP = "Category"
    ID_FIELD = "id"
    COLUMNS = [
        ("id", "ID"),
        ("nom", "Name"),
        ("description", "Description"),
    ]
