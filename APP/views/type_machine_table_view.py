from APP.views.base_crud import BaseCRUDTableView
from APP.views.type_machine_dialog import TypeMachineDialog

class TypeMachineTableView(BaseCRUDTableView):
    DIALOG_CLASS = TypeMachineDialog
    SERVICE_ATTR = "type_machine"
    WINDOW_TITLE = "Machine Types"
    ENTITY_NAME = "machine type"
    ENTITY_NAME_CAP = "Machine Type"
    ID_FIELD = "id_type_machine"
    COLUMNS = [
        ("id_type_machine", "ID"),
        ("nom", "Name"),
        ("description", "Description"),
        ("categorie", "Category"),
    ]
