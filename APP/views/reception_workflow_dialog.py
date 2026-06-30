from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QTextEdit,
                             QPushButton, QLabel, QGroupBox, QDateTimeEdit, QMessageBox)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QFont
from typing import List, Dict, Optional

class ReceptionWorkflowDialog(QDialog):
    """Dialog pour la réception de pièces dans le workflow de réception"""
    
    def __init__(self, parent=None, pieces: List[Dict] = None, 
                 types_reception: List[Dict] = None, emplacements: List[Dict] = None):
        super().__init__(parent)
        self.pieces = pieces or []
        self.types_reception = types_reception or []
        self.emplacements = emplacements or []
        
        self.setup_ui()
        self.setup_connections()
        self.load_data()

    def setup_ui(self):
        """Configure l'interface utilisateur"""
        self.setModal(True)
        self.setWindowTitle(self.tr("Parts Reception"))
        self.resize(500, 600)
        
        layout = QVBoxLayout()
        
        # Titre et description
        title_label = QLabel(self.tr("Parts Reception"))
        title_label.setFont(QFont("", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        info_label = QLabel(self.tr("Record the arrival of parts in the reception area (neutral impact on stock)."))
        info_label.setWordWrap(True)
        info_label.setStyleSheet("QLabel { color: #666; margin-bottom: 10px; }")
        layout.addWidget(info_label)
        
        # Informations principales
        main_group = QGroupBox(self.tr("Reception Information"))
        main_layout = QFormLayout()
        
        # Pièce
        self.piece_combo = QComboBox()
        self.piece_combo.setEditable(True)
        main_layout.addRow(self.tr("Part:"), self.piece_combo)
        
        # Quantité
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 999999)
        self.quantity_spin.setValue(1)
        main_layout.addRow(self.tr("Quantity received:"), self.quantity_spin)
        
        # Date et heure
        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setDateTime(QDateTime.currentDateTime())
        self.datetime_edit.setCalendarPopup(True)
        main_layout.addRow(self.tr("Reception Date/Time:"), self.datetime_edit)
        
        main_group.setLayout(main_layout)
        layout.addWidget(main_group)
        
        # Zone de réception (optionnelle)
        location_group = QGroupBox(self.tr("Reception Area"))
        location_layout = QFormLayout()
        
        self.location_combo = QComboBox()
        location_layout.addRow(self.tr("Reception location:"), self.location_combo)
        
        location_group.setLayout(location_layout)
        layout.addWidget(location_group)
        
        # Informations financières
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
        additional_group = QGroupBox(self.tr("Additional Information"))
        additional_layout = QFormLayout()
        
        # Référence document
        self.reference_edit = QLineEdit()
        self.reference_edit.setPlaceholderText(self.tr("Delivery note, invoice, etc."))
        additional_layout.addRow(self.tr("Document reference:"), self.reference_edit)
        
        # Commentaire
        self.comment_edit = QTextEdit()
        self.comment_edit.setMaximumHeight(80)
        self.comment_edit.setPlaceholderText(self.tr("Comment about the reception..."))
        additional_layout.addRow(self.tr("Comment:"), self.comment_edit)
        
        additional_group.setLayout(additional_layout)
        layout.addWidget(additional_group)
        
        # Boutons
        self.create_buttons(layout)
        
        self.setLayout(layout)

    def create_buttons(self, layout):
        """Crée les boutons"""
        btn_layout = QHBoxLayout()
        
        self.validate_btn = QPushButton(self.tr("Validate Reception"))
        self.validate_btn.setStyleSheet("QPushButton { background-color: #9C27B0; color: white; }")
        self.cancel_btn = QPushButton(self.tr("Cancel"))
        
        btn_layout.addWidget(self.validate_btn)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)

    def setup_connections(self):
        """Configure les connexions de signaux"""
        self.validate_btn.clicked.connect(self.validate)
        self.cancel_btn.clicked.connect(self.reject)
        
        if hasattr(self, 'piece_combo'):
            self.piece_combo.currentTextChanged.connect(self.on_piece_changed)

    def load_data(self):
        """Charge les données dans les combobox"""
        # Charger les pièces
        if hasattr(self, 'piece_combo'):
            self.piece_combo.clear()
            self.piece_combo.addItem(self.tr("Select a part..."), None)
            
            for piece in self.pieces:
                text = f"{piece['reference']} - {piece['nom']} (Stock: {piece.get('stock_actuel', 0)})"
                self.piece_combo.addItem(text, piece)
        
        # Charger les emplacements
        if hasattr(self, 'location_combo'):
            self.location_combo.clear()
            self.location_combo.addItem(self.tr("General reception area"), None)
            for emplacement in self.emplacements:
                text = f"{emplacement['nom']}"
                if emplacement.get('allee'):
                    text += f" - {emplacement['allee']}"
                self.location_combo.addItem(text, emplacement)

    def on_piece_changed(self):
        """Gère le changement de pièce sélectionnée"""
        # Pourrait être utilisé pour charger des infos spécifiques
        pass

    def validate(self):
        """Valide et ferme le dialog"""
        # Validation des données
        if not self.piece_combo.currentData():
            QMessageBox.warning(self, self.tr("Validation"), 
                              self.tr("Please select a part."))
            return
        
        if self.quantity_spin.value() <= 0:
            QMessageBox.warning(self, self.tr("Validation"), 
                              self.tr("Quantity must be positive."))
            return
        self.accept()

    def get_data(self):
        """Retourne les données saisies"""
        piece_data = self.piece_combo.currentData()
        location_data = self.location_combo.currentData()
        
        return {
            'piece_id': piece_data['id_piece'] if piece_data else None,
            'quantite': self.quantity_spin.value(),
            'emplacement_reception_id': location_data['id'] if location_data else None,
            'cout_unitaire': self.unit_cost_spin.value(),
            'reference': self.reference_edit.text().strip(),
            'commentaire': self.comment_edit.toPlainText().strip()
        }
