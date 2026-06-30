from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QHBoxLayout, QSpinBox, QDoubleSpinBox, QMessageBox, QComboBox, QLabel
import logging

logger = logging.getLogger(__name__)

class PieceDialog(QDialog):
    def __init__(self, parent=None, db=None, warehouses=None, fournisseurs=None, unites=None, categories=None, emplacements=None, statuts=None, machines=None):
        super().__init__(parent)
        self.db = db # Store db connection
        self.warehouses = warehouses or []
        self.all_emplacements = emplacements or [] # Store all emplacements for filtering

        self.setWindowTitle(self.tr("Part"))
        layout = QFormLayout(self)

        self.reference = QLineEdit(self)
        self.nom = QLineEdit(self)

        self.fournisseur_pref_id = QComboBox(self)
        if fournisseurs:
            for f in fournisseurs:
                self.fournisseur_pref_id.addItem(f["nom"], f["id_fournisseur"])

        self.prix_unitaire = QDoubleSpinBox(self)
        self.prix_unitaire.setMinimum(0)
        self.prix_unitaire.setMaximum(1_000_000)
        self.prix_unitaire.setDecimals(2)

        self.stock_alerte = QSpinBox(self)
        self.stock_alerte.setMinimum(0)
        self.stock_alerte.setMaximum(1_000_000)

        self.stock_actuel = QSpinBox(self)
        self.stock_actuel.setMinimum(0)
        self.stock_actuel.setMaximum(1_000_000)

        self.stock_reserve = QSpinBox(self)
        self.stock_reserve.setMinimum(0)
        self.stock_reserve.setMaximum(1_000_000)

        self.unite = QComboBox(self)
        if unites:
            for u in unites:
                self.unite.addItem(u["nom"], u["id"])

        self.categorie = QComboBox(self)
        if categories:
            for c in categories:
                self.categorie.addItem(c["nom"], c["id"])

        # --- New Emplacement Selection UI --- 
        self.emplacement_group_label = QLabel(self.tr("Specify Emplacement:"))
        layout.addRow(self.emplacement_group_label)

        self.warehouse_selector = QComboBox(self)
        if self.warehouses:
            for wh in self.warehouses:
                self.warehouse_selector.addItem(wh.get("nom", f"Warehouse {wh['id']}"), wh["id"])
        layout.addRow(self.tr("Warehouse"), self.warehouse_selector)

        self.aisle_input = QSpinBox(self)
        self.aisle_input.setRange(1, 999)
        self.shelf_input = QSpinBox(self)
        self.shelf_input.setRange(1, 999)
        self.level_input = QSpinBox(self)
        self.level_input.setRange(1, 999)

        h_layout_emplacement_inputs = QHBoxLayout()
        h_layout_emplacement_inputs.addWidget(QLabel(self.tr("Aisle:")))
        h_layout_emplacement_inputs.addWidget(self.aisle_input)
        h_layout_emplacement_inputs.addWidget(QLabel(self.tr("Shelf:")))
        h_layout_emplacement_inputs.addWidget(self.shelf_input)
        h_layout_emplacement_inputs.addWidget(QLabel(self.tr("Level:")))
        h_layout_emplacement_inputs.addWidget(self.level_input)
        layout.addRow(h_layout_emplacement_inputs)
        
        self.resolve_emplacement_btn = QPushButton(self.tr("Find/Set Emplacement"), self)
        layout.addRow(self.resolve_emplacement_btn)
        # --- End New Emplacement Selection UI ---

        self.emplacement_stockage = QComboBox(self) # This will be populated dynamically or used as confirmation
        self.emplacement_stockage.setPlaceholderText(self.tr("Select or find emplacement above"))
        # Initial population is removed; it's now dynamic or via Find/Set button

        self.statut = QComboBox(self)
        if statuts:
            for s in statuts:
                self.statut.addItem(s["nom"], s["id"])

        self.machine = QComboBox(self)
        if machines:
            for m in machines:
                self.machine.addItem(m["nom"], m["id_machine"])

        layout.addRow(self.tr("Reference"), self.reference)
        layout.addRow(self.tr("Name"), self.nom)
        layout.addRow(self.tr("Preferred Supplier"), self.fournisseur_pref_id)
        layout.addRow(self.tr("Unit Price"), self.prix_unitaire)
        layout.addRow(self.tr("Alert Stock"), self.stock_alerte)
        layout.addRow(self.tr("Current Stock"), self.stock_actuel)
        layout.addRow(self.tr("Reserved Stock"), self.stock_reserve)
        layout.addRow(self.tr("Unit"), self.unite)
        layout.addRow(self.tr("Category"), self.categorie)
        layout.addRow(self.tr("Location (Resolved)"), self.emplacement_stockage)
        layout.addRow(self.tr("Status"), self.statut)
        layout.addRow(self.tr("Machine"), self.machine)

        btns = QHBoxLayout()
        self.ok_btn = QPushButton(self.tr("OK"), self)
        self.cancel_btn = QPushButton(self.tr("Cancel"), self)
        btns.addWidget(self.ok_btn)
        btns.addWidget(self.cancel_btn)
        layout.addRow(btns)

        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        # Connections for new emplacement inputs
        self.warehouse_selector.currentIndexChanged.connect(self._on_warehouse_changed_for_emplacement)
        self.resolve_emplacement_btn.clicked.connect(self._resolve_emplacement_from_inputs)

    def _on_warehouse_changed_for_emplacement(self):
        # Clear/update aisle/shelf/level or emplacement_stockage if needed when warehouse changes
        self.emplacement_stockage.clear()
        self.emplacement_stockage.setPlaceholderText(self.tr("Select warehouse and use Find/Set"))
        # Potentially filter self.all_emplacements based on selected warehouse and repopulate self.emplacement_stockage
        # For now, just clearing it. User must use Find/Set.
        logger.debug("Warehouse changed, emplacement combo cleared")

    def _resolve_emplacement_from_inputs(self):
        if not self.db:
            QMessageBox.warning(self, self.tr("Database Error"), self.tr("Database connection not available."))
            return

        current_warehouse_id = self.warehouse_selector.currentData()
        aisle = self.aisle_input.value()
        shelf = self.shelf_input.value()
        level = self.level_input.value()

        if not current_warehouse_id:
            QMessageBox.warning(self, self.tr("Input Error"), self.tr("Please select a warehouse."))
            return

        # Query database for emplacement_id
        # Assuming allee, etagere, niveau are stored as strings in the database, matching previous observations.
        # If they are integers, the str() conversions should be removed.
        sql = """
            SELECT id, nom 
            FROM emplacement 
            WHERE magasin_id = %s AND allee = %s AND etagere = %s AND niveau = %s
        """
        try:
            results_list = self.db.execute(sql, (current_warehouse_id, str(aisle), str(shelf), str(level)))
            result = results_list[0] if results_list else None
            
            self.emplacement_stockage.clear()
            if result:
                emplacement_id = result['id']
                emplacement_nom = result.get('nom', f"A{aisle}S{shelf}L{level}") # Use constructed name if 'nom' is null
                self.emplacement_stockage.addItem(emplacement_nom, emplacement_id)
                self.emplacement_stockage.setCurrentIndex(0)
                QMessageBox.information(self, self.tr("Emplacement Found"), self.tr(f"Emplacement '{emplacement_nom}' selected."))
            else:
                self.emplacement_stockage.setPlaceholderText(self.tr(f"No match found for A{aisle}-S{shelf}-L{level}"))
                QMessageBox.warning(self, self.tr("Not Found"), self.tr("No emplacement found for the specified Aisle, Shelf, Level in this warehouse."))
        except Exception as e:
            QMessageBox.critical(self, self.tr("Query Error"), self.tr(f"Error finding emplacement: {e}"))
            logger.error("_resolve_emplacement_from_inputs failed: %s", e)

    def get_data(self):
        if not self.reference.text().strip() or not self.nom.text().strip() or self.unite.currentIndex() < 0:
            QMessageBox.warning(self, self.tr("Input error"), self.tr("Reference, Name and Unit are required."))
            return None
        return {
            "reference": self.reference.text(),
            "nom": self.nom.text(),
            "fournisseur_pref_id": self.fournisseur_pref_id.currentData() if self.fournisseur_pref_id.count() > 0 else None,
            "prix_unitaire": self.prix_unitaire.value(),
            "stock_alerte": self.stock_alerte.value(),
            "stock_actuel": self.stock_actuel.value(),
            "stock_reserve": self.stock_reserve.value(),
            "unite_id": self.unite.currentData() if self.unite.count() > 0 else None,
            "categorie_id": self.categorie.currentData() if self.categorie.count() > 0 else None,
            "emplacement_id": self.emplacement_stockage.currentData() if self.emplacement_stockage.count() > 0 else None, 
            "statut_id": self.statut.currentData() if self.statut.count() > 0 else None,
            "machine_id": self.machine.currentData() if self.machine.count() > 0 else None
        }

    def set_data(self, piece):
        self.reference.setText(piece.get("reference", ""))
        self.nom.setText(piece.get("nom", ""))

        if piece.get("fournisseur_pref_id") is not None:
            idx = self.fournisseur_pref_id.findData(piece.get("fournisseur_pref_id"))
            if idx >= 0:
                self.fournisseur_pref_id.setCurrentIndex(idx)
        
        self.prix_unitaire.setValue(piece.get("prix_unitaire", 0.0) or 0.0)
        self.stock_alerte.setValue(piece.get("stock_alerte", 0) or 0)
        self.stock_actuel.setValue(piece.get("stock_actuel", 0) or 0)
        self.stock_reserve.setValue(piece.get("stock_reserve", 0) or 0)

        if piece.get("unite_id") is not None:
            idx = self.unite.findData(piece.get("unite_id"))
            if idx >= 0:
                self.unite.setCurrentIndex(idx)

        if piece.get("categorie_id") is not None:
            idx = self.categorie.findData(piece.get("categorie_id"))
            if idx >= 0:
                self.categorie.setCurrentIndex(idx)
        
        self.emplacement_stockage.clear()
        if piece.get("emplacement_id") is not None:
            emp_id = piece.get("emplacement_id")
            # Try to find in self.all_emplacements first (if provided and comprehensive)
            found_emp_local = next((emp for emp in self.all_emplacements if emp['id'] == emp_id), None)

            if found_emp_local:
                magasin_id = found_emp_local.get('magasin_id')
                allee = found_emp_local.get('allee', '1') # Default to '1' if not present
                etagere = found_emp_local.get('etagere', '1') # Default to '1' if not present
                niveau = found_emp_local.get('niveau', '1') # Default to '1' if not present
                nom = found_emp_local.get("nom") or f"A{allee}S{etagere}L{niveau}"

                if magasin_id is not None and self.warehouse_selector.findData(magasin_id) != -1:
                    self.warehouse_selector.setCurrentIndex(self.warehouse_selector.findData(magasin_id))
                
                try:
                    self.aisle_input.setValue(int(str(allee)))
                    self.shelf_input.setValue(int(str(etagere)))
                    self.level_input.setValue(int(str(niveau)))
                except (ValueError, TypeError):
                    logger.warning("Could not convert A/S/L from local to int for emp_id %s. Values: %s, %s, %s", emp_id, allee, etagere, niveau)
                    self.aisle_input.setValue(1)
                    self.shelf_input.setValue(1)
                    self.level_input.setValue(1)

                self.emplacement_stockage.addItem(nom, emp_id)
                self.emplacement_stockage.setCurrentIndex(0)
            elif self.db and emp_id: # Fallback to DB query
                try:
                    sql_details = "SELECT id, nom, magasin_id, allee, etagere, niveau FROM emplacement WHERE id = %s"
                    emp_details_list = self.db.execute(sql_details, (emp_id,))
                    emp_details = emp_details_list[0] if emp_details_list else None
                    
                    if emp_details:
                        magasin_id = emp_details.get('magasin_id')
                        allee_str = str(emp_details.get('allee', '1'))
                        etagere_str = str(emp_details.get('etagere', '1'))
                        niveau_str = str(emp_details.get('niveau', '1'))
                        nom = emp_details.get("nom") or f"A{allee_str}S{etagere_str}L{niveau_str}"

                        if magasin_id is not None and self.warehouse_selector.findData(magasin_id) != -1:
                            self.warehouse_selector.setCurrentIndex(self.warehouse_selector.findData(magasin_id))
                        
                        try:
                            self.aisle_input.setValue(int(allee_str))
                            self.shelf_input.setValue(int(etagere_str))
                            self.level_input.setValue(int(niveau_str))
                        except (ValueError, TypeError):
                            logger.warning("Could not convert A/S/L from DB to int for emp_id %s. Values: %s, %s, %s", emp_id, allee_str, etagere_str, niveau_str)
                            self.aisle_input.setValue(1)
                            self.shelf_input.setValue(1)
                            self.level_input.setValue(1)
                        
                        self.emplacement_stockage.addItem(nom, emp_details['id'])
                        self.emplacement_stockage.setCurrentIndex(0)
                    else:
                        self.emplacement_stockage.setPlaceholderText(self.tr("Emplacement ID not found in DB"))
                        logger.warning("Emplacement ID %s not found in DB during set_data fallback", emp_id)
                except Exception as e:
                    logger.error("Error fetching emplacement details in set_data fallback: %s", e)
                    self.emplacement_stockage.setPlaceholderText(self.tr("Error loading emplacement details"))
            else: # Neither local nor DB access
                 self.emplacement_stockage.setPlaceholderText(self.tr("Emplacement details unavailable"))

        if self.statut.count() > 0 and piece.get("statut_id") is not None:
            idx = self.statut.findData(piece.get("statut_id"))
            if idx >= 0:
                self.statut.setCurrentIndex(idx)
        
        if self.machine.count() > 0 and piece.get("machine_id") is not None:
            idx = self.machine.findData(piece.get("machine_id"))
            if idx >= 0:
                self.machine.setCurrentIndex(idx)
