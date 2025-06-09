from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QHBoxLayout, QMessageBox

class PieceCategoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Part Category"))
        layout = QFormLayout(self)
        self.nom = QLineEdit(self)
        self.description = QLineEdit(self)
        layout.addRow(self.tr("Name"), self.nom)
        layout.addRow(self.tr("Description"), self.description)
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
            QMessageBox.warning(self, self.tr("Input error"), self.tr("Name is required."))
            return None
        return {
            "nom": self.nom.text(),
            "description": self.description.text()
        }

    def set_data(self, category):
        self.nom.setText(category.get("nom", ""))
        self.description.setText(category.get("description", ""))
