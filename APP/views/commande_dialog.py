from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, 
                             QSpinBox, QPushButton, QMessageBox, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QLabel, QGroupBox,
                             QFrame, QWidget)
from PySide6.QtCore import Qt, QDate, Signal
from datetime import datetime
from APP.controllers.commande_controller import CommandeController
from APP.models.commande_repository import CommandeRepository
from APP.models.ligne_commande_repository import LigneCommandeRepository

class CommandeDialog(QDialog):
    # Signal émis quand une commande est livrée pour rafraîchir la vue
    commande_livree = Signal()
    
    def __init__(self, db, commande_data=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.commande_data = commande_data or {}
        self.is_editing = bool(commande_data)
        self.commande_controller = CommandeController(
            db,
            CommandeRepository(db),
            LigneCommandeRepository(db)
        )
        self.setWindowTitle("Edit order" if commande_data else "New order")
        self.setMinimumWidth(900)
        
        self.init_ui()
        self.load_fournisseurs()
        
        if commande_data:
            self.load_commande_data()
        
        # Mettre à jour la visibilité et l'état des boutons après l'initialisation complète
        if self.is_editing:
            self.show_status_buttons()
            self.update_status_buttons()
    
    def show_status_buttons(self):
        """Force l'affichage des boutons de statut en mode édition"""
        if hasattr(self, 'status_widget'):
            self.status_widget.setVisible(True)
            self.status_label.setVisible(True)
            print(f"[DEBUG] show_status_buttons: widget visible = {self.status_widget.isVisible()}")
            
            # Forcer la visibilité de tous les boutons
            for btn_name in ['confirmer_btn', 'envoyer_btn', 'livrer_btn', 'copier_btn', 'annuler_btn']:
                if hasattr(self, btn_name):
                    btn = getattr(self, btn_name)
                    btn.setVisible(True)
                    print(f"[DEBUG] {btn_name} visible = {btn.isVisible()}")
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Group for basic order information
        info_group = QGroupBox("Order information")
        info_layout = QFormLayout()
        
        # Order number
        self.numero_commande = QLineEdit()
        info_layout.addRow("Order number:", self.numero_commande)
        
        # Supplier
        self.fournisseur_combo = QComboBox()
        info_layout.addRow("Supplier:", self.fournisseur_combo)
        
        # Dates
        self.date_commande = QDateEdit(calendarPopup=True)
        self.date_commande.setDate(QDate.currentDate())
        self.date_livraison_prevue = QDateEdit(calendarPopup=True)
        self.date_livraison_prevue.setDate(QDate.currentDate().addDays(14))
        
        info_layout.addRow("Order date:", self.date_commande)
        info_layout.addRow("Expected delivery date:", self.date_livraison_prevue)
        
        # Status
        self.statut_combo = QComboBox()
        self.statut_combo.addItems(["Brouillon", "Validee", "Envoyee", "Partielle", "Livree", "Annulee"])
        info_layout.addRow("Status:", self.statut_combo)
        
        # Amounts
        self.total_ht = QDoubleSpinBox()
        self.total_ht.setMaximum(999999.99)
        self.total_ht.setPrefix("€ ")
        
        self.frais_port = QDoubleSpinBox()
        self.frais_port.setMaximum(9999.99)
        self.frais_port.setPrefix("€ ")
        
        info_layout.addRow("Total (excl. tax):", self.total_ht)
        info_layout.addRow("Shipping cost:", self.frais_port)
        
        # Supplier reference
        self.reference_fournisseur = QLineEdit()
        info_layout.addRow("Supplier ref.:", self.reference_fournisseur)
        
        # Payment method
        self.mode_paiement = QComboBox()
        self.mode_paiement.addItems(["Virement", "Chèque", "Carte", "Prélèvement", "Autre"])
        info_layout.addRow("Payment method:", self.mode_paiement)
        
        # Notes
        self.notes = QLineEdit()
        info_layout.addRow("Notes:", self.notes)
        
        info_group.setLayout(info_layout)
        
        # Group for order lines
        self.lignes_group = QGroupBox("Order lines")
        lignes_layout = QVBoxLayout()
        
        # Create buttons first
        self.add_ligne_btn = QPushButton(self.tr("Add line"))
        self.edit_ligne_btn = QPushButton(self.tr("Edit"))
        self.del_ligne_btn = QPushButton(self.tr("Delete"))
        
        # Désactiver les boutons d'édition et suppression initialement
        self.edit_ligne_btn.setEnabled(False)
        self.del_ligne_btn.setEnabled(False)
        
        # Boutons d'action pour les lignes
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.add_ligne_btn)
        btn_layout.addWidget(self.edit_ligne_btn)
        btn_layout.addWidget(self.del_ligne_btn)
        
        # Order lines table
        self.lignes_table = QTableWidget()
        self.lignes_table.setColumnCount(6)  # 6 colonnes
        self.lignes_table.setHorizontalHeaderLabels([
            "Reference", 
            "Designation", 
            "Qty", 
            "Unit Price", 
            "Total",
            "Description"
        ])
        self.lignes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.lignes_table.horizontalHeader().setStretchLastSection(True)  # Stretch last column
        # Connect to enable/disable buttons dynamically based on selection
        self.lignes_table.itemSelectionChanged.connect(self.on_ligne_selection_changed)
        
        lignes_layout.addWidget(self.lignes_table)
        lignes_layout.addLayout(btn_layout)
        self.lignes_group.setLayout(lignes_layout)
        
        # Section for status actions
        self.status_label = QLabel("<b>Order actions:</b>")
        self.status_widget = QWidget()
        self.status_layout = QHBoxLayout()
        
        # Status management buttons
        self.confirmer_btn = QPushButton(self.tr("Confirm"))
        self.confirmer_btn.setToolTip("Change from 'Brouillon' to 'Validee'")
        
        self.envoyer_btn = QPushButton(self.tr("Send"))
        self.envoyer_btn.setToolTip("Change from 'Validee' to 'Envoyee'")
        
        self.livrer_btn = QPushButton(self.tr("Deliver"))
        self.livrer_btn.setToolTip("Change from 'Envoyee' to 'Livree' and create stock movements")
        
        self.copier_btn = QPushButton(self.tr("Duplicate"))
        self.copier_btn.setToolTip("Create a new order with the same lines")
        
        self.annuler_btn = QPushButton(self.tr("Cancel order"))
        self.annuler_btn.setToolTip("Cancel the order (becomes inaccessible)")
        self.annuler_btn.setStyleSheet("QPushButton { background-color: #ff6b6b; color: white; }")
        
        # Ajouter les boutons au layout
        self.status_layout.addWidget(self.confirmer_btn)
        self.status_layout.addWidget(self.envoyer_btn)
        self.status_layout.addWidget(self.livrer_btn)
        self.status_layout.addWidget(self.copier_btn)
        self.status_layout.addStretch()
        self.status_layout.addWidget(self.annuler_btn)
        
        self.status_widget.setLayout(self.status_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        
        # Dialog buttons
        button_box = QHBoxLayout()
        self.save_btn = QPushButton(self.tr("Save"))
        self.cancel_btn = QPushButton(self.tr("Close"))
        
        button_box.addStretch()
        button_box.addWidget(self.save_btn)
        button_box.addWidget(self.cancel_btn)
        
        # Add groups to main layout
        layout.addWidget(info_group)
        layout.addWidget(self.lignes_group)
        
        # Always add the separator and status section
        layout.addWidget(separator)
        layout.addWidget(self.status_label)
        layout.addWidget(self.status_widget)
        
        # Control visibility according to mode
        if self.is_editing:
            separator.setVisible(True)
            self.status_label.setVisible(True)
            self.status_widget.setVisible(True)
        else:
            separator.setVisible(False)
            self.status_label.setVisible(False)
            self.status_widget.setVisible(False)
        
        layout.addLayout(button_box)
        
        self.setLayout(layout)
        
        # Signals connections
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.add_ligne_btn.clicked.connect(self.add_ligne)
        self.edit_ligne_btn.clicked.connect(self.edit_ligne)
        self.del_ligne_btn.clicked.connect(self.del_ligne)
        
        # Status buttons connections (only in edit mode)
        if self.is_editing:
            self.confirmer_btn.clicked.connect(self.confirmer_commande)
            self.envoyer_btn.clicked.connect(self.envoyer_commande)
            self.livrer_btn.clicked.connect(self.livrer_commande)
            self.copier_btn.clicked.connect(self.copier_commande)
            self.annuler_btn.clicked.connect(self.annuler_commande)
    
    def load_fournisseurs(self):
        """Load the suppliers list from the database."""
        try:
            with self.db.conn.cursor() as cur:
                cur.execute("""
                    SELECT id_fournisseur, nom, COALESCE(telephone, '') as reference
                    FROM fournisseur 
                    ORDER BY nom
                """)
                fournisseurs = cur.fetchall()
                
                self.fournisseur_combo.clear()
                for id_fournisseur, nom, reference in fournisseurs:
                    display_text = f"{nom} ({reference})" if reference else nom
                    self.fournisseur_combo.addItem(display_text, userData=id_fournisseur)
                
                if self.fournisseur_combo.count() > 0:
                    self.fournisseur_combo.setCurrentIndex(0)
                else:
                    self.fournisseur_combo.addItem(self.tr("No supplier available"), None)
                    
        except Exception as e:
            QMessageBox.critical(
                self, 
                self.tr("Error"),
                self.tr(f"Unable to load suppliers list:\n{str(e)}")
            )
            # Add an empty supplier to avoid errors
            self.fournisseur_combo.addItem("No supplier available", None)
    
    def parse_date(self, date_str):
        """Convert a date string to a QDate object"""
        if not date_str:
            return None
            
        try:
            # Try different date formats
            formats = [
                '%Y-%m-%d %H:%M:%S',  # Format SQL standard avec heure
                '%Y-%m-%d',            # Format SQL date seule
                '%d/%m/%Y %H:%M:%S',   # Format français avec heure
                '%d/%m/%Y'              # Format français date seule
            ]
            
            # If it's already a date or datetime object
            if hasattr(date_str, 'year') and hasattr(date_str, 'month') and hasattr(date_str, 'day'):
                return QDate(date_str.year, date_str.month, date_str.day)
                
            # Otherwise, try to parse the string
            for fmt in formats:
                try:
                    dt = datetime.strptime(str(date_str), fmt)
                    return QDate(dt.year, dt.month, dt.day)
                except ValueError:
                    continue
                    
            print(f"[WARNING] Unrecognized date format: {date_str}")
            return None
            
        except Exception as e:
            print(f"[ERROR] Error parsing date {date_str}: {str(e)}")
            return None
    
    def load_commande_data(self):
        # Remplir les champs avec les données existantes
        if not self.commande_data:
            return
        
        try:
            # Remplir les champs de base
            self.numero_commande.setText(self.commande_data.get('numero_commande', ''))
            
            # Sélectionner le fournisseur dans la combo
            fournisseur_id = self.commande_data.get('fournisseur_id')
            if fournisseur_id:
                index = self.fournisseur_combo.findData(fournisseur_id)
                if index >= 0:
                    self.fournisseur_combo.setCurrentIndex(index)
            
            # Remplir les dates
            if 'date_commande' in self.commande_data and self.commande_data['date_commande']:
                qdate = self.parse_date(self.commande_data['date_commande'])
                if qdate:
                    self.date_commande.setDate(qdate)
                    
            if 'date_livraison_prevue' in self.commande_data and self.commande_data['date_livraison_prevue']:
                qdate = self.parse_date(self.commande_data['date_livraison_prevue'])
                if qdate:
                    self.date_livraison_prevue.setDate(qdate)
            
            # Remplir le statut
            statut = self.commande_data.get('statut', '')
            if statut:
                index = self.statut_combo.findText(statut, Qt.MatchFixedString)
                if index >= 0:
                    self.statut_combo.setCurrentIndex(index)
            
            # Remplir les montants
            if 'total_ht' in self.commande_data:
                self.total_ht.setValue(float(self.commande_data['total_ht'] or 0))
                
            if 'frais_port' in self.commande_data:
                self.frais_port.setValue(float(self.commande_data['frais_port'] or 0))
            
            # Autres champs
            if 'reference_fournisseur' in self.commande_data:
                self.reference_fournisseur.setText(self.commande_data['reference_fournisseur'] or '')
                
            if 'mode_paiement' in self.commande_data:
                index = self.mode_paiement.findText(
                    self.commande_data['mode_paiement'], 
                    Qt.MatchFixedString
                )
                if index >= 0:
                    self.mode_paiement.setCurrentIndex(index)
            
            if 'notes_commande' in self.commande_data:
                self.notes.setText(self.commande_data['notes_commande'] or '')
            
            # Charger les lignes de commande si l'ID est disponible
            if 'id_commande' in self.commande_data:
                self.load_lignes_commande()
                
        except Exception as e:
            QMessageBox.warning(
                self, 
                "Loading error", 
                f"Unable to load order data:\n{str(e)}"
            )
    
    def load_lignes_commande(self):
        """Load order lines from the database"""
        if not self.commande_data or 'id_commande' not in self.commande_data:
            return
            
        try:
            # Retrieve order lines from the database
            from ..models.ligne_commande_repository import LigneCommandeRepository
            repo = LigneCommandeRepository(self.db)
            lignes = repo.get_lignes_by_commande(self.commande_data['id_commande'])
            
            # Clear table
            self.lignes_table.setRowCount(0)
            
            # Fill table with lines
            for ligne in lignes:
                row = self.lignes_table.rowCount()
                self.lignes_table.insertRow(row)
                
                # Compute total
                quantite = ligne.get('quantite_commandee', 0)
                prix_unitaire = float(ligne.get('prix_unitaire_ht', 0))
                total = quantite * prix_unitaire
                
                # Create cells with data
                cells = [
                    QTableWidgetItem(ligne.get('piece_reference', '')),  # Reference
                    QTableWidgetItem(ligne.get('piece_nom', '')),        # Designation
                    QTableWidgetItem(str(quantite)),                      # Quantity
                    QTableWidgetItem(f"{prix_unitaire:.2f} €"),         # Unit price
                    QTableWidgetItem(f"{total:.2f} €"),                 # Total
                    QTableWidgetItem(ligne.get('description_libre', ''))  # Description
                ]
                
                # Ajouter les cellules au tableau
                for col, cell in enumerate(cells):
                    self.lignes_table.setItem(row, col, cell)
                    
                    # Store raw data in first cell for future reference
                    if col == 0:
                        cell.setData(Qt.UserRole, {
                            'piece_id': ligne.get('piece_id'),
                            'piece_reference': ligne.get('piece_reference', ''),
                            'piece_nom': ligne.get('piece_nom', ''),
                            'quantite_commandee': quantite,
                            'prix_unitaire_ht': prix_unitaire,
                            'description_libre': ligne.get('description_libre', '')
                        })
                
                # Enable edit and delete buttons
                self.edit_ligne_btn.setEnabled(True)
                self.del_ligne_btn.setEnabled(True)
                
            # Resize columns to content
            self.lignes_table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.warning(
                self, 
                "Loading error", 
                f"Unable to load order lines:\n{str(e)}"
            )
    
    def add_ligne(self):
        """Open the dialog to add a new order line"""
        from .ligne_commande_dialog import LigneCommandeDialog
        
        dialog = LigneCommandeDialog(self.db, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                # Compute total
                total = data['quantite_commandee'] * data['prix_unitaire_ht']
                
                # Add new line to table
                row = self.lignes_table.rowCount()
                self.lignes_table.insertRow(row)
                
                # Create cells with data
                cells = [
                    QTableWidgetItem(data['piece_reference']),  # Reference
                    QTableWidgetItem(data['piece_nom']),        # Designation
                    QTableWidgetItem(str(data['quantite_commandee'])),  # Quantity
                    QTableWidgetItem(f"{data['prix_unitaire_ht']:.2f} €"),  # Unit price
                    QTableWidgetItem(f"{total:.2f} €"),  # Total
                    QTableWidgetItem(data.get('description_libre', ''))  # Description
                ]
                
                # Add cells to table
                for col, cell in enumerate(cells):
                    self.lignes_table.setItem(row, col, cell)
                    
                    # Store raw data in first cell for future reference
                    if col == 0:
                        cell.setData(Qt.UserRole, data)
                
                # Resize columns to content
                self.lignes_table.resizeColumnsToContents()
                
                # Enable edit and delete buttons
                self.edit_ligne_btn.setEnabled(True)
                self.del_ligne_btn.setEnabled(True)
    
    def get_lignes_data(self):
        """Retourne une liste des lignes de commande avec extraction robuste."""
        lignes = []
        for row in range(self.lignes_table.rowCount()):
            piece_data = self.lignes_table.item(row, 0).data(Qt.UserRole)
            
            # Extraction robuste de piece_id (gère dicts imbriqués)
            if isinstance(piece_data, dict):
                piece_id = piece_data.get('piece_id')
                if isinstance(piece_id, dict):
                    piece_id = piece_id.get('id_piece') or piece_id.get('piece_id')
            else:
                piece_id = piece_data
            
            # Extraction des données de cellule avec fallback sur UserRole
            quantite = self.lignes_table.item(row, 2)
            prix_text = self.lignes_table.item(row, 3)
            
            quantite_val = int(quantite.text()) if quantite else (
                piece_data.get('quantite_commandee', 0) if isinstance(piece_data, dict) else 0
            )
            prix_val = float(prix_text.text().replace('€', '').strip()) if prix_text else (
                float(piece_data.get('prix_unitaire_ht', 0)) if isinstance(piece_data, dict) else 0.0
            )
            
            ligne = {
                'piece_id': piece_id,
                'piece_reference': self.lignes_table.item(row, 0).text() if self.lignes_table.item(row, 0) else '',
                'piece_nom': self.lignes_table.item(row, 1).text() if self.lignes_table.item(row, 1) else '',
                'quantite_commandee': quantite_val,
                'prix_unitaire_ht': prix_val,
                'description_libre': piece_data.get('description_libre', '') if isinstance(piece_data, dict) else ''
            }
            lignes.append(ligne)
        return lignes
    
    def edit_ligne(self):
        """Open the dialog to edit the selected order line"""
        row = self.lignes_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No selection", "Please select a line to edit.")
            return
        # Récupérer les données brutes de la ligne sélectionnée
        piece_data = self.lignes_table.item(row, 0).data(Qt.UserRole)
        from .ligne_commande_dialog import LigneCommandeDialog
        dialog = LigneCommandeDialog(self.db, piece_data=piece_data, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                total = data['quantite_commandee'] * data['prix_unitaire_ht']
                # Mettre à jour les cellules de la ligne
                cells = [
                    QTableWidgetItem(data['piece_reference']),
                    QTableWidgetItem(data['piece_nom']),
                    QTableWidgetItem(str(data['quantite_commandee'])),
                    QTableWidgetItem(f"{data['prix_unitaire_ht']:.2f} €"),
                    QTableWidgetItem(f"{total:.2f} €"),
                    QTableWidgetItem(data.get('description_libre', ''))
                ]
                for col, cell in enumerate(cells):
                    self.lignes_table.setItem(row, col, cell)
                    if col == 0:
                        cell.setData(Qt.UserRole, data)
                self.lignes_table.resizeColumnsToContents()

    def del_ligne(self):
        """Delete the selected line from the order lines table"""
        row = self.lignes_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No selection", "Please select a line to delete.")
            return
        self.lignes_table.removeRow(row)
        # Laisser la gestion de l'état des boutons à on_ligne_selection_changed
        self.on_ligne_selection_changed()
    
    
    def on_ligne_selection_changed(self):
        selected = self.lignes_table.currentRow() >= 0
        self.edit_ligne_btn.setEnabled(selected)
        self.del_ligne_btn.setEnabled(selected)

    def get_data(self):
        """
        Return a dictionary with the form data
        
        Returns:
            dict: The form data or None if validation fails
        """
        # Validate a supplier is selected
        fournisseur_id = self.fournisseur_combo.currentData()
        if not fournisseur_id:
            QMessageBox.warning(
                self,
                "Required field",
                "Please select a supplier."
            )
            return None
            
        # Validate that order lines are present
        lignes = self.get_lignes_data()
        if not lignes:
            QMessageBox.warning(
                self,
                "Empty order",
                "Please add at least one order line."
            )
            return None
            
        # Validate order number
        numero_commande = self.numero_commande.text().strip()
        if not numero_commande:
            QMessageBox.warning(
                self,
                "Required field",
                "Please enter an order number."
            )
            return None
        
        # Calculer le total HT à partir des lignes
        total_ht = sum(ligne['prix_unitaire_ht'] * ligne['quantite_commandee'] for ligne in lignes)
        
        # Default values for a new order
        self.fields = {
            'fournisseur_id': None,
            'numero_commande': '',
            'date_commande': datetime.now().strftime('%Y-%m-%d'),
            'date_livraison_prevue': '',
            'statut': 'Brouillon',  # Keep French canonical value matching DB constraint
            'total_ht': 0.0,
            'frais_port': 0.0,
            'reference_fournisseur': '',
            'mode_paiement': '',
            'notes_commande': ''
        }
        
        # Ensure status is valid
        statut = self.statut_combo.currentText()
        statuts_valides = ['Brouillon', 'Validee', 'Envoyee', 'Partielle', 'Livree', 'Annulee']
        if statut not in statuts_valides:
            statut = 'Brouillon'  # Default if status not valid
            
        data = {
            'numero_commande': numero_commande,
            'fournisseur_id': fournisseur_id,
            'date_commande': self.date_commande.date().toString(Qt.ISODate),
            'date_livraison_prevue': self.date_livraison_prevue.date().toString(Qt.ISODate),
            'statut': statut,
            'total_ht': total_ht,
            'frais_port': self.frais_port.value(),
            'reference_fournisseur': self.reference_fournisseur.text().strip() or None,
            'mode_paiement': self.mode_paiement.currentText(),
            'notes_commande': self.notes.text().strip() or None,
            'lignes': lignes
        }
        
        # Add ID if in edit mode
        if self.commande_data and 'id_commande' in self.commande_data:
            data['id_commande'] = self.commande_data['id_commande']
        
        return data

    def update_status_buttons(self):
        """Update visibility and state of buttons based on current status"""
        if not self.is_editing:
            return
            
        statut = self.commande_data.get('statut', 'Brouillon')
        print(f"[DEBUG] update_status_buttons: statut={statut}, is_editing={self.is_editing}")
        
        # Ensure the widget is visible
        if hasattr(self, 'status_widget'):
            self.status_widget.setVisible(True)
            print(f"[DEBUG] Widget de statut rendu visible: {self.status_widget.isVisible()}")
        
        # Disable all buttons by default
        self.confirmer_btn.setEnabled(False)
        self.envoyer_btn.setEnabled(False)
        self.livrer_btn.setEnabled(False)
        self.copier_btn.setEnabled(True)  # Always available
        self.annuler_btn.setEnabled(False)
        
        # Enable buttons depending on status
        if statut == 'Brouillon':
            self.confirmer_btn.setEnabled(True)
            self.annuler_btn.setEnabled(True)
        elif statut == 'Validee':
            self.envoyer_btn.setEnabled(True)
            self.annuler_btn.setEnabled(True)
        elif statut == 'Envoyee':
            self.livrer_btn.setEnabled(True)
            self.annuler_btn.setEnabled(True)
        elif statut == 'Livree':
            # Order finished, only duplicate is possible
            pass
        elif statut == 'Annulee':
            # Order cancelled, only duplicate is possible
            pass
    
    def confirmer_commande(self):
        """Change order from Brouillon to Validee"""
        if self._changer_statut('Validee'):
            QMessageBox.information(self, "Success", "Order successfully confirmed.")
            self.update_status_buttons()
    
    def envoyer_commande(self):
        """Change order from Validee to Envoyee"""
        if self._changer_statut('Envoyee'):
            QMessageBox.information(self, "Success", "Order sent to supplier.")
            self.update_status_buttons()
    
    def livrer_commande(self):
        """Change order from Envoyee to Livree and create stock movements"""
        reply = QMessageBox.question(
            self, 
            "Confirm delivery", 
            "Are you sure you want to mark this order as delivered?\n"
            "This will automatically create incoming stock movements.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Change status
                if self._changer_statut('Livree'):
                    # Create stock movements
                    self._creer_mouvements_livraison()
                    QMessageBox.information(
                        self, 
                        "Success", 
                        "Order successfully delivered.\nStock movements have been created."
                    )
                    self.update_status_buttons()
                    self.commande_livree.emit()  # Emit signal to refresh the view
            except Exception as e:
                QMessageBox.critical(
                    self, 
                    "Error", 
                    f"Error while delivering the order:\n{str(e)}"
                )
    
    def copier_commande(self):
        """Create a new order with the same lines"""
        reply = QMessageBox.question(
            self, 
            "Duplicate order", 
            "Do you want to create a new order with the same lines?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self._creer_copie_commande()
                QMessageBox.information(self, "Success", "New order created successfully.")
            except Exception as e:
                QMessageBox.critical(
                    self, 
                    "Error", 
                    f"Error while duplicating the order:\n{str(e)}"
                )
    
    def annuler_commande(self):
        """Cancel the order"""
        reply = QMessageBox.question(
            self, 
            "Cancel order", 
            "Are you sure you want to cancel this order?\n"
            "This action is irreversible.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self._changer_statut('Annulee'):
                QMessageBox.information(self, "Success", "Order cancelled.")
                self.update_status_buttons()
    
    def _changer_statut(self, nouveau_statut):
        """Change the order status (delegates to controller)."""
        try:
            self.commande_controller.changer_statut(self.commande_data['id_commande'], nouveau_statut)
            # Update local data and combo
            self.commande_data['statut'] = nouveau_statut
            if nouveau_statut == 'Livree':
                self.commande_data['date_livraison_reelle'] = datetime.now().strftime('%Y-%m-%d')
            index = self.statut_combo.findText(nouveau_statut, Qt.MatchFixedString)
            if index >= 0:
                self.statut_combo.setCurrentIndex(index)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error while changing status:\n{str(e)}")
            return False
    
    def _creer_mouvements_livraison(self):
        """Create stock movements for the order delivery (delegates to controller)."""
        return self.commande_controller.creer_mouvements_livraison(self.commande_data)
    
    def _creer_copie_commande(self):
        """Create a copy of the order (delegates to controller)."""
        try:
            return self.commande_controller.creer_copie_commande(self.commande_data)
        except ValueError as e:
            QMessageBox.warning(self, self.tr("Error"), self.tr(str(e)))
            return None
    
    def _generer_nouveau_numero(self):
        """Generate a new unique order number (via SQL MAX for O(1))."""
        try:
            with self.db.conn.cursor() as cur:
                cur.execute(
                    "SELECT MAX(CAST(NULLIF(regexp_replace(numero_commande, '[^0-9]', '', 'g'), '') AS INTEGER)) "
                    "FROM commande"
                )
                result = cur.fetchone()
                max_num = result[0] if result and result[0] else 0
            return str(max_num + 1)
        except Exception:
            return f"CMD-{int(datetime.now().timestamp())}"
