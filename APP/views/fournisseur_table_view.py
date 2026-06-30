from APP.views.base_crud import BaseCRUDTableView
from APP.views.fournisseur_dialog import FournisseurDialog

class FournisseurTableView(BaseCRUDTableView):
    DIALOG_CLASS = FournisseurDialog
    SERVICE_ATTR = "fournisseur"
    WINDOW_TITLE = "Suppliers"
    ENTITY_NAME = "supplier"
    ENTITY_NAME_CAP = "Supplier"
    ID_FIELD = "id_fournisseur"
    COLUMNS = [
        ("id_fournisseur", "ID"),
        ("nom", "Name"),
        ("contact", "Contact"),
        ("telephone", "Phone"),
        ("email", "Email"),
        ("delai_livraison_moyen_j", "Delivery (d)"),
        ("devise", "Currency"),
        ("note_qualite", "Quality"),
    ]
