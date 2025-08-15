from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QVBoxLayout, QComboBox, QCheckBox

import hashlib

class UserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("New user"))
        form_layout = QFormLayout()
        self.login = QLineEdit(self)
        self.mot_de_passe = QLineEdit(self)
        self.mot_de_passe.setEchoMode(QLineEdit.Password)
        self.nom_complet = QLineEdit(self)
        self.role = QComboBox(self)
        self.role.addItems([self.tr("Admin"), self.tr("User"), self.tr("Guest")])
        self.email = QLineEdit(self)
        self.actif = QCheckBox(self)
        self.actif.setChecked(True)
        form_layout.addRow(self.tr("Login"), self.login)
        form_layout.addRow(self.tr("Password"), self.mot_de_passe)
        form_layout.addRow(self.tr("Full name"), self.nom_complet)
        form_layout.addRow(self.tr("Role"), self.role)
        form_layout.addRow(self.tr("Email"), self.email)
        form_layout.addRow(self.tr("Active"), self.actif)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        vbox = QVBoxLayout()
        vbox.addLayout(form_layout)
        vbox.addWidget(self.buttons)
        self.setLayout(vbox)

    def get_data(self):
        # Hash du mot de passe
        mot_de_passe_hash = hashlib.sha256(self.mot_de_passe.text().encode('utf-8')).hexdigest()
        return {
            "login": self.login.text(),
            "mot_de_passe_hash": mot_de_passe_hash,
            "nom_complet": self.nom_complet.text(),
            "role": self.role.currentText(),
            "email": self.email.text(),
            "actif": 1 if self.actif.isChecked() else 0
        }
