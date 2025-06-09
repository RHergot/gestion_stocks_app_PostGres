from PySide6.QtWidgets import (QDialog, QFormLayout, QLineEdit, QPushButton, QHBoxLayout, 
                             QSpinBox, QMessageBox, QDoubleSpinBox, QTextEdit, QLabel,
                             QGroupBox, QVBoxLayout, QTabWidget, QWidget, QTableWidget,
                             QTableWidgetItem, QHeaderView, QAbstractItemView, QSizePolicy, QComboBox)
from PySide6.QtCore import Qt, QTimer

class EmplacementDialog(QDialog):
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self.emplacement_id = None
        self.setWindowTitle(self.tr("Location"))
        self.setMinimumWidth(500)
        self.setMinimumHeight(600)
        self.setWindowFlags(Qt.Window) # Ensure standard window appearance
        
        
        # Layout principal avec onglets
        main_layout = QVBoxLayout(self)
        
        # Créer les onglets
        self.tab_widget = QTabWidget()
        
        # Onglet 1: Informations de base
        self.create_basic_info_tab()
        
        # Onglet 2: Dimensions physiques
        self.create_dimensions_tab()
        
        # Onglet 3: Conditions de stockage
        self.create_conditions_tab()

        # Onglet 4: Stock Pièces
        self.create_stock_tab()

        main_layout.addWidget(self.tab_widget)
        
        # Boutons
        btns = QHBoxLayout()
        self.ok_btn = QPushButton(self.tr("OK"), self)
        self.cancel_btn = QPushButton(self.tr("Cancel"), self)
        btns.addWidget(self.ok_btn)
        btns.addWidget(self.cancel_btn)
        main_layout.addLayout(btns)
        
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def create_basic_info_tab(self):
        """Crée l'onglet des informations de base"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Champs existants
        self.magasin_id = QSpinBox(self)
        self.magasin_id.setMinimum(1)
        
        self.nom = QLineEdit(self)
        self.nom.setReadOnly(True)
        
        self.type = QComboBox(self)
        self.emplacement_types = ["stock", "reception", "expedition", "controle_qualite", "reserve", "production"]
        self.type.addItems(self.emplacement_types)
        # Set default to 'stock'
        try:
            default_type_index = self.emplacement_types.index("stock")
            self.type.setCurrentIndex(default_type_index)
        except ValueError:
            print("Warning: Default emplacement type 'stock' not found in list. Setting to first item.")
            if self.emplacement_types:
                self.type.setCurrentIndex(0)
        
        self.allee = QSpinBox(self)
        self.allee.setMinimum(0)
        
        self.etagere = QSpinBox(self)
        self.etagere.setMinimum(0)
        
        self.niveau = QSpinBox(self)
        self.niveau.setMinimum(0)
        
        layout.addRow(self.tr("Warehouse ID"), self.magasin_id)
        layout.addRow(self.tr("Name (auto)"), self.nom)
        layout.addRow(self.tr("Type"), self.type)
        layout.addRow(self.tr("Aisle"), self.allee)
        layout.addRow(self.tr("Shelf"), self.etagere)
        layout.addRow(self.tr("Level"), self.niveau)
        
        # Mise à jour auto du nom
        self.allee.valueChanged.connect(self.update_nom_auto)
        self.etagere.valueChanged.connect(self.update_nom_auto)
        self.niveau.valueChanged.connect(self.update_nom_auto)
        self.update_nom_auto()
        
        self.tab_widget.addTab(tab, self.tr("Basic Info"))

    def create_dimensions_tab(self):
        """Crée l'onglet des dimensions physiques"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Dimensions
        self.longueur_cm = QDoubleSpinBox(self)
        self.longueur_cm.setRange(0.1, 10000.0)
        self.longueur_cm.setDecimals(1)
        self.longueur_cm.setSuffix(" cm")
        self.longueur_cm.setValue(100.0)
        
        self.hauteur_cm = QDoubleSpinBox(self)
        self.hauteur_cm.setRange(0.1, 10000.0)
        self.hauteur_cm.setDecimals(1)
        self.hauteur_cm.setSuffix(" cm")
        self.hauteur_cm.setValue(50.0)
        
        self.profondeur_cm = QDoubleSpinBox(self)
        self.profondeur_cm.setRange(0.1, 10000.0)
        self.profondeur_cm.setDecimals(1)
        self.profondeur_cm.setSuffix(" cm")
        self.profondeur_cm.setValue(30.0)
        
        # Volume calculé automatiquement
        self.volume_label = QLabel("0 cm³")
        self.volume_label.setStyleSheet("QLabel { font-weight: bold; color: blue; }")
        
        # Capacité maximale
        self.capacite_max_kg = QDoubleSpinBox(self)
        self.capacite_max_kg.setRange(0.0, 100000.0)
        self.capacite_max_kg.setDecimals(1)
        self.capacite_max_kg.setSuffix(" kg")
        self.capacite_max_kg.setValue(50.0)
        
        layout.addRow(self.tr("Length"), self.longueur_cm)
        layout.addRow(self.tr("Height"), self.hauteur_cm)
        layout.addRow(self.tr("Depth"), self.profondeur_cm)
        layout.addRow(self.tr("Volume (calculated)"), self.volume_label)
        layout.addRow(self.tr("Max Capacity"), self.capacite_max_kg)
        
        # Connexions pour le calcul automatique du volume
        self.longueur_cm.valueChanged.connect(self.update_volume)
        self.hauteur_cm.valueChanged.connect(self.update_volume)
        self.profondeur_cm.valueChanged.connect(self.update_volume)
        self.update_volume()
        
        self.tab_widget.addTab(tab, self.tr("Dimensions"))

    def create_conditions_tab(self):
        """Crée l'onglet des conditions de stockage"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Température
        self.temperature_min_c = QDoubleSpinBox(self)
        self.temperature_min_c.setRange(-50.0, 100.0)
        self.temperature_min_c.setDecimals(1)
        self.temperature_min_c.setSuffix(" °C")
        self.temperature_min_c.setValue(15.0)
        
        self.temperature_max_c = QDoubleSpinBox(self)
        self.temperature_max_c.setRange(-50.0, 100.0)
        self.temperature_max_c.setDecimals(1)
        self.temperature_max_c.setSuffix(" °C")
        self.temperature_max_c.setValue(25.0)
        
        # Humidité
        self.humidite_max_pct = QDoubleSpinBox(self)
        self.humidite_max_pct.setRange(0.0, 100.0)
        self.humidite_max_pct.setDecimals(1)
        self.humidite_max_pct.setSuffix(" %")
        self.humidite_max_pct.setValue(70.0)
        
        # Conditions spéciales
        self.conditions_speciales = QTextEdit(self)
        self.conditions_speciales.setMaximumHeight(100)
        self.conditions_speciales.setPlaceholderText(
            self.tr("Special storage conditions (e.g., ventilation, lighting, security...)")
        )
        
        layout.addRow(self.tr("Min Temperature"), self.temperature_min_c)
        layout.addRow(self.tr("Max Temperature"), self.temperature_max_c)
        layout.addRow(self.tr("Max Humidity"), self.humidite_max_pct)
        layout.addRow(self.tr("Special Conditions"), self.conditions_speciales)
        
        self.tab_widget.addTab(tab, self.tr("Storage Conditions"))

    def create_stock_tab(self):
        """Crée l'onglet pour afficher le stock de pièces dans l'emplacement"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.stock_table = QTableWidget(self)
        self.stock_table.setColumnCount(2) # Pièce, Quantité
        self.stock_table.setHorizontalHeaderLabels([self.tr("Piece"), self.tr("Quantity")])
        self.stock_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.stock_table.setEditTriggers(QAbstractItemView.NoEditTriggers) # Read-only
        self.stock_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.stock_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.addWidget(self.stock_table)
        self.tab_widget.addTab(tab, self.tr("Stocked Parts"))

    def load_stock_data(self):
        """Charge et affiche les pièces stockées dans l'emplacement actuel en utilisant EmplacementExtService."""
        if not hasattr(self, 'stock_table'):
            return # Si la table n'est pas encore créée, ne rien faire

        self.stock_table.setRowCount(0) # Vider la table avant de charger de nouvelles données

        if not self.emplacement_id or not self.db:
            return

        try:
            from APP.services.emplacement_ext_service import EmplacementExtService
            service = EmplacementExtService(self.db)
            
            # Utiliser get_emplacement_complet pour obtenir toutes les données, y compris le stock
            emplacement_data = service.get_emplacement_complet(self.emplacement_id)
            
            stock_items = emplacement_data.get('stock_items', [])

            self.stock_table.setRowCount(len(stock_items))
            for row, item_data in enumerate(stock_items):
                # Utiliser les clés confirmées : 'piece_reference' et 'quantite'
                # Si 'piece_reference' n'est pas le nom souhaité, il faudra l'ajuster
                # ou s'assurer que la vue v_stock_par_emplacement contient une colonne 'piece_nom'.
                piece_ref = item_data.get('piece_reference', self.tr('Unknown Piece'))
                quantite_val = item_data.get('quantite', 0)
                
                self.stock_table.setItem(row, 0, QTableWidgetItem(str(piece_ref)))
                self.stock_table.setItem(row, 1, QTableWidgetItem(str(quantite_val)))

        except ImportError as e_import:
            print(f"Erreur d'importation pour EmplacementExtService: {e_import}")
            QMessageBox.critical(self, self.tr("Import Error"), self.tr("Could not load a required component to display stock data."))
        except Exception as e:
            print(f"Erreur lors du chargement du stock pour l'emplacement {self.emplacement_id}: {e}")
            QMessageBox.critical(self, self.tr("Error"), self.tr("Could not load stock data: {error_message}").format(error_message=str(e)))
            self.stock_table.setRowCount(0) # Assurer que la table est vide en cas d'erreur majeure

    def update_nom_auto(self):
        """Met à jour automatiquement le nom de l'emplacement"""
        nom = f"A{self.allee.value()}S{self.etagere.value()}L{self.niveau.value()}"
        self.nom.setText(nom)

    def update_volume(self):
        """Met à jour le calcul du volume"""
        try:
            longueur = self.longueur_cm.value()
            hauteur = self.hauteur_cm.value()
            profondeur = self.profondeur_cm.value()
            volume = longueur * hauteur * profondeur
            
            if volume >= 1000000:  # >= 1m³
                volume_str = f"{volume/1000000:.2f} m³"
            elif volume >= 1000:  # >= 1L
                volume_str = f"{volume/1000:.1f} L"
            else:
                volume_str = f"{volume:.0f} cm³"
            self.volume_label.setText(volume_str)
        except Exception as e:
            print(f"Error calculating volume: {e}")
            self.volume_label.setText("Error cm³")

    def validate_data(self):
        """Valide les données saisies"""
        errors = []
        
        # Validation des dimensions
        if self.longueur_cm.value() <= 0:
            errors.append(self.tr("Length must be positive"))
        if self.hauteur_cm.value() <= 0:
            errors.append(self.tr("Height must be positive"))
        if self.profondeur_cm.value() <= 0:
            errors.append(self.tr("Depth must be positive"))
        
        # Validation des températures
        if self.temperature_min_c.value() > self.temperature_max_c.value():
            errors.append(self.tr("Minimum temperature cannot be higher than maximum temperature"))
        
        # Validation de l'humidité
        if self.humidite_max_pct.value() < 0 or self.humidite_max_pct.value() > 100:
            errors.append(self.tr("Humidity must be between 0 and 100%"))
        
        if errors:
            QMessageBox.warning(self, self.tr("Validation Error"), "\n".join(errors))
            return False
        
        return True

    def accept(self):
        """Surcharge pour valider avant d'accepter"""
        if self.validate_data():
            super().accept()

    def get_data(self):
        """Récupère toutes les données du formulaire"""
        self.update_nom_auto()
        
        # Données de base
        base_data = {
            "magasin_id": self.magasin_id.value(),
            "nom": self.nom.text(),
            "type_emplacement": self.type.currentText(),
            "allee": self.allee.value(),
            "etagere": self.etagere.value(),
            "niveau": self.niveau.value()
        }
        
        # Données étendues
        ext_data = {
            "longueur_cm": self.longueur_cm.value(),
            "hauteur_cm": self.hauteur_cm.value(),
            "profondeur_cm": self.profondeur_cm.value(),
            "capacite_max_kg": self.capacite_max_kg.value(),
            "temperature_min_c": self.temperature_min_c.value(),
            "temperature_max_c": self.temperature_max_c.value(),
            "humidite_max_pct": self.humidite_max_pct.value(),
            "conditions_speciales": self.conditions_speciales.toPlainText().strip() or None,
            "actif": True
        }
        
        return {
            "base": base_data,
            "extension": ext_data
        }

    def set_data(self, data):
        """Charge les données dans le formulaire"""
        if data:
            self.emplacement_id = data.get("id")

            # Basic Info Tab
            magasin_id_val = data.get("magasin_id", 1)
            try:
                self.magasin_id.setValue(int(magasin_id_val) if magasin_id_val is not None else 1)
            except (ValueError, TypeError):
                self.magasin_id.setValue(1) # Fallback if conversion fails
            
            # self.nom.setText(data.get("nom", "")) # Nom is auto-generated
            self.type.setCurrentText(data.get("type_emplacement", data.get("type", "stock")))
            
            allee_val = data.get("allee", 0)
            try:
                self.allee.setValue(int(allee_val) if allee_val is not None else 0)
            except (ValueError, TypeError):
                self.allee.setValue(0) # Fallback
                
            etagere_val = data.get("etagere", 0)
            try:
                self.etagere.setValue(int(etagere_val) if etagere_val is not None else 0)
            except (ValueError, TypeError):
                self.etagere.setValue(0) # Fallback
                
            niveau_val = data.get("niveau", 0)
            try:
                self.niveau.setValue(int(niveau_val) if niveau_val is not None else 0)
            except (ValueError, TypeError):
                self.niveau.setValue(0) # Fallback
            
            self.update_nom_auto() # Update name based on aisle, shelf, level

            # Dimensions Tab
            dimensions_data = data.get("dimensions", data) # Check if 'dimensions' key exists, else use root data
            self.longueur_cm.setValue(float(dimensions_data.get("longueur_cm", 100.0)))
            self.hauteur_cm.setValue(float(dimensions_data.get("hauteur_cm", 50.0)))
            self.profondeur_cm.setValue(float(dimensions_data.get("profondeur_cm", 30.0)))
            self.capacite_max_kg.setValue(float(dimensions_data.get("capacite_max_kg", 50.0)))
            self.update_volume() # Update volume display

            # Conditions Tab
            conditions_data = data.get("conditions_stockage", data) # Check if 'conditions_stockage' key exists
            self.temperature_min_c.setValue(float(conditions_data.get("temperature_min_c", 15.0)))
            self.temperature_max_c.setValue(float(conditions_data.get("temperature_max_c", 25.0)))
            self.humidite_max_pct.setValue(float(conditions_data.get("humidite_max_pct", 70.0)))
            self.conditions_speciales.setPlainText(conditions_data.get("conditions_speciales", ""))

            # Stock Tab - Data loaded if emplacement_id is set
            self.load_stock_data()
        else:
            # Reset for a new emplacement
            self.emplacement_id = None
            self.magasin_id.setValue(1)
            self.type.setCurrentText("stock") # Default type
            self.allee.setValue(0)
            self.etagere.setValue(0)
            self.niveau.setValue(0)
            self.update_nom_auto()

            # Default dimensions
            self.longueur_cm.setValue(100.0)
            self.hauteur_cm.setValue(50.0)
            self.profondeur_cm.setValue(30.0)
            self.capacite_max_kg.setValue(50.0)
            self.update_volume()

            # Default conditions
            self.temperature_min_c.setValue(15.0)
            self.temperature_max_c.setValue(25.0)
            self.humidite_max_pct.setValue(70.0)
            self.conditions_speciales.clear()
            
            self.stock_table.setRowCount(0) # Clear stock table for new emplacement

    def load_emplacement_complet(self, emplacement_id: int):
        """Charge un emplacement complet avec ses extensions"""
        if not self.db:
            return
        
        try:
            from APP.services.emplacement_ext_service import EmplacementExtService
            service = EmplacementExtService(self.db)
            emplacement_complet = service.get_emplacement_complet(emplacement_id)
            
            if emplacement_complet:
                self.set_data(emplacement_complet)
            else:
                QMessageBox.warning(self, self.tr("Error"), 
                                  self.tr("Unable to load location data"))
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), 
                               self.tr(f"Error loading location: {e}"))
