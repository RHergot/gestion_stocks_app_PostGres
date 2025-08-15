from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QComboBox, 
                             QSpinBox, QDoubleSpinBox, QLineEdit, QPushButton,
                             QDialogButtonBox, QMessageBox)
from PySide6.QtCore import Qt

class LigneCommandeDialog(QDialog):
    def __init__(self, db, piece_data=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.piece_data = piece_data or {}
        self.setWindowTitle("Edit line" if piece_data else "New line")
        self.setMinimumWidth(400)
        
        self.init_ui()
        self.load_pieces()
        
        if piece_data:
            self.load_piece_data()
    
    def init_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        # Part selection
        self.piece_combo = QComboBox()
        self.piece_combo.setEditable(True)
        form_layout.addRow("Part:", self.piece_combo)
        
        # Fields for part details (read-only)
        self.reference = QLineEdit()
        self.reference.setReadOnly(True)
        form_layout.addRow("Reference:", self.reference)
        
        self.designation = QLineEdit()
        self.designation.setReadOnly(True)
        form_layout.addRow("Designation:", self.designation)
        
        # Quantity
        self.quantite = QSpinBox()
        self.quantite.setMinimum(1)
        self.quantite.setMaximum(9999)
        form_layout.addRow("Quantity:", self.quantite)
        
        # Unit price
        self.prix_unitaire = QDoubleSpinBox()
        self.prix_unitaire.setMinimum(0)
        self.prix_unitaire.setMaximum(999999.99)
        self.prix_unitaire.setPrefix("€ ")
        form_layout.addRow("Unit price (excl. tax):", self.prix_unitaire)
        
        # Free description
        self.description = QLineEdit()
        form_layout.addRow("Description:", self.description)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.validate)
        button_box.rejected.connect(self.reject)
        
        # Connect part change
        self.piece_combo.currentIndexChanged.connect(self.on_piece_changed)
        
        layout.addLayout(form_layout)
        layout.addWidget(button_box)
        self.setLayout(layout)
    
    def load_pieces(self):
        """Load the list of parts from the database"""
        print("Starting parts loading...")
        try:
            with self.db.conn.cursor() as cur:
                print("Database connection established")
                
                # Check the content of the piece table
                cur.execute("SELECT COUNT(*) FROM piece")
                count = cur.fetchone()[0]
                print(f"Total number of parts in the table: {count}")
                
                # Show first rows for debugging
                if count > 0:
                    cur.execute("SELECT id_piece, reference, nom, statut, stock_actuel FROM piece LIMIT 5")
                    print("\nExample of parts in the table:")
                    for row in cur.fetchall():
                        print(f"ID: {row[0]}, Ref: {row[1]}, Name: {row[2]}, Status: {row[3]}, Stock: {row[4]}")
                
                # First check if the table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE  table_schema = 'public'
                        AND    table_name   = 'piece'
                    );
                """)
                table_exists = cur.fetchone()[0]
                
                if not table_exists:
                    QMessageBox.warning(
                        self,
                        "Missing table",
                        "The 'piece' table does not exist in the database."
                    )
                    return
                
                # Retrieve the list of active parts with their available stock
                query = """
                    SELECT 
                        p.id_piece, 
                        p.reference, 
                        p.nom, 
                        COALESCE(p.prix_unitaire, 0) as prix_unitaire, 
                        p.stock_actuel,
                        p.stock_alerte,
                        p.unite,
                        p.categorie,
                        p.statut
                    FROM piece p
                    WHERE (LOWER(p.statut) = 'actif' OR p.statut IS NULL)  -- Accepter les pièces sans statut
                    AND (p.stock_actuel > 0 OR p.stock_actuel IS NULL)  -- Accepter les pièces sans stock défini
                    ORDER BY p.reference
                """
                print("Executing SQL query:", query)
                cur.execute(query)
                rows = cur.fetchall()
                print(f"{len(rows)} parts found in the database")
                
                self.pieces = []
                self.piece_combo.clear()
                self.piece_combo.addItem("Select a part", None)
                
                for row in rows:
                    try:
                        id_piece, reference, nom, prix_unitaire, stock_actuel, stock_alerte, unite, categorie, statut = row
                        print(f"Processing part: {reference} - {nom} (ID: {id_piece})")
                        
                        # Create the part dictionary with all information
                        piece = {
                            'id': id_piece,
                            'reference': reference or '',
                            'nom': nom or '',
                            'prix': float(prix_unitaire) if prix_unitaire is not None else 0.0,
                            'stock': int(stock_actuel) if stock_actuel is not None else 0,
                            'stock_alerte': int(stock_alerte) if stock_alerte is not None else 0,
                            'unite': unite or 'part',
                            'categorie': categorie or 'Uncategorized',
                            'statut': statut or 'Actif'
                        }
                        
                        # Add the part to the list
                        self.pieces.append(piece)
                        
                        # Add the part to the combo box
                        display_text = f"{piece['reference']} - {piece['nom']} ({piece['stock']} {piece['unite']})"
                        print(f"Add to combobox: {display_text}")
                        self.piece_combo.addItem(display_text, id_piece)
                        
                    except Exception as e:
                        print(f"Error while processing a part: {str(e)}")
                        import traceback
                        traceback.print_exc()
                    
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Unable to load the list of parts:\n{str(e)}"
            )
    
    def load_piece_data(self):
        if not self.piece_data:
            return
            
        # To implement: Load the selected part's data
        pass
    
    def on_piece_changed(self, index):
        # Get the ID of the selected part
        piece_id = self.piece_combo.currentData()
        
        # Reset fields if no part is selected
        if not piece_id:
            self.reference.clear()
            self.designation.clear()
            self.quantite.setValue(1)
            self.prix_unitaire.setValue(0.0)
            return
            
        # Find the selected part
        piece = next((p for p in self.pieces if p['id'] == piece_id), None)
        if not piece:
            return
            
        # Update fields with the part information
        self.reference.setText(piece['reference'])
        self.designation.setText(piece['nom'])
        
        # Use the part price as default value
        prix_piece = piece.get('prix', 0.0)
        self.prix_unitaire.setValue(prix_piece)
        
        # Set the maximum quantity based on available stock
        stock_disponible = piece.get('stock', 0)
        stock_alerte = piece.get('stock_alerte', 0)
        
        # Configure the quantity spinbox
        self.quantite.setMaximum(max(1, stock_disponible))
        self.quantite.setValue(1)
        
        # If stock is low or depleted, show an information message
        if stock_disponible <= stock_alerte or stock_disponible <= 5:
            message = f"Limited stock: {stock_disponible} {piece.get('unite', 'part')} available"
            if stock_disponible <= 0:
                message = "Out of stock!"
                
            QMessageBox.warning(
                self,
                "Stock alert",
                f"{message}. The alert stock level is {stock_alerte} {piece.get('unite', 'part')}."
            )
    
    def validate(self):
        # Ensure a part is selected
        piece_id = self.piece_combo.currentData()
        if not piece_id:
            QMessageBox.warning(
                self, 
                "Selection required", 
                "Please select a part from the list."
            )
            return False
            
        # Ensure the quantity is valid
        quantite = self.quantite.value()
        if quantite <= 0:
            QMessageBox.warning(
                self, 
                "Invalid quantity", 
                "Quantity must be greater than zero."
            )
            return False
            
        # Check available stock
        piece = next((p for p in getattr(self, 'pieces', []) if p['id'] == piece_id), None)
        if piece:
            stock_disponible = int(piece.get('stock', 0))
            if quantite > stock_disponible:
                QMessageBox.warning(
                    self,
                    "Insufficient stock",
                    f"Insufficient stock. Only {stock_disponible} part(s) left in stock."
                )
                return False
        
        # Ensure the price is valid
        if self.prix_unitaire.value() <= 0:
            QMessageBox.warning(
                self,
                "Invalid price",
                "Unit price must be greater than zero."
            )
            return False
            
        # Toutes les validations sont passées
        self.accept()
    
    def get_data(self):
        """Retourne un dictionnaire avec les données du formulaire"""
        return {
            'piece_id': self.piece_combo.currentData(),
            'piece_reference': self.reference.text(),
            'piece_nom': self.designation.text(),
            'quantite_commandee': self.quantite.value(),
            'prix_unitaire_ht': self.prix_unitaire.value(),
            'description_libre': self.description.text()
        }
