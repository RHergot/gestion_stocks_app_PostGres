from PySide6.QtWidgets import QLineEdit
from APP.views.base_crud import BaseCRUDDialog

class PieceCategoryDialog(BaseCRUDDialog):
    WINDOW_TITLE = "Part Category"
    ENTITY_NAME = "Category"
    REQUIRED_FIELD = "nom"
    FIELDS = [
        ("nom", "Name", QLineEdit, {}),
        ("description", "Description", QLineEdit, {}),
    ]
