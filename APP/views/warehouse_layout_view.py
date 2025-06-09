from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox, 
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt
from APP.views.emplacement_dialog import EmplacementDialog # To open on cell click

class WarehouseLayoutView(QWidget):
    def __init__(self, db, parent=None):
        print("DEBUG: WarehouseLayoutView.__init__() STARTED")
        super().__init__(parent)
        self.db = db
        self.setWindowTitle(self.tr("Warehouse Layout"))
        self.resize(700, 500) # Explicitly set a default size
        self.setStyleSheet("background-color: #f0f0f0;") # Set a solid background color
        print("DEBUG: WarehouseLayoutView resized to 700x500 and background set")

        self.current_warehouse_id = None
        self.current_warehouse_data = {} # To store max_aisles, max_shelves, max_levels
        self.all_warehouse_emplacements = {} # {aisle_num: {(shelf, level): emplacement_data}}

        main_layout = QVBoxLayout(self)

        # --- Warehouse and Aisle Selection --- 
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
        self.aisle_grids_layout = QVBoxLayout(self.aisle_grids_container) # Layout for the container
        self.scroll_area.setWidget(self.aisle_grids_container)
        main_layout.addWidget(self.scroll_area)

        # --- Connections --- 
        self.warehouse_combo.currentIndexChanged.connect(self._on_warehouse_selected)
        # self.layout_grid.cellClicked.connect(self._on_grid_cell_clicked) # Will be connected per-grid later

        self._load_warehouses()
        print("DEBUG: WarehouseLayoutView.__init__() COMPLETED")

    def _load_warehouses(self):
        """Loads warehouses into the combo box."""
        print("DEBUG: WarehouseLayoutView._load_warehouses() CALLED")
        self.warehouse_combo.clear()
        try:
            # Assuming inventory_warehouses has id, nom, max_aisles, max_shelves, max_levels
            sql = "SELECT id, nom, max_aisles, max_shelves, max_levels FROM inventory_warehouses WHERE actif = TRUE ORDER BY nom"
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

            for wh_id, nom, max_a, max_s, max_l in warehouses: # warehouses is now a list of tuples
                self.warehouse_combo.addItem(nom, userData={
                    'id': wh_id, 
                    'max_aisles': max_a or 1, # Default to 1 if NULL 
                    'max_shelves': max_s or 1, 
                    'max_levels': max_l or 1
                })
            
            if self.warehouse_combo.count() > 0:
                # Try to select 'STOCK' warehouse by default if it exists
                stock_index = self.warehouse_combo.findText("STOCK")
                if stock_index != -1:
                    self.warehouse_combo.setCurrentIndex(stock_index)
                else:
                    self.warehouse_combo.setCurrentIndex(0) # Select first one if STOCK not found
            else:
                # Handle case with no warehouses (disable selectors, clear grid)
                self.aisle_selector.setEnabled(False) # This line will be removed by previous/next edit for aisle_selector
                # self.layout_grid.clear() # Grid clearing will be handled differently
                # self.layout_grid.setRowCount(0)
                # self.layout_grid.setColumnCount(0)
                self.all_warehouse_emplacements.clear()
                self._clear_aisle_grids_display() # Placeholder for a method to clear UI

        except Exception as e:
            print(f"DEBUG: EXCEPTION in WarehouseLayoutView._load_warehouses(): {e}")
            # Optionally show a QMessageBox to the user

    def _clear_aisle_grids_display(self):
        """Clears all dynamically generated aisle grids from the UI."""
        # Implementation will involve iterating over self.aisle_grids_layout and removing widgets
        while self.aisle_grids_layout.count():
            child = self.aisle_grids_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        print("DEBUG: _clear_aisle_grids_display() - Cleared aisle grids display")

    def _on_warehouse_selected(self, index):
        """Handles warehouse selection change."""
        if index < 0: # No item selected or combo is empty
            self.current_warehouse_id = None
            self.current_warehouse_data = {}
            # self.aisle_selector.setEnabled(False) # Removed
            # self.aisle_selector.setValue(1) # Removed
            self.all_warehouse_emplacements.clear()
            self._clear_aisle_grids_display()
            return

        self.current_warehouse_data = self.warehouse_combo.itemData(index)
        self.current_warehouse_id = self.current_warehouse_data['id']
        
        # self.aisle_selector.setEnabled(True) # Removed
        # self.aisle_selector.setMaximum(self.current_warehouse_data.get('max_aisles', 1)) # Removed
        
        print(f"DEBUG: _on_warehouse_selected - Warehouse '{self.current_warehouse_data.get('nom')}' selected.")
        self._fetch_all_emplacements_for_warehouse()
        self._render_all_aisle_grids() # New method to create/update all aisle grids



    def _fetch_all_emplacements_for_warehouse(self):
        """Fetches all emplacements for all aisles of the current warehouse."""
        self.all_warehouse_emplacements = {}
        if not self.current_warehouse_id or not self.db or not self.current_warehouse_data:
            print("DEBUG: _fetch_all_emplacements_for_warehouse - Missing warehouse ID, DB, or data.")
            return

        max_aisles_to_fetch = self.current_warehouse_data.get('max_aisles', 0)
        if not isinstance(max_aisles_to_fetch, int) or max_aisles_to_fetch <= 0:
            print(f"DEBUG: _fetch_all_emplacements_for_warehouse - Invalid or zero max_aisles: {max_aisles_to_fetch}. Skipping fetch.")
            return
            
        print(f"DEBUG: _fetch_all_emplacements_for_warehouse - Warehouse ID: {self.current_warehouse_id}, Max Aisles: {max_aisles_to_fetch}")

        for aisle_number in range(1, max_aisles_to_fetch + 1):
            try:
                sql = """
                    SELECT id, nom, etagere, niveau 
                    FROM emplacement 
                    WHERE magasin_id = %s AND allee = %s
                """
                # Ensure aisle_number is passed as a string
                print(f"DEBUG: _fetch_all_emplacements_for_warehouse - Querying for Aisle: {str(aisle_number)}")
                emplacements_data = self.db.execute(sql, (self.current_warehouse_id, str(aisle_number)))
                
                emplacements_tuples = [] # Using a different name to avoid confusion
                if emplacements_data:
                    for emp_dict in emplacements_data:
                        emplacements_tuples.append((
                            emp_dict['id'], 
                            emp_dict['nom'], 
                            emp_dict.get('etagere'), 
                            emp_dict.get('niveau')
                        ))

                current_aisle_emplacements_dict = {} # Using a different name
                if not emplacements_tuples:
                    # print(f"DEBUG: _fetch_all_emplacements_for_warehouse - No emplacements found for aisle {aisle_number}.")
                    pass # Continue to next aisle if this one is empty

                for emp_id, nom, shelf_str, level_str in emplacements_tuples:
                    try:
                        shelf_int = int(shelf_str) if shelf_str is not None and str(shelf_str).strip() != '' else None
                        level_int = int(level_str) if level_str is not None and str(level_str).strip() != '' else None
                        
                        if shelf_int is not None and level_int is not None:
                            current_aisle_emplacements_dict[(shelf_int, level_int)] = {'id': emp_id, 'nom': nom}
                        # else:
                            # print(f"DEBUG: Skipped {nom} in aisle {aisle_number} due to None shelf/level_int ({shelf_str}, {level_str})")
                    except ValueError:
                        print(f"DEBUG: ValueError converting shelf/level for {nom} in aisle {aisle_number} (shelf='{shelf_str}', level='{level_str}')")
                
                if current_aisle_emplacements_dict:
                    self.all_warehouse_emplacements[aisle_number] = current_aisle_emplacements_dict
            
            except Exception as e:
                print(f"ERROR in _fetch_all_emplacements_for_warehouse processing aisle {aisle_number}: {e}")
                # Optionally, re-raise or handle more gracefully. For now, just logs and continues.

        print(f"DEBUG: _fetch_all_emplacements_for_warehouse - COMPLETED. Found emplacements for {len(self.all_warehouse_emplacements)} aisles.")

    def _on_grid_cell_clicked(self, row, column):
        print(f"DEBUG: Cell clicked at row {row}, column {column}")
        clicked_grid = self.sender()
        if not isinstance(clicked_grid, QTableWidget):
            print("ERROR: _on_grid_cell_clicked - Sender is not a QTableWidget.")
            return
        item = clicked_grid.item(row, column)
        if item:
            emplacement_info = item.data(Qt.ItemDataRole.UserRole)
            if emplacement_info and isinstance(emplacement_info, dict) and 'id' in emplacement_info:
                emplacement_id = emplacement_info['id']
                emplacement_nom = emplacement_info.get('nom', 'N/A')
                print(f"DEBUG: Clicked on emplacement: ID={emplacement_id}, Name='{emplacement_nom}'")
                
                # Instantiate EmplacementDialog
                dialog = EmplacementDialog(db=self.db, parent=self)
                # Load the specific emplacement data
                if hasattr(dialog, 'load_emplacement_complet'):
                    dialog.load_emplacement_complet(emplacement_id)
                    dialog.exec()  # Use exec() for a modal dialog
                else:
                    # Fallback or error if method doesn't exist, though search confirms it does
                    QMessageBox.critical(self, "Error", "EmplacementDialog is missing 'load_emplacement_complet' method.")
                    print("ERROR: EmplacementDialog does not have 'load_emplacement_complet' method.")
            else:
                print(f"DEBUG: Clicked cell has no valid emplacement data. Text: '{item.text()}'")
        else:
            print("DEBUG: Clicked on an empty cell item (should not happen if grid is populated).")

    def _render_all_aisle_grids(self):
        """Clears and recreates all aisle grids in the scrollable area."""
        self._clear_aisle_grids_display()
        print(f"DEBUG: _render_all_aisle_grids - Rendering for warehouse ID: {self.current_warehouse_id}")

        if not self.current_warehouse_id or not self.current_warehouse_data:
            print("DEBUG: _render_all_aisle_grids - No current warehouse selected or no data.")
            return

        max_aisles_to_display = min(self.current_warehouse_data.get('max_aisles', 0), 10) # Display up to 10 aisles
        max_shelves = self.current_warehouse_data.get('max_shelves', 1)
        max_levels = self.current_warehouse_data.get('max_levels', 1)

        if max_aisles_to_display == 0:
            print("DEBUG: _render_all_aisle_grids - Max aisles to display is 0.")
            # Optionally, display a message in the UI like "No aisles to display for this warehouse."
            no_aisles_label = QLabel(self.tr("This warehouse has no aisles configured or max_aisles is 0."))
            self.aisle_grids_layout.addWidget(no_aisles_label)
            return

        for aisle_num in range(1, max_aisles_to_display + 1):
            aisle_label_text = self.tr("Aisle {0}").format(aisle_num)
            aisle_label = QLabel(f"<b>{aisle_label_text}</b>") # Bold label
            self.aisle_grids_layout.addWidget(aisle_label)

            grid_table = QTableWidget()
            grid_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            grid_table.setSelectionBehavior(QAbstractItemView.SelectItems)
            grid_table.setSelectionMode(QAbstractItemView.SingleSelection)
            grid_table.setObjectName(f"aisle_grid_{aisle_num}") # For potential specific styling or identification
            
            # Store aisle number on the table for context if needed in cellClicked
            grid_table.setProperty("aisle_number", aisle_num) 

            self.aisle_grids_layout.addWidget(grid_table)
            grid_table.cellClicked.connect(self._on_grid_cell_clicked) # Connect signal

            # Populate this specific grid_table
            current_aisle_emplacements = self.all_warehouse_emplacements.get(aisle_num, {})
            # print(f"DEBUG: _render_all_aisle_grids - Populating grid for Aisle {aisle_num} with {len(current_aisle_emplacements)} emplacements.")

            grid_table.setRowCount(max_levels)
            grid_table.setColumnCount(max_shelves)

            # Set headers (Levels for rows, Shelves for columns)
            v_headers = [self.tr("L{0}").format(i+1) for i in range(max_levels)]
            h_headers = [self.tr("S{0}").format(i+1) for i in range(max_shelves)]
            grid_table.setVerticalHeaderLabels(v_headers)
            grid_table.setHorizontalHeaderLabels(h_headers)

            for r in range(max_levels):
                level_num = r + 1
                for c in range(max_shelves):
                    shelf_num = c + 1
                    emplacement_data = current_aisle_emplacements.get((shelf_num, level_num))
                    
                    item_text = f"A{aisle_num}S{shelf_num}L{level_num}" # Default text
                    item_data_to_store = {
                        'id': None, # Placeholder, will be filled if emplacement exists
                        'nom': item_text, 
                        'aisle': aisle_num, 
                        'shelf': shelf_num, 
                        'level': level_num,
                        'is_placeholder': True
                    }

                    if emplacement_data:
                        item_text = emplacement_data.get('nom', item_text)
                        item_data_to_store['id'] = emplacement_data.get('id')
                        item_data_to_store['nom'] = item_text # Update nom if found
                        item_data_to_store['is_placeholder'] = False
                    
                    table_item = QTableWidgetItem(item_text)
                    table_item.setData(Qt.ItemDataRole.UserRole, item_data_to_store)
                    table_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if not item_data_to_store['is_placeholder']:
                        table_item.setBackground(Qt.GlobalColor.cyan) # Highlight existing emplacements
                    else:
                        table_item.setForeground(Qt.GlobalColor.gray) # Gray out placeholder text

                    grid_table.setItem(r, c, table_item)
            
            grid_table.resizeColumnsToContents()
            grid_table.resizeRowsToContents()
            # Adjust size of the table to fit contents, or set fixed size
            # For dynamic height based on rows:
            total_row_height = grid_table.horizontalHeader().height() + 2 # +2 for border/margin
            for i in range(grid_table.rowCount()):
                total_row_height += grid_table.rowHeight(i)
            grid_table.setMinimumHeight(total_row_height)
            grid_table.setMaximumHeight(total_row_height) # Fix height to content

        print(f"DEBUG: _render_all_aisle_grids - COMPLETED for warehouse {self.current_warehouse_id}")

        grid_table.setRowCount(max_levels)
        grid_table.setColumnCount(max_shelves)

        # Set headers (Levels for rows, Shelves for columns)
        v_headers = [self.tr("L{0}").format(i+1) for i in range(max_levels)]
        h_headers = [self.tr("S{0}").format(i+1) for i in range(max_shelves)]
        grid_table.setVerticalHeaderLabels(v_headers)
        grid_table.setHorizontalHeaderLabels(h_headers)

        for r in range(max_levels):
            level_num = r + 1
            for c in range(max_shelves):
                shelf_num = c + 1
                emplacement_data = current_aisle_emplacements.get((shelf_num, level_num))
                
                item_text = f"A{aisle_num}S{shelf_num}L{level_num}" # Default text
                item_data_to_store = {
                    'id': None, # Placeholder, will be filled if emplacement exists
                    'nom': item_text, 
                    'aisle': aisle_num, 
                    'shelf': shelf_num, 
                    'level': level_num,
                    'is_placeholder': True
                }

                if emplacement_data:
                    item_text = emplacement_data.get('nom', item_text)
                    item_data_to_store['id'] = emplacement_data.get('id')
                    item_data_to_store['nom'] = item_text # Update nom if found
                    item_data_to_store['is_placeholder'] = False
                
                table_item = QTableWidgetItem(item_text)
                table_item.setData(Qt.ItemDataRole.UserRole, item_data_to_store)
                table_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if not item_data_to_store['is_placeholder']:
                    table_item.setBackground(Qt.GlobalColor.cyan) # Highlight existing emplacements
            return
        
        emplacement_id_to_load = emplacement_info.get('id')

        if emplacement_id_to_load:
            # Open EmplacementDialog with this ID
            dialog = EmplacementDialog(parent=self, db=self.db) # Pass db connection
            # The EmplacementDialog needs a method to load by ID. 
            # From memory, it uses get_emplacement_complet in load_stock_data, 
            # and set_data is called by load_emplacement_complet.
            # We need to ensure EmplacementDialog has a public method to trigger this load.
            # Let's assume there's a method like `load_and_display_emplacement(emp_id)`
            # For now, we can try to use its existing structure if set_data can be called directly after setting id
            
            # A more robust way would be to have a specific loading method in EmplacementDialog
            # e.g. dialog.load_emplacement_by_id(emplacement_id_to_load)
            # For now, let's assume we need to fetch the full data and pass it to set_data
            try:
                # Simplification: The EmplacementDialog's `load_emplacement_complet` method seems to be what we need.
                # It calls `set_data` internally. So we can call that.
                # This method, if it exists and works as expected, should handle its own data fetching using its services.
                if hasattr(dialog, 'load_emplacement_complet'):
                    dialog.load_emplacement_complet(emplacement_id_to_load)
                    dialog.exec()
                else:
                    print(f"EmplacementDialog does not have load_emplacement_complet method.")
                    # Fallback or error message

            except Exception as e:
                print(f"Error preparing or showing EmplacementDialog: {e}")
        else:
            # Cell represents a potential emplacement that doesn't exist in DB yet.
            # For now, do nothing. Could later implement creation.
            print(f"Clicked on potential emplacement: A{emplacement_info['aisle']}S{emplacement_info['shelf']}L{emplacement_info['level']}. Not in DB.")

if __name__ == '__main__':
    # This is for testing the widget independently
    import sys
    from PySide6.QtWidgets import QApplication
    # Mock DB connection for standalone testing
    class MockDB:
        def cursor(self, dictionary=False):
            return MockCursor(dictionary)
        def close(self):
            print("MockDB closed")

    class MockCursor:
        def __init__(self, dictionary=False):
            self.dictionary = dictionary
            self.rowcount = 0
        def execute(self, sql, params=None):
            print(f"Executing SQL: {sql} with params: {params}")
            if "FROM inventory_warehouses" in sql:
                self._data = [
                    (1, 'STOCK', 10, 5, 4),
                    (2, 'RECEPTION', 3, 3, 2)
                ]
            elif "FROM emplacement" in sql and params:
                # Simulate emplacements for STOCK, Aisle 1
                if params[0] == 1 and params[1] == 1: # warehouse_id=1 (STOCK), aisle=1
                    self._data = [
                        (101, 'A1S1L1', 1, 1),
                        (102, 'A1S1L2', 1, 2),
                        (105, 'A1S2L1', 2, 1),
                    ]
                else:
                    self._data = [] # No emplacements for other aisles in mock
            else:
                self._data = []
            self.rowcount = len(self._data)
        def fetchall(self):
            return self._data
        def fetchone(self):
            return self._data[0] if self._data else None
        def close(self):
            pass

    app = QApplication(sys.argv)
    db_conn = MockDB()
    view = WarehouseLayoutView(db=db_conn)
    view.resize(800, 600)
    view.show()
    sys.exit(app.exec())
