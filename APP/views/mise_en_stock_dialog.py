from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QComboBox, QSpinBox, QLineEdit, QTextEdit,
                             QPushButton, QLabel, QGroupBox, QDateTimeEdit, QMessageBox)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QFont
from typing import List, Dict, Optional

class MiseEnStockDialog(QDialog):
    """Dialog pour la mise en stock depuis la réception"""
    
    def __init__(self, parent=None, pieces: List[Dict] = None, emplacements: List[Dict] = None):
        super().__init__(parent)
        self.pieces = pieces or []
        self.emplacements = emplacements or []
        
        self.setup_ui()
        self.setup_connections()
        self.load_data()

    def setup_ui(self):
        """Configure l'interface utilisateur"""
        self.setModal(True)
        self.setWindowTitle(self.tr("Mise en Stock"))
        self.resize(500, 500)
        
        layout = QVBoxLayout()
        
        # Titre et description
        title_label = QLabel(self.tr("Mise en Stock"))
        title_label.setFont(QFont("", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        info_label = QLabel(self.tr("Transfère les pièces de la zone de réception vers leur emplacement de stockage définitif."))
        info_label.setWordWrap(True)
        info_label.setStyleSheet("QLabel { color: #666; margin-bottom: 10px; }")
        layout.addWidget(info_label)
        
        # Informations principales
        main_group = QGroupBox(self.tr("Informations de Mise en Stock"))
        main_layout = QFormLayout()
        
        # Pièce
        self.piece_combo = QComboBox()
        self.piece_combo.setEditable(True)
        main_layout.addRow(self.tr("Pièce:"), self.piece_combo)
        
        # Quantité
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 999999)
        self.quantity_spin.setValue(1)
        main_layout.addRow(self.tr("Quantité à stocker:"), self.quantity_spin)
        
        # Date et heure
        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setDateTime(QDateTime.currentDateTime())
        self.datetime_edit.setCalendarPopup(True)
        main_layout.addRow(self.tr("Date/Heure stockage:"), self.datetime_edit)
        
        main_group.setLayout(main_layout)
        layout.addWidget(main_group)
        
        # Emplacements
        location_group = QGroupBox(self.tr("Emplacements"))
        location_layout = QFormLayout()
        
        # Source (réception)
        self.source_location_combo = QComboBox()
        location_layout.addRow(self.tr("Depuis (réception):"), self.source_location_combo)
        
        # Destination (stockage final)
        self.dest_location_combo = QComboBox()
        location_layout.addRow(self.tr("Vers (stockage final):"), self.dest_location_combo)
        
        location_group.setLayout(location_layout)
        layout.addWidget(location_group)
        
        # Informations complémentaires
        additional_group = QGroupBox(self.tr("Informations Complémentaires"))
        additional_layout = QFormLayout()
        
        # Référence document
        self.reference_edit = QLineEdit()
        self.reference_edit.setPlaceholderText(self.tr("Référence de rangement, etc."))
        additional_layout.addRow(self.tr("Référence document:"), self.reference_edit)
        
        # Commentaire
        self.comment_edit = QTextEdit()
        self.comment_edit.setMaximumHeight(80)
        self.comment_edit.setPlaceholderText(self.tr("Commentaire sur la mise en stock..."))
        additional_layout.addRow(self.tr("Commentaire:"), self.comment_edit)
        
        additional_group.setLayout(additional_layout)
        layout.addWidget(additional_group)
        
        # Boutons
        self.create_buttons(layout)
        
        self.setLayout(layout)

    def create_buttons(self, layout):
        """Crée les boutons"""
        btn_layout = QHBoxLayout()
        
        self.validate_btn = QPushButton(self.tr("Valider Mise en Stock"))
        self.validate_btn.setStyleSheet("QPushButton { background-color: #673AB7; color: white; }")
        self.cancel_btn = QPushButton(self.tr("Annuler"))
        
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
            self.piece_combo.addItem(self.tr("Sélectionner une pièce..."), None)
            
            for piece in self.pieces:
                text = f"{piece['reference']} - {piece['nom']} (Stock: {piece.get('stock_actuel', 0)})"
                self.piece_combo.addItem(text, piece)
        
        # Charger les emplacements sources (réception)
        if hasattr(self, 'source_location_combo'):
            self.source_location_combo.clear()
            self.source_location_combo.addItem(self.tr("Zone de réception générale"), None)
            for emplacement in self.emplacements:
                # Filtrer pour ne montrer que les zones de réception ou générales
                if 'reception' in emplacement.get('nom', '').lower() or 'general' in emplacement.get('nom', '').lower():
                    text = f"{emplacement['nom']}"
                    if emplacement.get('allee'):
                        text += f" - {emplacement['allee']}"
                    self.source_location_combo.addItem(text, emplacement)
        
        # Charger les emplacements destination (stockage)
        if hasattr(self, 'dest_location_combo'):
            self.dest_location_combo.clear()
            self.dest_location_combo.addItem(self.tr("Sélectionner un emplacement..."), None)
            for emplacement in self.emplacements:
                text = f"{emplacement['nom']}"
                if emplacement.get('allee'):
                    text += f" - {emplacement['allee']}"
                self.dest_location_combo.addItem(text, emplacement)    
    def on_piece_changed(self):
        """Gère le changement de pièce sélectionnée"""
        # Pourrait être utilisé pour charger l'emplacement préférentiel de la pièce
        pass

    def validate(self):
        """Valide et ferme le dialog"""
        # Validation des données
        if not self.piece_combo.currentData():
            QMessageBox.warning(self, self.tr("Validation"), 
                              self.tr("Veuillez sélectionner une pièce."))
            return
        
        if self.quantity_spin.value() <= 0:
            QMessageBox.warning(self, self.tr("Validation"), 
                              self.tr("La quantité doit être positive."))
            return
        
        if not self.dest_location_combo.currentData():
            QMessageBox.warning(self, self.tr("Validation"), 
                              self.tr("Veuillez sélectionner un emplacement de destination."))
            return
        
        self.accept()

    def get_data(self):
        """Retourne les données saisies"""
        piece_data = self.piece_combo.currentData()
        dest_data = self.dest_location_combo.currentData()
        
        return {
            'piece_id': piece_data['id_piece'] if piece_data else None,
            'quantite': self.quantity_spin.value(),
            'emplacement_stockage_id': dest_data['id_emplacement'] if dest_data else None,
            'reference': self.reference_edit.text().strip(),
            'commentaire': self.comment_edit.toPlainText().strip()
        }
