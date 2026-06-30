"""Vue graphique de l'entrepôt — grille visuelle Aisle × Shelf × Level.

Accessible via le menu General > Warehouse Layout, ou depuis Locations > Grid View.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt
from APP.views.emplacement_dialog import EmplacementDialog
import logging

logger = logging.getLogger(__name__)


class WarehouseLayoutView(QWidget):
    """Vue graphique de l'entrepôt avec grilles par allée."""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle(self.tr("Warehouse Layout"))
        self.resize(700, 500)
        self.setStyleSheet("background-color: #f0f0f0;")

        self.current_warehouse_id = None
        self.current_warehouse_data = {}
        self.all_warehouse_emplacements = {}

        main_layout = QVBoxLayout(self)

        # --- Warehouse Selection ---
        selection_layout = QHBoxLayout()
        self.warehouse_label = QLabel(self.tr("Warehouse:"))
        selection_layout.addWidget(self.warehouse_label)
        self.warehouse_combo = QComboBox()
        selection_layout.addWidget(self.warehouse_combo)
        selection_layout.addStretch()
        main_layout.addLayout(selection_layout)

        # --- Layout Grids Container ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.aisle_grids_container = QWidget()
        self.aisle_grids_layout = QVBoxLayout(self.aisle_grids_container)
        self.scroll_area.setWidget(self.aisle_grids_container)
        main_layout.addWidget(self.scroll_area)

        # --- Connections ---
        self.warehouse_combo.currentIndexChanged.connect(self._on_warehouse_selected)

        self._load_warehouses()
        logger.debug("WarehouseLayoutView initialized")

    def _load_warehouses(self):
        """Charge les entrepôts dans la combobox."""
        self.warehouse_combo.clear()
        try:
            sql = (
                "SELECT id, nom, max_aisles, max_shelves, max_levels "
                "FROM inventory_warehouses WHERE actif = TRUE ORDER BY nom"
            )
            warehouses_data = self.db.execute(sql)
            warehouses = []
            if warehouses_data:
                for wh_dict in warehouses_data:
                    warehouses.append((
                        wh_dict['id'],
                        wh_dict['nom'],
                        wh_dict.get('max_aisles'),
                        wh_dict.get('max_shelves'),
                        wh_dict.get('max_levels')
                    ))

            for wh_id, nom, max_a, max_s, max_l in warehouses:
                self.warehouse_combo.addItem(nom, userData={
                    'id': wh_id,
                    'max_aisles': max_a or 1,
                    'max_shelves': max_s or 1,
                    'max_levels': max_l or 1
                })

            if self.warehouse_combo.count() > 0:
                stock_index = self.warehouse_combo.findText("STOCK")
                if stock_index != -1:
                    self.warehouse_combo.setCurrentIndex(stock_index)
                else:
                    self.warehouse_combo.setCurrentIndex(0)
            else:
                self.all_warehouse_emplacements.clear()
                self._clear_aisle_grids_display()

        except Exception as e:
            logger.error("Failed to load warehouses: %s", e)

    def _clear_aisle_grids_display(self):
        """Supprime toutes les grilles d'allées de l'UI."""
        while self.aisle_grids_layout.count():
            child = self.aisle_grids_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _on_warehouse_selected(self, index):
        """Gère le changement d'entrepôt sélectionné."""
        if index < 0:
            self.current_warehouse_id = None
            self.current_warehouse_data = {}
            self.all_warehouse_emplacements.clear()
            self._clear_aisle_grids_display()
            return

        self.current_warehouse_data = self.warehouse_combo.itemData(index)
        self.current_warehouse_id = self.current_warehouse_data['id']
        self._fetch_all_emplacements_for_warehouse()
        self._render_all_aisle_grids()

    def _fetch_all_emplacements_for_warehouse(self):
        """Récupère tous les emplacements pour toutes les allées."""
        self.all_warehouse_emplacements = {}
        if not self.current_warehouse_id or not self.db or not self.current_warehouse_data:
            return

        max_aisles = self.current_warehouse_data.get('max_aisles', 0)
        if not isinstance(max_aisles, int) or max_aisles <= 0:
            return

        for aisle_number in range(1, max_aisles + 1):
            try:
                sql = (
                    "SELECT id, nom, etagere, niveau "
                    "FROM emplacement "
                    "WHERE magasin_id = %s AND allee = %s"
                )
                emplacements_data = self.db.execute(sql, (self.current_warehouse_id, str(aisle_number)))

                aisle_emplacements = {}
                if emplacements_data:
                    for emp_dict in emplacements_data:
                        try:
                            shelf = int(emp_dict.get('etagere')) if emp_dict.get('etagere') not in (None, '') else None
                            level = int(emp_dict.get('niveau')) if emp_dict.get('niveau') not in (None, '') else None
                            if shelf is not None and level is not None:
                                aisle_emplacements[(shelf, level)] = {
                                    'id': emp_dict['id'],
                                    'nom': emp_dict['nom']
                                }
                        except (ValueError, TypeError):
                            pass

                if aisle_emplacements:
                    self.all_warehouse_emplacements[aisle_number] = aisle_emplacements

            except Exception as e:
                logger.error("Error fetching aisle %s: %s", aisle_number, e)

        logger.debug("Fetched emplacements for %s aisles", len(self.all_warehouse_emplacements))

    def _on_grid_cell_clicked(self, row, column):
        """Ouvre le dialogue d'édition au clic sur une cellule."""
        clicked_grid = self.sender()
        if not isinstance(clicked_grid, QTableWidget):
            return
        item = clicked_grid.item(row, column)
        if item:
            emplacement_info = item.data(Qt.ItemDataRole.UserRole)
            if emplacement_info and isinstance(emplacement_info, dict) and 'id' in emplacement_info:
                emplacement_id = emplacement_info['id']
                dialog = EmplacementDialog(db=self.db, parent=self)
                if hasattr(dialog, 'load_emplacement_complet'):
                    dialog.load_emplacement_complet(emplacement_id)
                    dialog.exec()
                else:
                    QMessageBox.critical(self, "Error",
                        "EmplacementDialog is missing 'load_emplacement_complet' method.")

    def _render_all_aisle_grids(self):
        """Recrée toutes les grilles d'allées dans la zone scrollable."""
        self._clear_aisle_grids_display()

        if not self.current_warehouse_id or not self.current_warehouse_data:
            return

        max_aisles = min(self.current_warehouse_data.get('max_aisles', 0), 10)
        max_shelves = self.current_warehouse_data.get('max_shelves', 1)
        max_levels = self.current_warehouse_data.get('max_levels', 1)

        if max_aisles == 0:
            no_aisles_label = QLabel(self.tr("This warehouse has no aisles configured."))
            self.aisle_grids_layout.addWidget(no_aisles_label)
            return

        for aisle_num in range(1, max_aisles + 1):
            aisle_label = QLabel(f"<b>{self.tr('Aisle {0}').format(aisle_num)}</b>")
            self.aisle_grids_layout.addWidget(aisle_label)

            grid_table = QTableWidget()
            grid_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            grid_table.setSelectionBehavior(QAbstractItemView.SelectItems)
            grid_table.setSelectionMode(QAbstractItemView.SingleSelection)
            grid_table.setProperty("aisle_number", aisle_num)
            self.aisle_grids_layout.addWidget(grid_table)
            grid_table.cellClicked.connect(self._on_grid_cell_clicked)

            current_emplacements = self.all_warehouse_emplacements.get(aisle_num, {})
            grid_table.setRowCount(max_levels)
            grid_table.setColumnCount(max_shelves)

            v_headers = [self.tr("L{0}").format(i + 1) for i in range(max_levels)]
            h_headers = [self.tr("S{0}").format(i + 1) for i in range(max_shelves)]
            grid_table.setVerticalHeaderLabels(v_headers)
            grid_table.setHorizontalHeaderLabels(h_headers)

            for r in range(max_levels):
                level_num = r + 1
                for c in range(max_shelves):
                    shelf_num = c + 1
                    emp = current_emplacements.get((shelf_num, level_num))

                    item_text = f"A{aisle_num}S{shelf_num}L{level_num}"
                    item_data = {
                        'id': emp['id'] if emp else None,
                        'nom': emp['nom'] if emp else item_text,
                        'aisle': aisle_num, 'shelf': shelf_num, 'level': level_num,
                        'is_placeholder': emp is None
                    }

                    table_item = QTableWidgetItem(item_data['nom'])
                    table_item.setData(Qt.ItemDataRole.UserRole, item_data)
                    table_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if emp:
                        table_item.setBackground(Qt.GlobalColor.cyan)
                    else:
                        table_item.setForeground(Qt.GlobalColor.gray)

                    grid_table.setItem(r, c, table_item)

            grid_table.resizeColumnsToContents()
            grid_table.resizeRowsToContents()
            total_height = grid_table.horizontalHeader().height() + 2
            for i in range(grid_table.rowCount()):
                total_height += grid_table.rowHeight(i)
            grid_table.setMinimumHeight(total_height)
            grid_table.setMaximumHeight(total_height)
