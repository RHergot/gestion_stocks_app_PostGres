from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, QHBoxLayout, QMessageBox, QDialog
from PySide6.QtCore import Qt
from APP.views.type_machine_dialog import TypeMachineDialog

class TypeMachineTableView(QWidget):
    def __init__(self, type_machine_service, parent=None):
        super().__init__(parent)
        self.type_machine_service = type_machine_service
        self.setWindowTitle(self.tr("Types de machine"))
        self.resize(800, 600)
        layout = QVBoxLayout()
        self.setGeometry(100, 100, 800, 600)
        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Nom"), self.tr("Description"), self.tr("Catégorie")
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

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

        self.add_btn.clicked.connect(self.add_type_machine)
        self.edit_btn.clicked.connect(self.edit_type_machine)
        self.delete_btn.clicked.connect(self.delete_type_machine)
        self.refresh_btn.clicked.connect(self.refresh)
        self.close_btn.clicked.connect(self.close)

        self.refresh()

    def refresh(self):
        type_machines = self.type_machine_service.list_type_machines()
        self.table.setRowCount(len(type_machines))
        for row, t in enumerate(type_machines):
            self.table.setItem(row, 0, QTableWidgetItem(str(t.get("id_type_machine", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(t.get("nom", "")))
            self.table.setItem(row, 2, QTableWidgetItem(t.get("description", "")))
            self.table.setItem(row, 3, QTableWidgetItem(t.get("categorie", "")))

    def get_selected_type_machine(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return {
            "id_type_machine": self.table.item(row, 0).text(),
            "nom": self.table.item(row, 1).text(),
            "description": self.table.item(row, 2).text(),
            "categorie": self.table.item(row, 3).text(),
        }

    def add_type_machine(self):
        dialog = TypeMachineDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data is None:
                return
            self.type_machine_service.create_type_machine(data)
            self.refresh()

    def edit_type_machine(self):
        type_machine = self.get_selected_type_machine()
        if not type_machine:
            QMessageBox.warning(self, self.tr("Aucun type sélectionné"), self.tr("Veuillez sélectionner un type à modifier."))
            return
        dialog = TypeMachineDialog(self)
        dialog.nom.setText(type_machine["nom"])
        dialog.description.setText(type_machine["description"])
        dialog.categorie.setText(type_machine["categorie"])
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data is None:
                return
            data["id_type_machine"] = type_machine["id_type_machine"]
            self.type_machine_service.update_type_machine(data)
            self.refresh()

    def delete_type_machine(self):
        type_machine = self.get_selected_type_machine()
        if not type_machine:
            QMessageBox.warning(self, self.tr("Aucun type sélectionné"), self.tr("Veuillez sélectionner un type à supprimer."))
            return
        confirm = QMessageBox.question(self, self.tr("Confirmer la suppression"), self.tr(f"Supprimer le type '{type_machine['nom']}' ?"), QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.type_machine_service.delete_type_machine(type_machine["id_type_machine"])
            self.refresh()
