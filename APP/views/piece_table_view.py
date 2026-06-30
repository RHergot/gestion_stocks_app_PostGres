from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QHeaderView, QMessageBox, QDialog, QMenuBar, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from APP.services.piece_service import PieceService
from .piece_dialog import PieceDialog
from .piece_delete_dialog import PieceDeleteDialog

class PieceTableView(QWidget):
    def __init__(self, piece_service: PieceService, parent=None):
        super().__init__(parent)
        self.piece_service = piece_service
        self.setWindowTitle(self.tr("Parts"))
        self.resize(1100, 500)
        layout = QVBoxLayout()
        # Barre de menu locale
        from PySide6.QtWidgets import QMenuBar, QMenu
        from PySide6.QtGui import QAction
        self.menu_bar = QMenuBar(self)
        selection_menu = self.menu_bar.addMenu(self.tr("Selection"))
        # 1. Pièces en stock faible
        stock_faible_action = QAction(self.tr("Low stock parts"), self)
        stock_faible_action.triggered.connect(self.show_stock_faible)
        selection_menu.addAction(stock_faible_action)
        # 2. Pièces par machine
        par_machine_action = QAction(self.tr("Parts by machine"), self)
        par_machine_action.triggered.connect(self.show_pieces_by_machine)
        selection_menu.addAction(par_machine_action)
        # 3. Inventaire par catégorie
        inventaire_categorie_action = QAction(self.tr("Inventory by category"), self)
        inventaire_categorie_action.triggered.connect(self.show_inventaire_categorie)
        selection_menu.addAction(inventaire_categorie_action)
        # 4. Emplacements sous-utilisés
        emplacements_vides_action = QAction(self.tr("Underutilized locations"), self)
        emplacements_vides_action.triggered.connect(self.show_emplacements_vides)
        selection_menu.addAction(emplacements_vides_action)
        # 5. Pièces par statut
        par_statut_action = QAction(self.tr("Parts by status"), self)
        par_statut_action.triggered.connect(self.show_pieces_by_statut)
        selection_menu.addAction(par_statut_action)
        layout.addWidget(self.menu_bar)
        self.table = QTableWidget(self)
        self.table.setColumnCount(13)
        self.table.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Reference"), self.tr("Name"), self.tr("Preferred Supplier"), self.tr("Unit Price"),
            self.tr("Alert Stock"), self.tr("Current Stock"), self.tr("Reserved Stock"), self.tr("Unit"), self.tr("Category"),
            self.tr("Location"), self.tr("Status"), self.tr("Machine")
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSortingEnabled(True)
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
        # Ensure this widget behaves as a top-level window (movable/resizable)
        # even if it has a parent (we use parent to access services).
        self.setWindowFlags(self.windowFlags() | Qt.Window)
        self.setWindowModality(Qt.NonModal)
        self.add_btn.clicked.connect(self.add_piece)
        self.edit_btn.clicked.connect(self.edit_piece)
        self.delete_btn.clicked.connect(self.delete_piece)
        self.refresh_btn.clicked.connect(self.refresh)
        self.close_btn.clicked.connect(self.close)
        self.refresh()

    def refresh(self):
        pieces = self.piece_service.get_all_pieces()
        self.set_pieces_table(pieces)

    def set_pieces_table(self, pieces):
        self.table.setColumnCount(13)
        self.table.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Reference"), self.tr("Name"), self.tr("Preferred Supplier"), self.tr("Unit Price"),
            self.tr("Alert Stock"), self.tr("Current Stock"), self.tr("Reserved Stock"), self.tr("Unit"), self.tr("Category"),
            self.tr("Location"), self.tr("Status"), self.tr("Machine")
        ])
        self.table.setRowCount(len(pieces))
        for row, p in enumerate(pieces):
            self.table.setItem(row, 0, QTableWidgetItem(str(p["id_piece"])))
            self.table.setItem(row, 1, QTableWidgetItem(p["reference"]))
            self.table.setItem(row, 2, QTableWidgetItem(p["nom"]))
            self.table.setItem(row, 3, QTableWidgetItem(str(p.get("fournisseur_pref_id") or "")))
            self.table.setItem(row, 4, QTableWidgetItem(str(p.get("prix_unitaire") or "")))
            self.table.setItem(row, 5, QTableWidgetItem(str(p.get("stock_alerte") or "")))
            self.table.setItem(row, 6, QTableWidgetItem(str(p.get("stock_actuel") or "")))
            self.table.setItem(row, 7, QTableWidgetItem(str(p.get("stock_reserve") or "")))
            self.table.setItem(row, 8, QTableWidgetItem(p["unite"]))
            self.table.setItem(row, 9, QTableWidgetItem(p.get("categorie", "")))
            self.table.setItem(row, 10, QTableWidgetItem(p.get("emplacement_stockage", "")))
            self.table.setItem(row, 11, QTableWidgetItem(p.get("statut", "")))
            self.table.setItem(row, 12, QTableWidgetItem(p.get("machine", "")))

    def populate_table_selection(self, headers, data_rows):
        self.table.clear()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(data_rows))
        for row_idx, row in enumerate(data_rows):
            for col_idx, value in enumerate(row):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

    def get_selected_piece(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.piece_service.get_piece_by_id(
            int(self.table.item(row, 0).text())
        )

    def show_stock_faible(self):
        pieces = self.piece_service.get_pieces_stock_faible()
        self.set_pieces_table(pieces)

    def show_pieces_by_machine(self):
        pieces = self.piece_service.get_pieces_by_machine()
        self.set_pieces_table(pieces)

    def show_inventaire_categorie(self):
        pieces = self.piece_service.get_pieces_by_categorie()
        self.set_pieces_table(pieces)

    def show_emplacements_vides(self):
        pieces = self.piece_service.get_pieces_emplacements_sous_utilises()
        self.set_pieces_table(pieces)

    def show_pieces_by_statut(self):
        pieces = self.piece_service.get_pieces_by_statut()
        self.set_pieces_table(pieces)

    def add_piece(self):
        fournisseurs = self.parent().fournisseur_service.list_fournisseurs()
        unites = self.parent().piece_unit_service.list_units()
        categories = self.parent().piece_category_service.list_categories()
        emplacements = self.parent().emplacement_service.get_all_emplacements()
        statuts = self.parent().piece_statut_service.list_statuts()
        machines = self.parent().machine_service.list_machines()
        warehouses = self.parent().emplacement_service.get_all_warehouses()
        dialog = PieceDialog(self, db=self.piece_service.db, warehouses=warehouses, fournisseurs=fournisseurs, unites=unites, categories=categories, emplacements=emplacements, statuts=statuts, machines=machines)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                self.piece_service.add_piece(data)
                self.refresh()

    def edit_piece(self):
        piece = self.get_selected_piece()
        if not piece:
            QMessageBox.warning(self, self.tr("No part selected"), self.tr("Please select a part to edit."))
            return
        fournisseurs = self.parent().fournisseur_service.list_fournisseurs()
        unites = self.parent().piece_unit_service.list_units()
        categories = self.parent().piece_category_service.list_categories()
        emplacements = self.parent().emplacement_service.get_all_emplacements()
        statuts = self.parent().piece_statut_service.list_statuts()
        machines = self.parent().machine_service.list_machines()
        warehouses = self.parent().emplacement_service.get_all_warehouses()
        dialog = PieceDialog(self, db=self.piece_service.db, warehouses=warehouses, fournisseurs=fournisseurs, unites=unites, categories=categories, emplacements=emplacements, statuts=statuts, machines=machines)
        dialog.set_data(piece)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                self.piece_service.update_piece(piece["id_piece"], data)
                self.refresh()

    def delete_piece(self):
        piece = self.get_selected_piece()
        if not piece:
            QMessageBox.warning(self, self.tr("No part selected"), self.tr("Please select a part to delete."))
            return
        dlg = PieceDeleteDialog(self, self.piece_service, piece)
        if dlg.exec() == QDialog.Accepted:
            self.refresh()
