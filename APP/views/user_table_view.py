from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, QHBoxLayout, QMessageBox, QDialog
from PySide6.QtCore import Qt

class UserTableView(QWidget):
    def __init__(self, user_service, parent=None):
        super().__init__(parent)
        self.user_service = user_service
        self.setWindowTitle(self.tr("Users"))
        self.resize(800, 600)
        layout = QVBoxLayout()
        self.setGeometry(100, 100, 800, 600)
        self.table = QTableWidget(self)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Login"), self.tr("Full name"), self.tr("Role"), self.tr("Email"), self.tr("Active"), self.tr("Last login")
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        # Boutons d'action
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton(self.tr("Add"), self)
        self.edit_btn = QPushButton(self.tr("Edit"), self)
        self.delete_btn = QPushButton(self.tr("Delete"), self)
        self.refresh_btn = QPushButton(self.tr("Refresh"), self)
        self.close_btn = QPushButton(self.tr("Close"), self)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        self.add_btn.clicked.connect(self.add_user)
        self.edit_btn.clicked.connect(self.edit_user)
        self.delete_btn.clicked.connect(self.delete_user)
        self.refresh_btn.clicked.connect(self.refresh)
        self.close_btn.clicked.connect(self.close)

        self.refresh()

    def refresh(self):
        users = self.user_service.list_users()
        self.table.setRowCount(len(users))
        for row, user in enumerate(users):
            self.table.setItem(row, 0, QTableWidgetItem(str(user.get("id_utilisateur", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(user.get("login", "")))
            self.table.setItem(row, 2, QTableWidgetItem(user.get("nom_complet", "")))
            self.table.setItem(row, 3, QTableWidgetItem(user.get("role", "")))
            self.table.setItem(row, 4, QTableWidgetItem(user.get("email", "")))
            self.table.setItem(row, 5, QTableWidgetItem(self.tr("Yes") if user.get("actif") else self.tr("No")))
            self.table.setItem(row, 6, QTableWidgetItem(user.get("derniere_connexion", "")))

    def get_selected_user(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        user = {
            "id_utilisateur": self.table.item(row, 0).text(),
            "login": self.table.item(row, 1).text(),
            "nom_complet": self.table.item(row, 2).text(),
            "role": self.table.item(row, 3).text(),
            "email": self.table.item(row, 4).text(),
            "actif": self.table.item(row, 5).text() == self.tr("Yes"),
            "derniere_connexion": self.table.item(row, 6).text(),
        }
        return user

    def add_user(self):
        from .user_dialog import UserDialog
        dialog = UserDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            self.user_service.create_user(data)
            self.refresh()

    def edit_user(self):
        user = self.get_selected_user()
        if not user:
            QMessageBox.warning(self, self.tr("No user selected"), self.tr("Please select a user to edit."))
            return
        from .user_dialog import UserDialog
        dialog = UserDialog(self)
        # Pré-remplir les champs
        dialog.login.setText(user["login"])
        dialog.nom_complet.setText(user["nom_complet"])
        dialog.role.setCurrentText(user["role"])
        dialog.email.setText(user["email"])
        dialog.actif.setChecked(user["actif"])
        # On ne pré-remplit pas le mot de passe (sécurité)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            data["id_utilisateur"] = user["id_utilisateur"]
            self.user_service.update_user(data)
            self.refresh()

    def delete_user(self):
        user = self.get_selected_user()
        if not user:
            QMessageBox.warning(self, self.tr("No user selected"), self.tr("Please select a user to delete."))
            return
        confirm = QMessageBox.question(self, self.tr("Confirm deletion"), self.tr(f"Delete user {user['login']}?"))
        if confirm == QMessageBox.Yes:
            self.user_service.delete_user(user["id_utilisateur"])
            self.refresh()
