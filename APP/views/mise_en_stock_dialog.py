from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QComboBox, QSpinBox, QLineEdit, QTextEdit,
                             QPushButton, QLabel, QGroupBox, QDateTimeEdit, QMessageBox)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QFont
from typing import List, Dict, Optional

class MiseEnStockDialog(QDialog):
    """Dialog for putaway from receiving"""
    
    def __init__(self, parent=None, pieces: List[Dict] = None, emplacements: List[Dict] = None):
        super().__init__(parent)
        self.pieces = pieces or []
        self.emplacements = emplacements or []
        
        self.setup_ui()
        self.setup_connections()
        self.load_data()

    def setup_ui(self):
        """Set up the user interface"""
        self.setModal(True)
        self.setWindowTitle(self.tr("Stock Putaway"))
        self.resize(500, 500)
        
        layout = QVBoxLayout()
        
        # Title and description
        title_label = QLabel(self.tr("Stock Putaway"))
        title_label.setFont(QFont("", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        info_label = QLabel(self.tr("Transfers parts from the receiving area to their final storage location."))
        info_label.setWordWrap(True)
        info_label.setStyleSheet("QLabel { color: #666; margin-bottom: 10px; }")
        layout.addWidget(info_label)
        
        # Main information
        main_group = QGroupBox(self.tr("Putaway Information"))
        main_layout = QFormLayout()
        
        # Part
        self.piece_combo = QComboBox()
        self.piece_combo.setEditable(True)
        main_layout.addRow(self.tr("Part:"), self.piece_combo)
        
        # Quantity
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 999999)
        self.quantity_spin.setValue(1)
        main_layout.addRow(self.tr("Quantity to store:"), self.quantity_spin)
        
        # Date and time
        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setDateTime(QDateTime.currentDateTime())
        self.datetime_edit.setCalendarPopup(True)
        main_layout.addRow(self.tr("Storage Date/Time:"), self.datetime_edit)
        
        main_group.setLayout(main_layout)
        layout.addWidget(main_group)
        
        # Locations
        location_group = QGroupBox(self.tr("Locations"))
        location_layout = QFormLayout()
        
        # Source (receiving)
        self.source_location_combo = QComboBox()
        location_layout.addRow(self.tr("From (receiving):"), self.source_location_combo)
        
        # Destination (final storage)
        self.dest_location_combo = QComboBox()
        location_layout.addRow(self.tr("To (final storage):"), self.dest_location_combo)
        
        location_group.setLayout(location_layout)
        layout.addWidget(location_group)
        
        # Additional information
        additional_group = QGroupBox(self.tr("Additional Information"))
        additional_layout = QFormLayout()
        
        # Document reference
        self.reference_edit = QLineEdit()
        self.reference_edit.setPlaceholderText(self.tr("Storage reference, etc."))
        additional_layout.addRow(self.tr("Document reference:"), self.reference_edit)
        
        # Comment
        self.comment_edit = QTextEdit()
        self.comment_edit.setMaximumHeight(80)
        self.comment_edit.setPlaceholderText(self.tr("Comment about putaway..."))
        additional_layout.addRow(self.tr("Comment:"), self.comment_edit)
        
        additional_group.setLayout(additional_layout)
        layout.addWidget(additional_group)
        
        # Buttons
        self.create_buttons(layout)
        
        self.setLayout(layout)

    def create_buttons(self, layout):
        """Create the buttons"""
        btn_layout = QHBoxLayout()
        
        self.validate_btn = QPushButton(self.tr("Confirm Putaway"))
        self.validate_btn.setStyleSheet("QPushButton { background-color: #673AB7; color: white; }")
        self.cancel_btn = QPushButton(self.tr("Cancel"))
        
        btn_layout.addWidget(self.validate_btn)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)

    def setup_connections(self):
        """Set up signal connections"""
        self.validate_btn.clicked.connect(self.validate)
        self.cancel_btn.clicked.connect(self.reject)
        
        if hasattr(self, 'piece_combo'):
            self.piece_combo.currentTextChanged.connect(self.on_piece_changed)

    def load_data(self):
        """Load data into the combo boxes"""
        # Load parts
        if hasattr(self, 'piece_combo'):
            self.piece_combo.clear()
            self.piece_combo.addItem(self.tr("Select a part..."), None)
            
            for piece in self.pieces:
                text = f"{piece['reference']} - {piece['nom']} (Stock: {piece.get('stock_actuel', 0)})"
                self.piece_combo.addItem(text, piece)
        
        # Load source locations (receiving)
        if hasattr(self, 'source_location_combo'):
            self.source_location_combo.clear()
            self.source_location_combo.addItem(self.tr("General receiving area"), None)
            for emplacement in self.emplacements:
                # Filter to show only receiving or general areas
                if 'reception' in emplacement.get('nom', '').lower() or 'general' in emplacement.get('nom', '').lower():
                    text = f"{emplacement['nom']}"
                    if emplacement.get('allee'):
                        text += f" - {emplacement['allee']}"
                    self.source_location_combo.addItem(text, emplacement)
        
        # Load destination locations (storage)
        if hasattr(self, 'dest_location_combo'):
            self.dest_location_combo.clear()
            self.dest_location_combo.addItem(self.tr("Select a location..."), None)
            for emplacement in self.emplacements:
                text = f"{emplacement['nom']}"
                if emplacement.get('allee'):
                    text += f" - {emplacement['allee']}"
                self.dest_location_combo.addItem(text, emplacement)
    def on_piece_changed(self):
        """Handle the change of selected part"""
        # Could be used to load the preferred location of the part
        pass

    def validate(self):
        """Validate and close the dialog"""
        # Data validation
        if not self.piece_combo.currentData():
            QMessageBox.warning(self, self.tr("Validation"), 
                              self.tr("Please select a part."))
            return
        
        if self.quantity_spin.value() <= 0:
            QMessageBox.warning(self, self.tr("Validation"), 
                              self.tr("Quantity must be positive."))
            return
        
        if not self.dest_location_combo.currentData():
            QMessageBox.warning(self, self.tr("Validation"), 
                              self.tr("Please select a destination location."))
            return
        
        self.accept()

    def get_data(self):
        """Return the entered data"""
        piece_data = self.piece_combo.currentData()
        dest_data = self.dest_location_combo.currentData()
        
        return {
            'piece_id': piece_data['id_piece'] if piece_data else None,
            'quantite': self.quantity_spin.value(),
            'emplacement_stockage_id': dest_data['id'] if dest_data else None,
            'reference': self.reference_edit.text().strip(),
            'commentaire': self.comment_edit.toPlainText().strip()
        }
