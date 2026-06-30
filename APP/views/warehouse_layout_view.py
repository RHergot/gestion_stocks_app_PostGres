"""Vue graphique de l'entrepôt — double mode : Layout (grille) + Inventaire (détaillé).

Mode Layout : grille Aisle×Shelf×Level avec cellules cliquables → édition.
Mode Inventaire : sélection warehouse + allée → tableau des pièces par emplacement
  (pièce, quantité, machine, fournisseur) — vue magasinier pratique.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QScrollArea, QTabWidget, QPushButton
)
from PySide6.QtCore import Qt
from APP.views.emplacement_dialog import EmplacementDialog
import logging

logger = logging.getLogger(__name__)


class WarehouseLayoutView(QWidget):
    """Vue entrepôt avec deux onglets : Layout et Inventaire."""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle(self.tr("Warehouse"))
        self.resize(900, 650)

        self.current_warehouse_id = None
        self.current_warehouse_data = {}

        main_layout = QVBoxLayout(self)

        # --- Warehouse + Aisle Selection (shared) ---
        sel_layout = QHBoxLayout()
        sel_layout.addWidget(QLabel(self.tr("Warehouse:")))
        self.warehouse_combo = QComboBox()
        self.warehouse_combo.setMinimumWidth(150)
        sel_layout.addWidget(self.warehouse_combo)

        sel_layout.addWidget(QLabel(self.tr("Aisle:")))
        self.aisle_combo = QComboBox()
        self.aisle_combo.setMinimumWidth(80)
        self.aisle_combo.addItem(self.tr("All"), 0)  # 0 = all aisles
        sel_layout.addWidget(self.aisle_combo)

        self.refresh_btn = QPushButton(self.tr("Refresh"))
        sel_layout.addWidget(self.refresh_btn)
        sel_layout.addStretch()
        main_layout.addLayout(sel_layout)

        # --- Tab Widget ---
        self.tabs = QTabWidget()
        self._setup_layout_tab()
        self._setup_inventory_tab()
        main_layout.addWidget(self.tabs)

        # --- Connections ---
        self.warehouse_combo.currentIndexChanged.connect(self._on_warehouse_changed)
        self.aisle_combo.currentIndexChanged.connect(self._on_aisle_changed)
        self.refresh_btn.clicked.connect(self._refresh_current_tab)

        self._load_warehouses()

    # =========================================================================
    # Onglet 1 : Layout (grille visuelle)
    # =========================================================================

    def _setup_layout_tab(self):
        self.layout_tab = QWidget()
        layout = QVBoxLayout(self.layout_tab)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.aisle_grids_container = QWidget()
        self.aisle_grids_layout = QVBoxLayout(self.aisle_grids_container)
        self.scroll_area.setWidget(self.aisle_grids_container)
        layout.addWidget(self.scroll_area)
        self.tabs.addTab(self.layout_tab, self.tr("Layout"))

    # =========================================================================
    # Onglet 2 : Inventaire (tableau détaillé par allée)
    # =========================================================================

    def _setup_inventory_tab(self):
        self.inventory_tab = QWidget()
        layout = QVBoxLayout(self.inventory_tab)
        self.inventory_table = QTableWidget()
        self.inventory_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.inventory_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.inventory_table.setAlternatingRowColors(True)
        layout.addWidget(self.inventory_table)
        self.tabs.addTab(self.inventory_tab, self.tr("Inventory"))

    # =========================================================================
    # Chargement des données
    # =========================================================================

    def _load_warehouses(self):
        self.warehouse_combo.blockSignals(True)
        self.warehouse_combo.clear()
        try:
            sql = (
                "SELECT id, nom, max_aisles, max_shelves, max_levels "
                "FROM inventory_warehouses WHERE actif = TRUE ORDER BY nom"
            )
            rows = self.db.execute(sql)
            if rows:
                for wh in rows:
                    self.warehouse_combo.addItem(wh['nom'], userData={
                        'id': wh['id'],
                        'max_aisles': wh.get('max_aisles') or 1,
                        'max_shelves': wh.get('max_shelves') or 1,
                        'max_levels': wh.get('max_levels') or 1,
                    })
                stock_idx = self.warehouse_combo.findText("STOCK")
                self.warehouse_combo.setCurrentIndex(stock_idx if stock_idx >= 0 else 0)
        except Exception as e:
            logger.error("Failed to load warehouses: %s", e)
        self.warehouse_combo.blockSignals(False)

    def _update_aisle_combo(self):
        self.aisle_combo.blockSignals(True)
        self.aisle_combo.clear()
        self.aisle_combo.addItem(self.tr("All"), 0)
        if self.current_warehouse_data:
            max_a = self.current_warehouse_data.get('max_aisles', 0)
            for a in range(1, min(max_a, 20) + 1):
                self.aisle_combo.addItem(self.tr("Aisle {0}").format(a), a)
        self.aisle_combo.blockSignals(False)

    # =========================================================================
    # Événements
    # =========================================================================

    def _on_warehouse_changed(self, index):
        if index < 0:
            self.current_warehouse_id = None
            self.current_warehouse_data = {}
            self._clear_layout_grids()
            self.inventory_table.setRowCount(0)
            return
        self.current_warehouse_data = self.warehouse_combo.itemData(index)
        self.current_warehouse_id = self.current_warehouse_data['id']
        self._update_aisle_combo()
        self._refresh_current_tab()

    def _on_aisle_changed(self, _index):
        self._refresh_current_tab()

    def _refresh_current_tab(self):
        if self.tabs.currentIndex() == 0:
            self._refresh_layout()
        else:
            self._refresh_inventory()

    # =========================================================================
    # Layout : grille Aisle×Shelf×Level
    # =========================================================================

    def _clear_layout_grids(self):
        while self.aisle_grids_layout.count():
            child = self.aisle_grids_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _refresh_layout(self):
        self._clear_layout_grids()
        if not self.current_warehouse_id or not self.current_warehouse_data:
            return

        max_aisles = min(self.current_warehouse_data.get('max_aisles', 0), 10)
        max_shelves = self.current_warehouse_data.get('max_shelves', 1)
        max_levels = self.current_warehouse_data.get('max_levels', 1)

        aisle_filter = self.aisle_combo.currentData()
        aisles_to_show = [aisle_filter] if aisle_filter else range(1, max_aisles + 1)

        if not aisles_to_show or (isinstance(aisles_to_show, range) and max_aisles == 0):
            label = QLabel(self.tr("No aisles configured."))
            self.aisle_grids_layout.addWidget(label)
            return

        for aisle_num in aisles_to_show:
            if isinstance(aisles_to_show, range) and aisle_num > max_aisles:
                continue

            emplacements = self._fetch_emplacements(aisle_num)
            label = QLabel(f"<b>{self.tr('Aisle {0}').format(aisle_num)}</b>")
            self.aisle_grids_layout.addWidget(label)

            grid = QTableWidget()
            grid.setEditTriggers(QAbstractItemView.NoEditTriggers)
            grid.setProperty("aisle_number", aisle_num)
            self.aisle_grids_layout.addWidget(grid)
            grid.cellClicked.connect(self._on_grid_cell_clicked)

            grid.setRowCount(max_levels)
            grid.setColumnCount(max_shelves)
            v_headers = [self.tr("L{0}").format(i + 1) for i in range(max_levels)]
            h_headers = [self.tr("S{0}").format(i + 1) for i in range(max_shelves)]
            grid.setVerticalHeaderLabels(v_headers)
            grid.setHorizontalHeaderLabels(h_headers)

            for r in range(max_levels):
                for c in range(max_shelves):
                    key = (c + 1, r + 1)
                    emp = emplacements.get(key)
                    text = emp['nom'] if emp else f"A{aisle_num}S{c+1}L{r+1}"
                    item = QTableWidgetItem(text)
                    item.setData(Qt.ItemDataRole.UserRole, {
                        'id': emp['id'] if emp else None,
                        'nom': text,
                        'aisle': aisle_num, 'shelf': c + 1, 'level': r + 1,
                        'is_placeholder': emp is None
                    })
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if emp:
                        item.setBackground(Qt.GlobalColor.cyan)
                    else:
                        item.setForeground(Qt.GlobalColor.gray)
                    grid.setItem(r, c, item)

            grid.resizeColumnsToContents()
            total_h = grid.horizontalHeader().height() + 2
            for i in range(grid.rowCount()):
                total_h += grid.rowHeight(i)
            grid.setMinimumHeight(total_h)
            grid.setMaximumHeight(total_h)

    def _fetch_emplacements(self, aisle_num):
        """Retourne {(shelf, level): {id, nom}} pour une allée."""
        result = {}
        try:
            sql = "SELECT id, nom, etagere, niveau FROM emplacement WHERE magasin_id = %s AND allee = %s"
            rows = self.db.execute(sql, (self.current_warehouse_id, str(aisle_num)))
            if rows:
                for e in rows:
                    try:
                        shelf = int(e['etagere']) if str(e.get('etagere', '')).strip() else None
                        level = int(e['niveau']) if str(e.get('niveau', '')).strip() else None
                        if shelf is not None and level is not None:
                            result[(shelf, level)] = {'id': e['id'], 'nom': e['nom']}
                    except (ValueError, TypeError):
                        pass
        except Exception as e:
            logger.error("Error fetching emplacements aisle %s: %s", aisle_num, e)
        return result

    def _on_grid_cell_clicked(self, row, column):
        grid = self.sender()
        if not isinstance(grid, QTableWidget):
            return
        item = grid.item(row, column)
        if item:
            info = item.data(Qt.ItemDataRole.UserRole)
            if info and isinstance(info, dict) and info.get('id'):
                dialog = EmplacementDialog(db=self.db, parent=self)
                if hasattr(dialog, 'load_emplacement_complet'):
                    dialog.load_emplacement_complet(info['id'])
                    dialog.exec()

    # =========================================================================
    # Inventaire : tableau détaillé par allée (vue magasinier)
    # =========================================================================

    def _refresh_inventory(self):
        self.inventory_table.clear()
        if not self.current_warehouse_id:
            self.inventory_table.setRowCount(0)
            return

        aisle_filter = self.aisle_combo.currentData()
        if not aisle_filter:
            # "All" selected — show summary per aisle
            self._refresh_inventory_summary()
            return

        # Detailed view for one aisle
        headers = [
            self.tr("Shelf"), self.tr("Level"), self.tr("Location"),
            self.tr("Part"), self.tr("Reference"), self.tr("Qty"),
            self.tr("Machine"), self.tr("Supplier")
        ]
        self.inventory_table.setColumnCount(len(headers))
        self.inventory_table.setHorizontalHeaderLabels(headers)
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        sql = (
            "SELECT e.id, e.etagere, e.niveau, e.nom AS loc_name, "
            "p.nom AS piece_nom, p.reference, "
            "COALESCE(es.quantite, 0) AS quantite, "
            "m.nom AS machine_nom, f.nom AS fournisseur_nom "
            "FROM emplacement e "
            "LEFT JOIN emplacement_stock es ON es.emplacement_id = e.id "
            "LEFT JOIN piece p ON es.piece_id = p.id_piece "
            "LEFT JOIN piece_extension pe ON e.id = pe.emplacement_id AND p.id_piece = pe.id_piece "
            "LEFT JOIN machine m ON pe.machine_id = m.id_machine "
            "LEFT JOIN fournisseur f ON p.fournisseur_pref_id = f.id_fournisseur "
            "WHERE e.magasin_id = %s AND e.allee = %s "
            "ORDER BY e.etagere::int, e.niveau::int"
        )
        try:
            rows = self.db.execute(sql, (self.current_warehouse_id, str(aisle_filter)))
        except Exception as e:
            logger.error("Inventory query failed: %s", e)
            rows = []

        if not rows:
            self.inventory_table.setRowCount(0)
            return

        self.inventory_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            shelf = str(r.get('etagere', ''))
            level = str(r.get('niveau', ''))
            loc = str(r.get('loc_name', ''))
            piece = str(r.get('piece_nom') or '—')
            ref = str(r.get('reference') or '—')
            qty = str(r.get('quantite', 0))
            machine = str(r.get('machine_nom') or '—')
            supplier = str(r.get('fournisseur_nom') or '—')

            for col, val in enumerate([shelf, level, loc, piece, ref, qty, machine, supplier]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                # Colorer les emplacements vides
                if piece == '—' and col == 3:
                    item.setForeground(Qt.GlobalColor.gray)
                self.inventory_table.setItem(i, col, item)

    def _refresh_inventory_summary(self):
        """Vue résumée : une ligne par emplacement occupé, toutes allées."""
        headers = [
            self.tr("Aisle"), self.tr("Shelf"), self.tr("Level"), self.tr("Location"),
            self.tr("Part"), self.tr("Reference"), self.tr("Qty"),
            self.tr("Machine"), self.tr("Supplier")
        ]
        self.inventory_table.setColumnCount(len(headers))
        self.inventory_table.setHorizontalHeaderLabels(headers)
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        sql = (
            "SELECT e.allee, e.etagere, e.niveau, e.nom AS loc_name, "
            "p.nom AS piece_nom, p.reference, "
            "COALESCE(es.quantite, 0) AS quantite, "
            "m.nom AS machine_nom, f.nom AS fournisseur_nom "
            "FROM emplacement e "
            "JOIN emplacement_stock es ON es.emplacement_id = e.id "
            "JOIN piece p ON es.piece_id = p.id_piece "
            "LEFT JOIN piece_extension pe ON e.id = pe.emplacement_id AND p.id_piece = pe.id_piece "
            "LEFT JOIN machine m ON pe.machine_id = m.id_machine "
            "LEFT JOIN fournisseur f ON p.fournisseur_pref_id = f.id_fournisseur "
            "WHERE e.magasin_id = %s "
            "ORDER BY e.allee::int, e.etagere::int, e.niveau::int"
        )
        try:
            rows = self.db.execute(sql, (self.current_warehouse_id,))
        except Exception as e:
            logger.error("Inventory summary query failed: %s", e)
            rows = []

        self.inventory_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            aisle = str(r.get('allee', ''))
            shelf = str(r.get('etagere', ''))
            level = str(r.get('niveau', ''))
            loc = str(r.get('loc_name', ''))
            piece = str(r.get('piece_nom') or '—')
            ref = str(r.get('reference') or '—')
            qty = str(r.get('quantite', 0))
            machine = str(r.get('machine_nom') or '—')
            supplier = str(r.get('fournisseur_nom') or '—')

            for col, val in enumerate([aisle, shelf, level, loc, piece, ref, qty, machine, supplier]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.inventory_table.setItem(i, col, item)
