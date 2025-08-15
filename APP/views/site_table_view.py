from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, QHBoxLayout, QMessageBox, QDialog
from PySide6.QtCore import Qt
from APP.views.site_dialog import SiteDialog

class SiteTableView(QWidget):
    def __init__(self, site_service, parent=None):
        super().__init__(parent)
        self.site_service = site_service
        self.setWindowTitle(self.tr("Sites"))
        self.resize(800, 600)
        layout = QVBoxLayout()
        self.setGeometry(100, 100, 800, 600)
        self.table = QTableWidget(self)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Name"), self.tr("Address"), self.tr("City"), self.tr("Country"), self.tr("Primary contact")
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

        self.add_btn.clicked.connect(self.add_site)
        self.edit_btn.clicked.connect(self.edit_site)
        self.delete_btn.clicked.connect(self.delete_site)
        self.refresh_btn.clicked.connect(self.refresh)
        self.close_btn.clicked.connect(self.close)

        self.refresh()

    def refresh(self):
        sites = self.site_service.list_sites()
        self.table.setRowCount(len(sites))
        for row, s in enumerate(sites):
            self.table.setItem(row, 0, QTableWidgetItem(str(s.get("id_site", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(s.get("nom", "")))
            self.table.setItem(row, 2, QTableWidgetItem(s.get("adresse", "")))
            self.table.setItem(row, 3, QTableWidgetItem(s.get("ville", "")))
            self.table.setItem(row, 4, QTableWidgetItem(s.get("pays", "")))
            self.table.setItem(row, 5, QTableWidgetItem(s.get("contact_principal", "")))

    def get_selected_site(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return {
            "id_site": self.table.item(row, 0).text(),
            "nom": self.table.item(row, 1).text(),
            "adresse": self.table.item(row, 2).text(),
            "ville": self.table.item(row, 3).text(),
            "pays": self.table.item(row, 4).text(),
            "contact_principal": self.table.item(row, 5).text(),
        }

    def add_site(self):
        dialog = SiteDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data is None:
                return
            self.site_service.create_site(data)
            self.refresh()

    def edit_site(self):
        site = self.get_selected_site()
        if not site:
            QMessageBox.warning(self, self.tr("No site selected"), self.tr("Please select a site to edit."))
            return
        dialog = SiteDialog(self)
        dialog.nom.setText(site["nom"])
        dialog.adresse.setText(site["adresse"])
        dialog.ville.setText(site["ville"])
        dialog.pays.setText(site["pays"])
        dialog.contact_principal.setText(site["contact_principal"])
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data is None:
                return
            data["id_site"] = site["id_site"]
            self.site_service.update_site(data)
            self.refresh()

    def delete_site(self):
        site = self.get_selected_site()
        if not site:
            QMessageBox.warning(self, self.tr("No site selected"), self.tr("Please select a site to delete."))
            return
        confirm = QMessageBox.question(self, self.tr("Confirm deletion"), self.tr(f"Delete site '{site['nom']}'?"), QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.site_service.delete_site(site["id_site"])
            self.refresh()
