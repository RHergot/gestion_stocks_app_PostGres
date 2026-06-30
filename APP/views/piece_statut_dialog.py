from PySide6.QtWidgets import QLineEdit
from APP.views.base_crud import BaseCRUDDialog

class PieceStatutDialog(BaseCRUDDialog):
    WINDOW_TITLE = "Part Status"
    ENTITY_NAME = "Status"
    REQUIRED_FIELD = "nom"
    FIELDS = [
        ("nom", "Name", QLineEdit, {}),
        ("description", "Description", QLineEdit, {}),
    ]
