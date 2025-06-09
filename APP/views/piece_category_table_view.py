from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QHeaderView, QMessageBox, QDialog
from APP.services.piece_category_service import PieceCategoryService
from .piece_category_dialog import PieceCategoryDialog

class PieceCategoryTableView(QWidget):
    def __init__(self, category_service: PieceCategoryService, parent=None):
        super().__init__(parent)
        self.category_service = category_service
        self.setWindowTitle(self.tr("Part Categories"))
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
        self.add_btn.clicked.connect(self.add_category)
        self.edit_btn.clicked.connect(self.edit_category)
        self.delete_btn.clicked.connect(self.delete_category)
        self.refresh_btn.clicked.connect(self.refresh)
        self.close_btn.clicked.connect(self.close)
        self.refresh()

    def refresh(self):
        categories = self.category_service.get_all_categories()
        self.table.setRowCount(len(categories))
        for row, c in enumerate(categories):
            self.table.setItem(row, 0, QTableWidgetItem(str(c["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(c["nom"]))
            self.table.setItem(row, 2, QTableWidgetItem(c.get("description", "")))

    def get_selected_category(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.category_service.get_category_by_id(
            int(self.table.item(row, 0).text())
        )

    def add_category(self):
        dialog = PieceCategoryDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                self.category_service.add_category(data)
                self.refresh()

    def edit_category(self):
        category = self.get_selected_category()
        if not category:
            QMessageBox.warning(self, self.tr("No category selected"), self.tr("Please select a category to edit."))
            return
        dialog = PieceCategoryDialog(self)
        dialog.set_data(category)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                self.category_service.update_category(category["id"], data)
                self.refresh()

    def delete_category(self):
        category = self.get_selected_category()
        if not category:
            QMessageBox.warning(self, self.tr("No category selected"), self.tr("Please select a category to delete."))
            return
        confirm = QMessageBox.question(self, self.tr("Confirm deletion"), self.tr(f"Delete category '{category['nom']}'?"), QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.category_service.delete_category(category["id"])
            self.refresh()
