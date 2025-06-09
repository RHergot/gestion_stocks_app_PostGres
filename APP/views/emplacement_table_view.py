from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QHeaderView, QMessageBox, QDialog
from APP.services.emplacement_service import EmplacementService
from .emplacement_dialog import EmplacementDialog
from APP.views.warehouse_layout_view import WarehouseLayoutView # Added import

class EmplacementTableView(QWidget):
    def __init__(self, emplacement_service: EmplacementService, db=None, parent=None):
        super().__init__(parent)
        self.emplacement_service = emplacement_service
        self.db = db
        self.setWindowTitle(self.tr("Locations"))
        self.resize(800, 600)
        layout = QVBoxLayout()
        self.setGeometry(100, 100, 800, 600)
        self.table = QTableWidget(self)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Warehouse ID"), self.tr("Name"), self.tr("Type"), self.tr("Aisle"), self.tr("Shelf"), self.tr("Level")
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton(self.tr("Add"), self)
        self.edit_btn = QPushButton(self.tr("Edit"), self)
        self.delete_btn = QPushButton(self.tr("Delete"), self)
        self.refresh_btn = QPushButton(self.tr("Refresh"), self)
        self.close_btn = QPushButton(self.tr("Close"), self)
        self.grid_view_btn = QPushButton(self.tr("Grid View"), self) # Added Grid View button
        for btn in [self.add_btn, self.edit_btn, self.delete_btn, self.refresh_btn, self.grid_view_btn, self.close_btn]: # Added grid_view_btn to layout
            btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self.add_btn.clicked.connect(self.add_emplacement)
        self.edit_btn.clicked.connect(self.edit_emplacement)
        self.delete_btn.clicked.connect(self.delete_emplacement)
        self.refresh_btn.clicked.connect(self.refresh)
        self.grid_view_btn.clicked.connect(self.show_grid_view) # Connect new button
        self.close_btn.clicked.connect(self.close)
        self.refresh()

    def refresh(self):
        emplacements = self.emplacement_service.get_all_emplacements()
        self.table.setRowCount(len(emplacements))
        for row, e in enumerate(emplacements):
            self.table.setItem(row, 0, QTableWidgetItem(str(e["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(str(e["magasin_id"])))
            self.table.setItem(row, 2, QTableWidgetItem(e["nom"]))
            self.table.setItem(row, 3, QTableWidgetItem(e.get("type", "")))
            self.table.setItem(row, 4, QTableWidgetItem(str(e.get("allee") or "")))
            self.table.setItem(row, 5, QTableWidgetItem(str(e.get("etagere") or "")))
            self.table.setItem(row, 6, QTableWidgetItem(str(e.get("niveau") or "")))

    def get_selected_emplacement(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.emplacement_service.get_emplacement_by_id(
            int(self.table.item(row, 0).text())
        )

    def add_emplacement(self):
        try:
            dialog = EmplacementDialog(self, self.db)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                if data:
                    self.emplacement_service.add_emplacement(data)
                    self.refresh()
                    QMessageBox.information(self, self.tr("Success"), self.tr("Location added successfully."))
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), self.tr(f"Failed to add location: {e}"))

    def edit_emplacement(self):
        try:
            emplacement = self.get_selected_emplacement()
            if not emplacement:
                QMessageBox.warning(self, self.tr("No location selected"), self.tr("Please select a location to edit."))
                return
            
            dialog = EmplacementDialog(self, self.db)
            
            # Charger les données complètes (avec extensions si disponibles)
            if hasattr(self.emplacement_service, 'get_emplacement_complet'):
                emplacement_complet = self.emplacement_service.get_emplacement_complet(emplacement["id"])
                if emplacement_complet:
                    dialog.set_data(emplacement_complet)
                else:
                    dialog.set_data(emplacement)
            else:
                dialog.set_data(emplacement)
            
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                if data:
                    self.emplacement_service.update_emplacement(emplacement["id"], data)
                    self.refresh()
                    QMessageBox.information(self, self.tr("Success"), self.tr("Location updated successfully."))
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), self.tr(f"Failed to update location: {e}"))

    def delete_emplacement(self):
        emplacement = self.get_selected_emplacement()
        if not emplacement:
            QMessageBox.warning(self, self.tr("No location selected"), self.tr("Please select a location to delete."))
            return
        confirm = QMessageBox.question(self, self.tr("Confirm deletion"), self.tr(f"Delete location '{emplacement['nom']}'?"), QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.emplacement_service.delete_emplacement(emplacement["id"])
            self.refresh()

    def show_grid_view(self):
        """Opens the Warehouse Layout View."""
        print("DEBUG: EmplacementTableView.show_grid_view() CALLED")
        # Store the widget as an attribute to prevent it from being garbage collected
        # if it's a top-level window and has no other parent.
        try:
            self.warehouse_layout_widget = WarehouseLayoutView(db=self.db) # No parent, make it top-level
            print(f"DEBUG: WarehouseLayoutView instance created (top-level): {self.warehouse_layout_widget}")
            self.warehouse_layout_widget.show() # Show as a separate window
            print("DEBUG: self.warehouse_layout_widget.show() EXECUTED")
        except Exception as e:
            print(f"DEBUG: EXCEPTION in show_grid_view: {e}")
            QMessageBox.critical(self, self.tr("Error"), self.tr(f"Failed to open Grid View: {e}"))
