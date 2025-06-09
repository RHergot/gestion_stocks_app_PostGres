from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QHeaderView, QMessageBox, QDialog
from APP.services.fournisseur_service import FournisseurService
from .fournisseur_dialog import FournisseurDialog

class FournisseurTableView(QWidget):
    def __init__(self, fournisseur_service: FournisseurService, parent=None):
        super().__init__(parent)
        self.fournisseur_service = fournisseur_service
        self.setWindowTitle(self.tr("Suppliers"))
        self.resize(800, 600)
        layout = QVBoxLayout()
        self.setGeometry(100, 100, 800, 600)
        self.table = QTableWidget(self)
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Name"), self.tr("Contact"), self.tr("Address"), self.tr("Phone"), self.tr("Email"),
            self.tr("Delivery (days)"), self.tr("Currency"), self.tr("Quality")
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton(self.tr("Add"), self)
        self.edit_btn = QPushButton(self.tr("Edit"), self)
        self.delete_btn = QPushButton(self.tr("Delete"), self)
        self.refresh_btn = QPushButton(self.tr("Refresh"), self)
        self.close_btn = QPushButton(self.tr("Close"), self)
        for btn in [self.add_btn, self.edit_btn, self.delete_btn, self.refresh_btn, self.close_btn]:
            btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self.add_btn.clicked.connect(self.add_fournisseur)
        self.edit_btn.clicked.connect(self.edit_fournisseur)
        self.delete_btn.clicked.connect(self.delete_fournisseur)
        self.refresh_btn.clicked.connect(self.refresh)
        self.close_btn.clicked.connect(self.close)
        self.refresh()

    def refresh(self):
        fournisseurs = self.fournisseur_service.get_all_fournisseurs()
        self.table.setRowCount(len(fournisseurs))
        for row, f in enumerate(fournisseurs):
                        # f peut être un tuple ou un dict selon le curseur utilisé
            if isinstance(f, dict):
                self.table.setItem(row, 0, QTableWidgetItem(str(f.get("id_fournisseur", ""))))
                self.table.setItem(row, 1, QTableWidgetItem(f.get("nom", "")))
                self.table.setItem(row, 2, QTableWidgetItem(f.get("contact", "")))
                self.table.setItem(row, 3, QTableWidgetItem(f.get("adresse", "")))
                self.table.setItem(row, 4, QTableWidgetItem(f.get("telephone", "")))
                self.table.setItem(row, 5, QTableWidgetItem(f.get("email", "")))
                self.table.setItem(row, 6, QTableWidgetItem(str(f.get("delai_livraison_moyen_j") or "")))
                self.table.setItem(row, 7, QTableWidgetItem(f.get("devise", "EUR")))
                self.table.setItem(row, 8, QTableWidgetItem(str(f.get("note_qualite") or "")))
            else:
                self.table.setItem(row, 0, QTableWidgetItem(str(f[0])))
                self.table.setItem(row, 1, QTableWidgetItem(f[1]))
                self.table.setItem(row, 2, QTableWidgetItem(f[2] if f[2] else ""))
                self.table.setItem(row, 3, QTableWidgetItem(f[3] if f[3] else ""))
                self.table.setItem(row, 4, QTableWidgetItem(f[4] if f[4] else ""))
                self.table.setItem(row, 5, QTableWidgetItem(f[5] if f[5] else ""))
                self.table.setItem(row, 6, QTableWidgetItem(str(f[6]) if f[6] is not None else ""))
                self.table.setItem(row, 7, QTableWidgetItem(f[7] if f[7] else "EUR"))
                self.table.setItem(row, 8, QTableWidgetItem(str(f[8]) if f[8] is not None else ""))

    def get_selected_fournisseur(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.fournisseur_service.get_fournisseur_by_id(
            int(self.table.item(row, 0).text())
        )

    def add_fournisseur(self):
        dialog = FournisseurDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                try:
                    self.fournisseur_service.add_fournisseur(data)
                    QMessageBox.information(self, 
                        self.tr("Succès"), 
                        self.tr("Le fournisseur a été ajouté avec succès."))
                    self.refresh()
                except ValueError as e:
                    QMessageBox.warning(self, 
                        self.tr("Erreur"), 
                        str(e))
                except Exception as e:
                    QMessageBox.critical(self, 
                        self.tr("Erreur"), 
                        self.tr("Une erreur est survenue lors de l'ajout du fournisseur.") + f"\n\nDétails: {str(e)}")

    def edit_fournisseur(self):
        fournisseur = self.get_selected_fournisseur()
        if not fournisseur:
            QMessageBox.warning(self, self.tr("No supplier selected"), self.tr("Please select a supplier to edit."))
            return
        dialog = FournisseurDialog(self)
        dialog.set_data(fournisseur)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                self.fournisseur_service.update_fournisseur(fournisseur["id_fournisseur"], data)
                self.refresh()

    def delete_fournisseur(self):
        fournisseur = self.get_selected_fournisseur()
        if not fournisseur:
            QMessageBox.warning(self, self.tr("No supplier selected"), self.tr("Please select a supplier to delete."))
            return
        confirm = QMessageBox.question(self, self.tr("Confirm deletion"), self.tr(f"Delete supplier '{fournisseur['nom']}'?"), QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.fournisseur_service.delete_fournisseur(fournisseur["id_fournisseur"])
            self.refresh()
