from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QTextEdit,
                             QPushButton, QLabel, QGroupBox, QDateTimeEdit, QMessageBox,
                             QTabWidget, QWidget)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QFont
from typing import List, Dict, Optional

class MouvementDialog(QDialog):
    def __init__(self, parent=None, mouvement_type: str = 'entree', 
                 pieces: List[Dict] = None, types_mouvement: List[Dict] = None,
                 emplacements: List[Dict] = None):
        super().__init__(parent)
        self.mouvement_type = mouvement_type
        self.pieces = pieces or []
        self.types_mouvement = types_mouvement or []
        self.emplacements = emplacements or []
        
        self.setup_ui()
        self.setup_connections()
        self.load_data()

    def setup_ui(self):
        """Configure the user interface"""
        self.setModal(True)
        self.resize(500, 600)
        
        # Titre selon le type de mouvement
        titles = {
            'entree': self.tr("New Stock Entry"),
            'sortie': self.tr("New Stock Out"),
            'transfert': self.tr("New Transfer"),
            'inventaire': self.tr("Inventory Adjustment")
        }
        self.setWindowTitle(titles.get(self.mouvement_type, self.tr("New Movement")))
        
        layout = QVBoxLayout()
        
        # Onglets pour différents types de mouvements
        if self.mouvement_type in ['entree', 'sortie']:
            self.create_entry_exit_form(layout)
        elif self.mouvement_type == 'transfert':
            self.create_transfer_form(layout)
        elif self.mouvement_type == 'inventaire':
            self.create_inventory_form(layout)
        
        # Boutons
        self.create_buttons(layout)
        
        self.setLayout(layout)

    def create_entry_exit_form(self, layout):
        """Create the form for entry/exit"""
        # Informations principales
        main_group = QGroupBox(self.tr("Main Information"))
        main_layout = QFormLayout()
        
        # Pièce
        self.piece_combo = QComboBox()
        self.piece_combo.setEditable(True)
        main_layout.addRow(self.tr("Part:"), self.piece_combo)
        
        # Type de mouvement
        self.type_combo = QComboBox()
        main_layout.addRow(self.tr("Movement type:"), self.type_combo)
        
        # Quantité
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 999999)
        self.quantity_spin.setValue(1)
        main_layout.addRow(self.tr("Quantity:"), self.quantity_spin)
        
        # Date et heure
        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setDateTime(QDateTime.currentDateTime())
        self.datetime_edit.setCalendarPopup(True)
        main_layout.addRow(self.tr("Date/Time:"), self.datetime_edit)
        
        main_group.setLayout(main_layout)
        layout.addWidget(main_group)
        
        # Emplacement
        location_group = QGroupBox(self.tr("Location"))
        location_layout = QFormLayout()
        
        if self.mouvement_type == 'entree':
            self.location_combo = QComboBox()
            location_layout.addRow(self.tr("Destination location:"), self.location_combo)
        else:  # sortie
            self.location_combo = QComboBox()
            location_layout.addRow(self.tr("Source location:"), self.location_combo)
        
        location_group.setLayout(location_layout)
        layout.addWidget(location_group)
        
        # Informations financières (pour les entrées)
        if self.mouvement_type == 'entree':
            financial_group = QGroupBox(self.tr("Financial Information"))
            financial_layout = QFormLayout()
            
            self.unit_cost_spin = QDoubleSpinBox()
            self.unit_cost_spin.setRange(0.0, 999999.99)
            self.unit_cost_spin.setDecimals(2)
            self.unit_cost_spin.setSuffix(" €")
            financial_layout.addRow(self.tr("Unit cost:"), self.unit_cost_spin)
            
            financial_group.setLayout(financial_layout)
            layout.addWidget(financial_group)
        
        # Informations complémentaires
        self.create_additional_info_form(layout)

    def create_transfer_form(self, layout):
        """Create the form for transfer"""
        # Informations principales
        main_group = QGroupBox(self.tr("Transfer Information"))
        main_layout = QFormLayout()
        
        # Pièce
        self.piece_combo = QComboBox()
        self.piece_combo.setEditable(True)
        main_layout.addRow(self.tr("Part:"), self.piece_combo)
        
        # Quantité
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 999999)
        self.quantity_spin.setValue(1)
        main_layout.addRow(self.tr("Quantity:"), self.quantity_spin)
        
        # Date et heure
        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setDateTime(QDateTime.currentDateTime())
        self.datetime_edit.setCalendarPopup(True)
        main_layout.addRow(self.tr("Date/Time:"), self.datetime_edit)
        
        main_group.setLayout(main_layout)
        layout.addWidget(main_group)
        
        # Emplacements
        location_group = QGroupBox(self.tr("Locations"))
        location_layout = QFormLayout()
        
        self.source_location_combo = QComboBox()
        location_layout.addRow(self.tr("Source location:"), self.source_location_combo)
        
        self.dest_location_combo = QComboBox()
        location_layout.addRow(self.tr("Destination location:"), self.dest_location_combo)
        
        location_group.setLayout(location_layout)
        layout.addWidget(location_group)
        
        # Informations complémentaires
        self.create_additional_info_form(layout)

    def create_inventory_form(self, layout):
        """Create the form for inventory adjustment"""
        # Informations principales
        main_group = QGroupBox(self.tr("Inventory Adjustment"))
        main_layout = QFormLayout()
        
        # Pièce
        self.piece_combo = QComboBox()
        self.piece_combo.setEditable(True)
        main_layout.addRow(self.tr("Part:"), self.piece_combo)
        
        # Stock actuel (lecture seule)
        self.current_stock_label = QLabel("0")
        self.current_stock_label.setStyleSheet("QLabel { font-weight: bold; color: blue; }")
        main_layout.addRow(self.tr("Current stock:"), self.current_stock_label)
        
        # Nouveau stock
        self.new_stock_spin = QSpinBox()
        self.new_stock_spin.setRange(0, 999999)
        self.new_stock_spin.setValue(0)
        main_layout.addRow(self.tr("New stock:"), self.new_stock_spin)
        
        # Différence (calculée automatiquement)
        self.difference_label = QLabel("0")
        self.difference_label.setStyleSheet("QLabel { font-weight: bold; }")
        main_layout.addRow(self.tr("Difference:"), self.difference_label)
        
        # Date et heure
        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setDateTime(QDateTime.currentDateTime())
        self.datetime_edit.setCalendarPopup(True)
        main_layout.addRow(self.tr("Date/Time:"), self.datetime_edit)
        
        main_group.setLayout(main_layout)
        layout.addWidget(main_group)
        
        # Informations complémentaires
        self.create_additional_info_form(layout)

    def create_additional_info_form(self, layout):
        """Create the additional information form"""
        additional_group = QGroupBox(self.tr("Additional Information"))
        additional_layout = QFormLayout()
        
        # Référence document
        self.reference_edit = QLineEdit()
        self.reference_edit.setPlaceholderText(self.tr("Purchase order, invoice, etc."))
        additional_layout.addRow(self.tr("Document reference:"), self.reference_edit)
        
        # Commentaire
        self.comment_edit = QTextEdit()
        self.comment_edit.setMaximumHeight(80)
        self.comment_edit.setPlaceholderText(self.tr("Optional comment..."))
        additional_layout.addRow(self.tr("Comment:"), self.comment_edit)
        
        additional_group.setLayout(additional_layout)
        layout.addWidget(additional_group)

    def create_buttons(self, layout):
        """Create buttons"""
        button_layout = QHBoxLayout()
        
        self.validate_btn = QPushButton(self.tr("Validate"))
        self.validate_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        
        self.cancel_btn = QPushButton(self.tr("Cancel"))
        self.cancel_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        
        button_layout.addStretch()
        button_layout.addWidget(self.validate_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)

    def setup_connections(self):
        """Configure signal connections"""
        self.validate_btn.clicked.connect(self.validate)
        self.cancel_btn.clicked.connect(self.reject)
        
        # Connexions spécifiques selon le type
        if hasattr(self, 'piece_combo'):
            self.piece_combo.currentTextChanged.connect(self.on_piece_changed)
        
        if self.mouvement_type == 'inventaire':
            if hasattr(self, 'new_stock_spin'):
                self.new_stock_spin.valueChanged.connect(self.calculate_difference)

    def load_data(self):
        """Load data into the comboboxes"""
        # Charger les pièces
        if hasattr(self, 'piece_combo'):
            self.piece_combo.clear()
            self.piece_combo.addItem(self.tr("Select a part..."), None)
            
            for piece in self.pieces:
                text = f"{piece['reference']} - {piece['nom']} (Stock: {piece.get('stock_actuel', 0)})"
                self.piece_combo.addItem(text, piece)
        
        # Charger les types de mouvement
        if hasattr(self, 'type_combo'):
            self.type_combo.clear()
            for type_mouvement in self.types_mouvement:
                self.type_combo.addItem(type_mouvement['nom'], type_mouvement)
        
        # Charger les emplacements
        if hasattr(self, 'location_combo'):
            self.location_combo.clear()
            self.location_combo.addItem(self.tr("No specific location"), None)
            for emplacement in self.emplacements:
                text = f"{emplacement['nom']}"
                if emplacement.get('allee'):
                    text += f" - {emplacement['allee']}"
                self.location_combo.addItem(text, emplacement)
        
        # Pour les transferts
        if hasattr(self, 'source_location_combo'):
            for combo in [self.source_location_combo, self.dest_location_combo]:
                combo.clear()
                combo.addItem(self.tr("Select a location..."), None)
                for emplacement in self.emplacements:
                    text = f"{emplacement['nom']}"
                    if emplacement.get('allee'):
                        text += f" - {emplacement['allee']}"
                    combo.addItem(text, emplacement)

    def on_piece_changed(self):
        """Handle change of selected part"""
        if self.mouvement_type == 'inventaire':
            piece_data = self.piece_combo.currentData()
            if piece_data:
                current_stock = piece_data.get('stock_actuel', 0)
                self.current_stock_label.setText(str(current_stock))
                self.new_stock_spin.setValue(current_stock)
                self.calculate_difference()

    def calculate_difference(self):
        """Calculate the difference for inventory adjustment"""
        if self.mouvement_type == 'inventaire':
            try:
                current_stock = int(self.current_stock_label.text())
                new_stock = self.new_stock_spin.value()
                difference = new_stock - current_stock
                
                self.difference_label.setText(str(difference))
                
                # Coloration selon le type de différence
                if difference > 0:
                    self.difference_label.setStyleSheet("QLabel { font-weight: bold; color: green; }")
                elif difference < 0:
                    self.difference_label.setStyleSheet("QLabel { font-weight: bold; color: red; }")
                else:
                    self.difference_label.setStyleSheet("QLabel { font-weight: bold; color: gray; }")
                    
            except ValueError:
                self.difference_label.setText("0")

    def validate(self):
        """Validate the form"""
        try:
            # Validation commune
            if not hasattr(self, 'piece_combo') or not self.piece_combo.currentData():
                QMessageBox.warning(self, self.tr("Validation"), 
                                  self.tr("Please select a part."))
                return
            
            # Validations spécifiques selon le type
            if self.mouvement_type in ['entree', 'sortie']:
                if not self.type_combo.currentData():
                    QMessageBox.warning(self, self.tr("Validation"), 
                                      self.tr("Please select a movement type."))
                    return
                
                if self.quantity_spin.value() <= 0:
                    QMessageBox.warning(self, self.tr("Validation"), 
                                      self.tr("Quantity must be positive."))
                    return
            
            elif self.mouvement_type == 'transfert':
                if not self.source_location_combo.currentData():
                    QMessageBox.warning(self, self.tr("Validation"), 
                                      self.tr("Please select a source location."))
                    return
                
                if not self.dest_location_combo.currentData():
                    QMessageBox.warning(self, self.tr("Validation"), 
                                      self.tr("Please select a destination location."))
                    return
                
                if (self.source_location_combo.currentData()['id'] == 
                    self.dest_location_combo.currentData()['id']):
                    QMessageBox.warning(self, self.tr("Validation"), 
                                      self.tr("Source and destination locations must be different."))
                    return
                
                if self.quantity_spin.value() <= 0:
                    QMessageBox.warning(self, self.tr("Validation"), 
                                      self.tr("Quantity must be positive."))
                    return
            
            elif self.mouvement_type == 'inventaire':
                if self.new_stock_spin.value() < 0:
                    QMessageBox.warning(self, self.tr("Validation"), 
                                      self.tr("New stock cannot be negative."))
                    return
            
            # Si toutes les validations passent
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), 
                               self.tr(f"Error during validation: {e}"))

    def get_data(self) -> Dict:
        """Retrieve form data"""
        try:
            piece_data = self.piece_combo.currentData()
            base_data = {
                'piece_id': piece_data['id_piece'],
                'reference': self.reference_edit.text().strip(),
                'commentaire': self.comment_edit.toPlainText().strip()
            }
            
            if self.mouvement_type in ['entree', 'sortie']:
                type_data = self.type_combo.currentData()
                location_data = self.location_combo.currentData()
                
                base_data.update({
                    'quantite': self.quantity_spin.value(),
                    'type_mouvement': type_data['nom']
                })
                
                if self.mouvement_type == 'entree':
                    base_data['emplacement_id'] = location_data['id'] if location_data else None
                    if hasattr(self, 'unit_cost_spin'):
                        base_data['cout_unitaire'] = self.unit_cost_spin.value() if self.unit_cost_spin.value() > 0 else None
                else:  # sortie
                    base_data['emplacement_id'] = location_data['id'] if location_data else None
            
            elif self.mouvement_type == 'transfert':
                source_data = self.source_location_combo.currentData()
                dest_data = self.dest_location_combo.currentData()
                
                base_data.update({
                    'quantite': self.quantity_spin.value(),
                    'emplacement_source_id': source_data['id'],
                    'emplacement_destination_id': dest_data['id']
                })
            
            elif self.mouvement_type == 'inventaire':
                base_data.update({
                    'nouveau_stock': self.new_stock_spin.value()
                })
            
            return base_data
            
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), 
                               self.tr(f"Error while retrieving data: {e}"))
            return {}

    def set_data(self, data: Dict):
        """Set form data (for editing)"""
        # This method can be used to pre-fill the form
        # when editing an existing movement
        pass