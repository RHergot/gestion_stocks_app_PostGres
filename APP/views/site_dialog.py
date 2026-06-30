from PySide6.QtWidgets import QLineEdit
from APP.views.base_crud import BaseCRUDDialog

class SiteDialog(BaseCRUDDialog):
    WINDOW_TITLE = "Add/Edit Site"
    ENTITY_NAME = "Site"
    REQUIRED_FIELD = "nom"
    FIELDS = [
        ("nom", "Name", QLineEdit, {}),
        ("adresse", "Address", QLineEdit, {}),
        ("ville", "City", QLineEdit, {}),
        ("pays", "Country", QLineEdit, {}),
        ("contact_principal", "Primary contact", QLineEdit, {}),
    ]
