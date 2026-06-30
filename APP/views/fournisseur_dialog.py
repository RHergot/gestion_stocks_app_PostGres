from PySide6.QtWidgets import QLineEdit, QSpinBox, QDoubleSpinBox
from APP.views.base_crud import BaseCRUDDialog

class FournisseurDialog(BaseCRUDDialog):
    WINDOW_TITLE = "Supplier"
    ENTITY_NAME = "Supplier"
    REQUIRED_FIELD = "nom"
    FIELDS = [
        ("nom", "Name", QLineEdit, {}),
        ("contact", "Contact", QLineEdit, {}),
        ("adresse", "Address", QLineEdit, {}),
        ("telephone", "Phone", QLineEdit, {}),
        ("email", "Email", QLineEdit, {}),
        ("delai_livraison_moyen_j", "Delivery (days)", QSpinBox, {"minimum": 0, "maximum": 365}),
        ("devise", "Currency", QLineEdit, {}),
        ("note_qualite", "Quality (0-5)", QDoubleSpinBox, {"minimum": 0, "maximum": 5, "singleStep": 0.1}),
    ]
