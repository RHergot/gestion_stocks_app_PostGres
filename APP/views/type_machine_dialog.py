from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QHBoxLayout

class TypeMachineDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("New machine type"))
        layout = QFormLayout(self)

        self.nom = QLineEdit(self)
        self.description = QLineEdit(self)
        self.categorie = QLineEdit(self)

        layout.addRow(self.tr("Name"), self.nom)
        layout.addRow(self.tr("Description"), self.description)
        layout.addRow(self.tr("Category"), self.categorie)

        btns = QHBoxLayout()
        self.ok_btn = QPushButton("OK", self)
        self.cancel_btn = QPushButton("Cancel", self)
        btns.addWidget(self.ok_btn)
        btns.addWidget(self.cancel_btn)
        layout.addRow(btns)

        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def get_data(self):
        if not self.nom.text().strip():
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, self.tr("Input error"), self.tr("Machine type name is required."))
            return None
        return {
            "nom": self.nom.text(),
            "description": self.description.text(),
            "categorie": self.categorie.text(),
        }
