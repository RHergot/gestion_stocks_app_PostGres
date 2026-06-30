from PySide6.QtWidgets import QLineEdit
from APP.views.base_crud import BaseCRUDDialog

class TypeMachineDialog(BaseCRUDDialog):
    WINDOW_TITLE = "New machine type"
    ENTITY_NAME = "Machine type"
    REQUIRED_FIELD = "nom"
    FIELDS = [
        ("nom", "Name", QLineEdit, {}),
        ("description", "Description", QLineEdit, {}),
        ("categorie", "Category", QLineEdit, {}),
    ]
