from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QHBoxLayout, QMessageBox

class SiteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Ajouter/Modifier un site"))
        layout = QFormLayout(self)

        self.nom = QLineEdit(self)
        self.adresse = QLineEdit(self)
        self.ville = QLineEdit(self)
        self.pays = QLineEdit(self)
        self.contact_principal = QLineEdit(self)

        layout.addRow(self.tr("Nom"), self.nom)
        layout.addRow(self.tr("Adresse"), self.adresse)
        layout.addRow(self.tr("Ville"), self.ville)
        layout.addRow(self.tr("Pays"), self.pays)
        layout.addRow(self.tr("Contact principal"), self.contact_principal)

        btns = QHBoxLayout()
        self.ok_btn = QPushButton(self.tr("OK"), self)
        self.cancel_btn = QPushButton(self.tr("Annuler"), self)
        btns.addWidget(self.ok_btn)
        btns.addWidget(self.cancel_btn)
        layout.addRow(btns)

        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def get_data(self):
        if not self.nom.text().strip():
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, self.tr("Erreur de saisie"), self.tr("Le nom du site est obligatoire."))
            return None
        return {
            "nom": self.nom.text(),
            "adresse": self.adresse.text(),
            "ville": self.ville.text(),
            "pays": self.pays.text(),
            "contact_principal": self.contact_principal.text(),
        }
