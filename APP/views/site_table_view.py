from APP.views.base_crud import BaseCRUDTableView
from APP.views.site_dialog import SiteDialog

class SiteTableView(BaseCRUDTableView):
    DIALOG_CLASS = SiteDialog
    SERVICE_ATTR = "site"
    WINDOW_TITLE = "Sites"
    ENTITY_NAME = "site"
    ENTITY_NAME_CAP = "Site"
    ID_FIELD = "id_site"
    COLUMNS = [
        ("id_site", "ID"),
        ("nom", "Name"),
        ("adresse", "Address"),
        ("ville", "City"),
        ("pays", "Country"),
        ("contact_principal", "Primary contact"),
    ]
