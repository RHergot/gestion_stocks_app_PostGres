from PySide6.QtWidgets import QLineEdit
from APP.views.base_crud import BaseCRUDDialog

class FabricantDialog(BaseCRUDDialog):
    WINDOW_TITLE = "Add/Edit Manufacturer"
    ENTITY_NAME = "Manufacturer"
    REQUIRED_FIELD = "nom"
    FIELDS = [
        ("nom", "Name", QLineEdit, {}),
        ("contact", "Contact", QLineEdit, {}),
        ("site_web", "Website", QLineEdit, {}),
        ("support_technique", "Technical support", QLineEdit, {}),
    ]
