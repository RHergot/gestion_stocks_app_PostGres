from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QComboBox, QDateEdit, QTextEdit, QPushButton, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QDate

class MachineDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Add/Edit Machine"))
        layout = QFormLayout(self)

        self.nom = QLineEdit(self)
        self.serial = QLineEdit(self)
        self.modele = QLineEdit(self)
        self.date_installation = QDateEdit(self)
        self.date_installation.setCalendarPopup(True)
        self.date_installation.setDisplayFormat("yyyy-MM-dd")
        self.localisation = QLineEdit(self)
        self.etat = QLineEdit(self)
        self.informations_techniques = QTextEdit(self)
        from APP.models.type_machine_repository import TypeMachineRepository
        from APP.models.site_repository import SiteRepository
        from APP.models.fabricant_repository import FabricantRepository
        # Récupérer db via la hiérarchie de widgets — préférer l'injection explicite
        db = None
        if parent is not None:
            db = getattr(parent, 'db', None) or (
                getattr(parent.parent(), 'db', None) if hasattr(parent, 'parent') else None
            )
        self.type_machine_id = QComboBox(self)
        self.site_id = QComboBox(self)
        self.fabricant_id = QComboBox(self)
        self.parent_machine_id = QLineEdit(self)
        self.criticite = QLineEdit(self)
        self.garantie_fin = QDateEdit(self)
        self.garantie_fin.setCalendarPopup(True)
        self.garantie_fin.setDisplayFormat("yyyy-MM-dd")

        # Remplir les combos depuis la base
        if db:
            types = TypeMachineRepository(db).get_all_type_machines() or []
            self.type_machine_id.addItem("", "")
            for t in types:
                self.type_machine_id.addItem(f"{t['nom']} (ID {t['id_type_machine']})", t['id_type_machine'])
            sites = SiteRepository(db).get_all_sites() or []
            self.site_id.addItem("", "")
            for s in sites:
                self.site_id.addItem(f"{s['nom']} (ID {s['id_site']})", s['id_site'])
            fabricants = FabricantRepository(db).get_all_fabricants() or []
            self.fabricant_id.addItem("", "")
            for f in fabricants:
                self.fabricant_id.addItem(f"{f['nom']} (ID {f['id_fabricant']})", f['id_fabricant'])

        layout.addRow(self.tr("Name"), self.nom)
        layout.addRow(self.tr("Serial number"), self.serial)
        layout.addRow(self.tr("Model"), self.modele)
        layout.addRow(self.tr("Installation date"), self.date_installation)
        layout.addRow(self.tr("Location"), self.localisation)
        layout.addRow(self.tr("Status"), self.etat)
        layout.addRow(self.tr("Technical info"), self.informations_techniques)
        layout.addRow(self.tr("Machine type"), self.type_machine_id)
        layout.addRow(self.tr("Site"), self.site_id)
        layout.addRow(self.tr("Manufacturer"), self.fabricant_id)
        layout.addRow(self.tr("Parent machine ID"), self.parent_machine_id)
        layout.addRow(self.tr("Criticality"), self.criticite)
        layout.addRow(self.tr("Warranty end"), self.garantie_fin)

        btns = QHBoxLayout()
        self.ok_btn = QPushButton("OK", self)
        self.cancel_btn = QPushButton("Cancel", self)
        btns.addWidget(self.ok_btn)
        btns.addWidget(self.cancel_btn)
        layout.addRow(btns)

        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def get_data(self):
        # Validation simple
        errors = []
        if not self.nom.text().strip():
            errors.append("Name is required.")
        if not self.type_machine_id.currentData():
            errors.append("Machine type is required.")
        if not self.site_id.currentData():
            errors.append("Site is required.")
        if not self.fabricant_id.currentData():
            errors.append("Manufacturer is required.")
        if errors:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, self.tr("Input error"), self.tr("\n").join([self.tr(e) for e in errors]))
            return None
        return {
            "nom": self.nom.text(),
            "serial": self.serial.text(),
            "modele": self.modele.text(),
            "date_installation": self.date_installation.text(),
            "localisation": self.localisation.text(),
            "etat": self.etat.text(),
            "informations_techniques": self.informations_techniques.toPlainText(),
            "type_machine_id": self.type_machine_id.currentData(),
            "site_id": self.site_id.currentData(),
            "fabricant_id": self.fabricant_id.currentData(),
            "parent_machine_id": self.parent_machine_id.text(),
            "criticite": self.criticite.text(),
            "garantie_fin": self.garantie_fin.text(),
        }
