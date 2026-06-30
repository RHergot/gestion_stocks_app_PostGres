from PySide6.QtWidgets import QLineEdit
from APP.views.base_crud import BaseCRUDDialog

class PieceUnitDialog(BaseCRUDDialog):
    WINDOW_TITLE = "Unit of Measure"
    ENTITY_NAME = "Unit"
    REQUIRED_FIELD = "nom"
    FIELDS = [
        ("nom", "Name", QLineEdit, {}),
        ("description", "Description", QLineEdit, {}),
    ]
