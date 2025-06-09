from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, QHBoxLayout, QMessageBox, QDialog
from PySide6.QtCore import Qt
from APP.views.fabricant_dialog import FabricantDialog

class FabricantTableView(QWidget):
    def __init__(self, fabricant_service, parent=None):
        super().__init__(parent)
        self.fabricant_service = fabricant_service
        self.setWindowTitle("Fabricants")
        self.resize(800, 600)
        layout = QVBoxLayout()
        self.setGeometry(100, 100, 800, 600)
        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nom", "Contact", "Site web", "Support technique"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add", self)
        self.edit_btn = QPushButton("Edit", self)
        self.delete_btn = QPushButton("Delete", self)
        self.refresh_btn = QPushButton("Refresh", self)
        self.close_btn = QPushButton("Close", self)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        self.add_btn.clicked.connect(self.add_fabricant)
        self.edit_btn.clicked.connect(self.edit_fabricant)
        self.delete_btn.clicked.connect(self.delete_fabricant)
        self.refresh_btn.clicked.connect(self.refresh)
        self.close_btn.clicked.connect(self.close)

        self.refresh()

    def refresh(self):
        fabricants = self.fabricant_service.list_fabricants()
        self.table.setRowCount(len(fabricants))
        for row, f in enumerate(fabricants):
            self.table.setItem(row, 0, QTableWidgetItem(str(f.get("id_fabricant", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(f.get("nom", "")))
            self.table.setItem(row, 2, QTableWidgetItem(f.get("contact", "")))
            self.table.setItem(row, 3, QTableWidgetItem(f.get("site_web", "")))
            self.table.setItem(row, 4, QTableWidgetItem(f.get("support_technique", "")))

    def get_selected_fabricant(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return {
            "id_fabricant": self.table.item(row, 0).text(),
            "nom": self.table.item(row, 1).text(),
            "contact": self.table.item(row, 2).text(),
            "site_web": self.table.item(row, 3).text(),
            "support_technique": self.table.item(row, 4).text(),
        }

    def add_fabricant(self):
        dialog = FabricantDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data is None:
                return
            self.fabricant_service.create_fabricant(data)
            self.refresh()

    def edit_fabricant(self):
        fabricant = self.get_selected_fabricant()
        if not fabricant:
            QMessageBox.warning(self, "Aucun fabricant sélectionné", "Veuillez sélectionner un fabricant à modifier.")
            return
        dialog = FabricantDialog(self)
        dialog.nom.setText(fabricant["nom"])
        dialog.contact.setText(fabricant["contact"])
        dialog.site_web.setText(fabricant["site_web"])
        dialog.support_technique.setText(fabricant["support_technique"])
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data is None:
                return
            data["id_fabricant"] = fabricant["id_fabricant"]
            self.fabricant_service.update_fabricant(data)
            self.refresh()

    def delete_fabricant(self):
        fabricant = self.get_selected_fabricant()
        if not fabricant:
            QMessageBox.warning(self, "Aucun fabricant sélectionné", "Veuillez sélectionner un fabricant à supprimer.")
            return
        confirm = QMessageBox.question(self, "Confirmer la suppression", f"Supprimer le fabricant '{fabricant['nom']}' ?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.fabricant_service.delete_fabricant(fabricant["id_fabricant"])
            self.refresh()
