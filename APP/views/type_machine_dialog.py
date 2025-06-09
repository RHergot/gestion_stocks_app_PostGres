from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QHBoxLayout

class TypeMachineDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Nouveau type de machine"))
        layout = QFormLayout(self)

        self.nom = QLineEdit(self)
        self.description = QLineEdit(self)
        self.categorie = QLineEdit(self)

        layout.addRow(self.tr("Nom"), self.nom)
        layout.addRow(self.tr("Description"), self.description)
        layout.addRow(self.tr("Catégorie"), self.categorie)

        btns = QHBoxLayout()
        self.ok_btn = QPushButton("OK", self)
        self.cancel_btn = QPushButton("Annuler", self)
        btns.addWidget(self.ok_btn)
        btns.addWidget(self.cancel_btn)
        layout.addRow(btns)

        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def get_data(self):
        if not self.nom.text().strip():
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, self.tr("Erreur de saisie"), self.tr("Le nom du type de machine est obligatoire."))
            return None
        return {
            "nom": self.nom.text(),
            "description": self.description.text(),
            "categorie": self.categorie.text(),
        }
