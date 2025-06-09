from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QHeaderView, QMessageBox, QDialog
from APP.services.piece_statut_service import PieceStatutService
from .piece_statut_dialog import PieceStatutDialog

class PieceStatutTableView(QWidget):
    def __init__(self, statut_service: PieceStatutService, parent=None):
        super().__init__(parent)
        self.statut_service = statut_service
        self.setWindowTitle(self.tr("Part Statuses"))
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
        self.add_btn.clicked.connect(self.add_statut)
        self.edit_btn.clicked.connect(self.edit_statut)
        self.delete_btn.clicked.connect(self.delete_statut)
        self.refresh_btn.clicked.connect(self.refresh)
        self.close_btn.clicked.connect(self.close)
        self.refresh()

    def refresh(self):
        statuts = self.statut_service.get_all_statuts()
        self.table.setRowCount(len(statuts))
        for row, s in enumerate(statuts):
            self.table.setItem(row, 0, QTableWidgetItem(str(s["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(s["nom"]))
            self.table.setItem(row, 2, QTableWidgetItem(s.get("description", "")))

    def get_selected_statut(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.statut_service.get_statut_by_id(
            int(self.table.item(row, 0).text())
        )

    def add_statut(self):
        dialog = PieceStatutDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                self.statut_service.add_statut(data)
                self.refresh()

    def edit_statut(self):
        statut = self.get_selected_statut()
        if not statut:
            QMessageBox.warning(self, self.tr("No status selected"), self.tr("Please select a status to edit."))
            return
        dialog = PieceStatutDialog(self)
        dialog.set_data(statut)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                self.statut_service.update_statut(statut["id"], data)
                self.refresh()

    def delete_statut(self):
        statut = self.get_selected_statut()
        if not statut:
            QMessageBox.warning(self, self.tr("No status selected"), self.tr("Please select a status to delete."))
            return
        confirm = QMessageBox.question(self, self.tr("Confirm deletion"), self.tr(f"Delete status '{statut['nom']}'?"), QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.statut_service.delete_statut(statut["id"])
            self.refresh()
