from APP.views.base_crud import BaseCRUDTableView
from APP.views.fabricant_dialog import FabricantDialog

class FabricantTableView(BaseCRUDTableView):
    DIALOG_CLASS = FabricantDialog
    SERVICE_ATTR = "fabricant"
    WINDOW_TITLE = "Manufacturers"
    ENTITY_NAME = "manufacturer"
    ENTITY_NAME_CAP = "Manufacturer"
    ID_FIELD = "id_fabricant"
    COLUMNS = [
        ("id_fabricant", "ID"),
        ("nom", "Name"),
        ("contact", "Contact"),
        ("site_web", "Website"),
        ("support_technique", "Technical support"),
    ]
