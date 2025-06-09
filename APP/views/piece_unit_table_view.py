from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QHeaderView, QMessageBox, QDialog
from APP.services.piece_unit_service import PieceUnitService
from .piece_unit_dialog import PieceUnitDialog

class PieceUnitTableView(QWidget):
    def __init__(self, unit_service: PieceUnitService, parent=None):
        super().__init__(parent)
        self.unit_service = unit_service
        self.setWindowTitle(self.tr("Units of Measure"))
        self.resize(800, 600)
        layout = QVBoxLayout()
        self.setGeometry(100, 100, 800, 600)
        self.table = QTableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Name"), self.tr("Description")
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
        self.add_btn.clicked.connect(self.add_unit)
        self.edit_btn.clicked.connect(self.edit_unit)
        self.delete_btn.clicked.connect(self.delete_unit)
        self.refresh_btn.clicked.connect(self.refresh)
        self.close_btn.clicked.connect(self.close)
        self.refresh()

    def refresh(self):
        units = self.unit_service.get_all_units()
        self.table.setRowCount(len(units))
        for row, u in enumerate(units):
            self.table.setItem(row, 0, QTableWidgetItem(str(u["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(u["nom"]))
            self.table.setItem(row, 2, QTableWidgetItem(u.get("description", "")))

    def get_selected_unit(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.unit_service.get_unit_by_id(
            int(self.table.item(row, 0).text())
        )

    def add_unit(self):
        dialog = PieceUnitDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                self.unit_service.add_unit(data)
                self.refresh()

    def edit_unit(self):
        unit = self.get_selected_unit()
        if not unit:
            QMessageBox.warning(self, self.tr("No unit selected"), self.tr("Please select a unit to edit."))
            return
        dialog = PieceUnitDialog(self)
        dialog.set_data(unit)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                self.unit_service.update_unit(unit["id"], data)
                self.refresh()

    def delete_unit(self):
        unit = self.get_selected_unit()
        if not unit:
            QMessageBox.warning(self, self.tr("No unit selected"), self.tr("Please select a unit to delete."))
            return
        confirm = QMessageBox.question(self, self.tr("Confirm deletion"), self.tr(f"Delete unit '{unit['nom']}'?"), QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.unit_service.delete_unit(unit["id"])
            self.refresh()
