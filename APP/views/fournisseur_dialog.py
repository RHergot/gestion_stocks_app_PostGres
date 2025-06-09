from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QHBoxLayout, QSpinBox, QDoubleSpinBox, QMessageBox

class FournisseurDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Supplier"))
        layout = QFormLayout(self)
        self.nom = QLineEdit(self)
        self.contact = QLineEdit(self)
        self.adresse = QLineEdit(self)
        self.telephone = QLineEdit(self)
        self.email = QLineEdit(self)
        self.delai_livraison_moyen_j = QSpinBox(self)
        self.delai_livraison_moyen_j.setMinimum(0)
        self.delai_livraison_moyen_j.setMaximum(365)
        self.devise = QLineEdit(self)
        self.devise.setText("EUR")
        self.note_qualite = QDoubleSpinBox(self)
        self.note_qualite.setMinimum(0)
        self.note_qualite.setMaximum(5)
        self.note_qualite.setSingleStep(0.1)
        layout.addRow(self.tr("Name"), self.nom)
        layout.addRow(self.tr("Contact"), self.contact)
        layout.addRow(self.tr("Address"), self.adresse)
        layout.addRow(self.tr("Phone"), self.telephone)
        layout.addRow(self.tr("Email"), self.email)
        layout.addRow(self.tr("Delivery (days)"), self.delai_livraison_moyen_j)
        layout.addRow(self.tr("Currency"), self.devise)
        layout.addRow(self.tr("Quality (0-5)"), self.note_qualite)
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
            QMessageBox.warning(self, self.tr("Input error"), self.tr("Supplier name is required."))
            return None
        return {
            "nom": self.nom.text(),
            "contact": self.contact.text(),
            "adresse": self.adresse.text(),
            "telephone": self.telephone.text(),
            "email": self.email.text(),
            "delai_livraison_moyen_j": self.delai_livraison_moyen_j.value(),
            "devise": self.devise.text(),
            "note_qualite": self.note_qualite.value()
        }

    def set_data(self, fournisseur):
        self.nom.setText(fournisseur.get("nom", ""))
        self.contact.setText(fournisseur.get("contact", ""))
        self.adresse.setText(fournisseur.get("adresse", ""))
        self.telephone.setText(fournisseur.get("telephone", ""))
        self.email.setText(fournisseur.get("email", ""))
        if fournisseur.get("delai_livraison_moyen_j") is not None:
            self.delai_livraison_moyen_j.setValue(fournisseur.get("delai_livraison_moyen_j"))
        self.devise.setText(fournisseur.get("devise", "EUR"))
        if fournisseur.get("note_qualite") is not None:
            self.note_qualite.setValue(fournisseur.get("note_qualite"))
