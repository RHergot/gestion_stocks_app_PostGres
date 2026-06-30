from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QHBoxLayout

class FabricantDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Add/Edit Manufacturer"))
        layout = QFormLayout(self)

        self.nom = QLineEdit(self)
        self.contact = QLineEdit(self)
        self.site_web = QLineEdit(self)
        self.support_technique = QLineEdit(self)

        layout.addRow(self.tr("Name"), self.nom)
        layout.addRow(self.tr("Contact"), self.contact)
        layout.addRow(self.tr("Website"), self.site_web)
        layout.addRow(self.tr("Technical support"), self.support_technique)

        btns = QHBoxLayout()
        self.ok_btn = QPushButton(self.tr("OK"), self)
        self.cancel_btn = QPushButton(self.tr("Cancel"), self)
        btns.addWidget(self.ok_btn)
        btns.addWidget(self.cancel_btn)
        layout.addRow(btns)

        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def get_data(self):
        if not self.nom.text().strip():
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, self.tr("Input error"), self.tr("Manufacturer name is required."))
            return None
        return {
            "nom": self.nom.text(),
            "contact": self.contact.text(),
            "site_web": self.site_web.text(),
            "support_technique": self.support_technique.text(),
        }
