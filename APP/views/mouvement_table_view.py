from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QPushButton, QHBoxLayout, QHeaderView, QMessageBox, QDialog, 
                             QMenuBar, QMenu, QDateEdit, QComboBox, QLabel, QLineEdit,
                             QFormLayout, QGroupBox, QSplitter, QTextEdit, QSpinBox)
from PySide6.QtGui import QAction, QFont, QColor
from PySide6.QtCore import Qt, QDate
from APP.controllers.mouvement_controller import MouvementController
from .mouvement_dialog import MouvementDialog
from .reception_workflow_dialog import ReceptionWorkflowDialog
from .mise_en_stock_dialog import MiseEnStockDialog
from datetime import datetime, date

class MouvementTableView(QWidget):
    def __init__(self, mouvement_controller: MouvementController, parent=None):
        super().__init__(parent)
        self.mouvement_controller = mouvement_controller
        self.setWindowTitle(self.tr("Stock Movements"))
        self.resize(1400, 700)
        
        # Layout principal avec splitter
        main_layout = QVBoxLayout()
        splitter = QSplitter(Qt.Horizontal)
        
        # Partie gauche - Liste des mouvements
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Barre de menu
        self.create_menu_bar(left_layout)
        
        # Filtres
        self.create_filters(left_layout)
        
        # Table des mouvements
        self.create_movements_table(left_layout)
        
        # Boutons d'action
        self.create_action_buttons(left_layout)
        
        # Partie droite - Détails et actions rapides
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Actions rapides
        self.create_quick_actions(right_layout)
        
        # Détails du mouvement sélectionné
        self.create_movement_details(right_layout)
        
        # Statistiques
        self.create_statistics_panel(right_layout)
        
        # Ajouter au splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([1000, 400])
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
        
        # Connecter les signaux
        self.connect_signals()
        
        # Charger les données initiales
        self.refresh_data()

    def create_menu_bar(self, layout):
        """Creates the menu bar"""
        self.menu_bar = QMenuBar(self)
        
        # Menu Affichage
        view_menu = self.menu_bar.addMenu(self.tr("View"))
        
        # Tous les mouvements
        all_movements_action = QAction(self.tr("All movements"), self)
        all_movements_action.triggered.connect(self.show_all_movements)
        view_menu.addAction(all_movements_action)
        
        view_menu.addSeparator()
        
        # Mouvements d'entrée
        entries_action = QAction(self.tr("Entries only"), self)
        entries_action.triggered.connect(self.show_entries_only)
        view_menu.addAction(entries_action)
        
        # Mouvements de sortie
        exits_action = QAction(self.tr("Exits only"), self)
        exits_action.triggered.connect(self.show_exits_only)
        view_menu.addAction(exits_action)
        
        # Transferts
        transfers_action = QAction(self.tr("Transfers only"), self)
        transfers_action.triggered.connect(self.show_transfers_only)
        view_menu.addAction(transfers_action)
        
        view_menu.addSeparator()
        
        # Workflow de réception
        reception_action = QAction(self.tr("Reception movements"), self)
        reception_action.triggered.connect(self.show_reception_only)
        view_menu.addAction(reception_action)
        
        # Mouvements neutres (impact = 0)
        neutral_action = QAction(self.tr("Neutral movements"), self)
        neutral_action.triggered.connect(self.show_neutral_only)
        view_menu.addAction(neutral_action)
        
        view_menu.addSeparator()
        
        # Mouvements du jour
        today_action = QAction(self.tr("Today's movements"), self)
        today_action.triggered.connect(self.show_today_movements)
        view_menu.addAction(today_action)
        
        # Menu Rapports
        reports_menu = self.menu_bar.addMenu(self.tr("Reports"))
        
        # Rapport d'activité
        activity_report_action = QAction(self.tr("Activity report"), self)
        activity_report_action.triggered.connect(self.generate_activity_report)
        reports_menu.addAction(activity_report_action)
        
        # Stocks faibles
        low_stock_action = QAction(self.tr("Low stock parts"), self)
        low_stock_action.triggered.connect(self.show_low_stock)
        reports_menu.addAction(low_stock_action)
        
        layout.addWidget(self.menu_bar)

    def create_filters(self, layout):
        """Creates the filters section"""
        filter_group = QGroupBox(self.tr("Filters"))
        filter_layout = QFormLayout()
        
        # Filtre par pièce
        self.piece_filter = QComboBox()
        self.piece_filter.addItem(self.tr("All parts"), None)
        filter_layout.addRow(self.tr("Part:"), self.piece_filter)
        
        # Filtre par type de mouvement
        self.type_filter = QComboBox()
        self.type_filter.addItem(self.tr("All types"), None)
        filter_layout.addRow(self.tr("Type:"), self.type_filter)
        
        # Filtre par date
        date_layout = QHBoxLayout()
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        
        date_layout.addWidget(QLabel(self.tr("From:")))
        date_layout.addWidget(self.date_from)
        date_layout.addWidget(QLabel(self.tr("To:")))
        date_layout.addWidget(self.date_to)
        
        filter_layout.addRow(self.tr("Period:"), date_layout)
        
        # Bouton appliquer filtres
        self.apply_filters_btn = QPushButton(self.tr("Apply filters"))
        self.apply_filters_btn.clicked.connect(self.apply_filters)
        filter_layout.addRow("", self.apply_filters_btn)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

    def create_movements_table(self, layout):
        """Creates the movements table"""
        self.table = QTableWidget(self)
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Date"), self.tr("Part"), self.tr("Type"),
            self.tr("Quantity"), self.tr("Stock Before"), self.tr("Stock After"),
            self.tr("Source location"), self.tr("Dest. location"),
            self.tr("User"), self.tr("Reference"), self.tr("Total cost")
        ])
        
        # Configuration de la table
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        
        layout.addWidget(self.table)

    def create_action_buttons(self, layout):
        """Creates action buttons"""
        btn_layout = QHBoxLayout()
        
        # Boutons traditionnels
        self.new_entry_btn = QPushButton(self.tr("New Entry"))
        self.new_exit_btn = QPushButton(self.tr("New Exit"))
        self.new_transfer_btn = QPushButton(self.tr("New Transfer"))
        self.inventory_btn = QPushButton(self.tr("Inventory Adjustment"))
        self.move_to_waste_btn = QPushButton(self.tr("Move all to Waste"))
        
        # Nouveaux boutons pour workflow de réception
        self.new_reception_btn = QPushButton(self.tr("Receive Parts"))
        self.mise_en_stock_btn = QPushButton(self.tr("Put In Stock"))
        
        # Boutons d'action
        self.cancel_btn = QPushButton(self.tr("Cancel Movement"))
        self.refresh_btn = QPushButton(self.tr("Refresh"))
        self.close_btn = QPushButton(self.tr("Close"))
        
        # Style des boutons traditionnels
        self.new_entry_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        self.new_exit_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        self.new_transfer_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; }")
        self.inventory_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; }")
        self.move_to_waste_btn.setStyleSheet("QPushButton { background-color: #795548; color: white; }")
        
        # Style des nouveaux boutons de workflow réception
        self.new_reception_btn.setStyleSheet("QPushButton { background-color: #9C27B0; color: white; }")
        self.mise_en_stock_btn.setStyleSheet("QPushButton { background-color: #673AB7; color: white; }")
        
        # Style des boutons d'action
        self.cancel_btn.setStyleSheet("QPushButton { background-color: #9E9E9E; color: white; }")
        
        # Première ligne - opérations traditionnelles
        first_row = QHBoxLayout()
        for btn in [self.new_entry_btn, self.new_exit_btn, self.new_transfer_btn, 
                   self.inventory_btn, self.move_to_waste_btn]:
            first_row.addWidget(btn)
        
        # Deuxième ligne - workflow réception + actions
        second_row = QHBoxLayout()
        for btn in [self.new_reception_btn, self.mise_en_stock_btn, 
                   self.cancel_btn, self.refresh_btn, self.close_btn]:
            second_row.addWidget(btn)
        
        btn_layout.addLayout(first_row)
        btn_layout.addLayout(second_row)
        layout.addLayout(btn_layout)

    def create_quick_actions(self, layout):
        """Creates the quick actions panel"""
        quick_group = QGroupBox(self.tr("Quick Actions"))
        quick_layout = QVBoxLayout()
        
        # Entrée rapide
        entry_layout = QFormLayout()
        self.quick_piece_combo = QComboBox()
        self.quick_quantity_spin = QSpinBox()
        self.quick_quantity_spin.setRange(1, 9999)
        self.quick_entry_btn = QPushButton(self.tr("Quick Entry"))
        
        entry_layout.addRow(self.tr("Part:"), self.quick_piece_combo)
        entry_layout.addRow(self.tr("Quantity:"), self.quick_quantity_spin)
        entry_layout.addRow("", self.quick_entry_btn)
        
        quick_layout.addLayout(entry_layout)
        quick_group.setLayout(quick_layout)
        layout.addWidget(quick_group)

    def create_movement_details(self, layout):
        """Creates the movement details panel"""
        details_group = QGroupBox(self.tr("Movement Details"))
        details_layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(200)
        
        details_layout.addWidget(self.details_text)
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)

    def create_statistics_panel(self, layout):
        """Creates the statistics panel"""
        stats_group = QGroupBox(self.tr("Statistics"))
        stats_layout = QVBoxLayout()
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(150)
        
        stats_layout.addWidget(self.stats_text)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

    def connect_signals(self):
        """Connecte les signaux"""
        # Boutons d'action traditionnels
        self.new_entry_btn.clicked.connect(self.new_entry)
        self.new_exit_btn.clicked.connect(self.new_exit)
        self.new_transfer_btn.clicked.connect(self.new_transfer)
        self.inventory_btn.clicked.connect(self.inventory_adjustment)
        self.move_to_waste_btn.clicked.connect(self.move_all_to_waste)
        
        # Nouveaux boutons workflow réception
        self.new_reception_btn.clicked.connect(self.new_reception)
        self.mise_en_stock_btn.clicked.connect(self.mise_en_stock)
        
        # Boutons d'action
        self.cancel_btn.clicked.connect(self.cancel_movement)
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.close_btn.clicked.connect(self.close)
        
        # Action rapide
        self.quick_entry_btn.clicked.connect(self.quick_entry)
        
        # Sélection dans la table
        self.table.itemSelectionChanged.connect(self.on_selection_changed)

    def refresh_data(self):
        """Refreshes data"""
        try:
            # Charger les mouvements
            mouvements = self.mouvement_controller.lister_mouvements()
            self.populate_table(mouvements)
            
            # Charger les données pour les combos
            self.load_combo_data()
            
            # Mettre à jour les statistiques
            self.update_statistics()
            
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), 
                               self.tr(f"Error while loading data: {e}"))

    def populate_table(self, mouvements):
        """Fills the table with movements"""
        self.table.setRowCount(len(mouvements))
        
        for row, mouvement in enumerate(mouvements):
            self.table.setItem(row, 0, QTableWidgetItem(str(mouvement.get('id', ''))))
            
            # Date formatée
            date_str = ""
            if mouvement.get('date_mouvement'):
                if isinstance(mouvement['date_mouvement'], str):
                    date_obj = datetime.fromisoformat(mouvement['date_mouvement'].replace('Z', '+00:00'))
                    date_str = date_obj.strftime('%d/%m/%Y %H:%M')
                else:
                    date_str = mouvement['date_mouvement'].strftime('%d/%m/%Y %H:%M')
            
            self.table.setItem(row, 1, QTableWidgetItem(date_str))
            self.table.setItem(row, 2, QTableWidgetItem(mouvement.get('piece_reference', '')))
            self.table.setItem(row, 3, QTableWidgetItem(mouvement.get('type_mouvement', '')))
            self.table.setItem(row, 4, QTableWidgetItem(str(mouvement.get('quantite', ''))))
            self.table.setItem(row, 5, QTableWidgetItem(str(mouvement.get('stock_avant', ''))))
            self.table.setItem(row, 6, QTableWidgetItem(str(mouvement.get('stock_apres', ''))))
            self.table.setItem(row, 7, QTableWidgetItem(mouvement.get('emplacement_source', '')))
            self.table.setItem(row, 8, QTableWidgetItem(mouvement.get('emplacement_destination', '')))
            self.table.setItem(row, 9, QTableWidgetItem(mouvement.get('utilisateur', '')))
            self.table.setItem(row, 10, QTableWidgetItem(mouvement.get('reference_document', '')))
            
            # Coût total formaté
            cout_total = mouvement.get('cout_total')
            cout_str = f"{cout_total:.2f} €" if cout_total else ""
            self.table.setItem(row, 11, QTableWidgetItem(cout_str))
            
            # Coloration selon le type de mouvement avec transparence 75%
            if mouvement.get('impact_stock') == 1:  # Entrée
                # Vert avec 75% de transparence (alpha = 64 sur 255)
                background_color = QColor(0, 255, 0, 64)  # Vert transparent
                text_color = QColor(0, 0, 0)  # Noir
                for col in range(12):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(background_color)
                        item.setForeground(text_color)
            elif mouvement.get('impact_stock') == -1:  # Sortie
                # Rouge avec 75% de transparence (alpha = 64 sur 255)
                background_color = QColor(255, 0, 0, 64)  # Rouge transparent
                text_color = QColor(0, 0, 0)  # Noir
                for col in range(12):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(background_color)
                        item.setForeground(text_color)
            elif mouvement.get('impact_stock') == 0:  # Neutral (reception)
                # Violet/Magenta avec 75% de transparence (alpha = 64 sur 255)
                background_color = QColor(255, 0, 255, 64)  # Magenta transparent
                text_color = QColor(0, 0, 0)  # Noir
                for col in range(12):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(background_color)
                        item.setForeground(text_color)

    def load_combo_data(self):
        """Loads data for comboboxes"""
        try:
            # Charger les pièces
            pieces = self.mouvement_controller.obtenir_pieces_disponibles()
            self.piece_filter.clear()
            self.piece_filter.addItem(self.tr("All parts"), None)
            self.quick_piece_combo.clear()
            
            for piece in pieces:
                text = f"{piece['reference']} - {piece['nom']}"
                self.piece_filter.addItem(text, piece['id_piece'])
                self.quick_piece_combo.addItem(text, piece['id_piece'])
            
            # Charger les types de mouvement
            types = self.mouvement_controller.obtenir_types_mouvement()
            self.type_filter.clear()
            self.type_filter.addItem(self.tr("Tous les types"), None)
            
            for type_mouvement in types:
                self.type_filter.addItem(type_mouvement['nom'], type_mouvement['id'])
                
        except Exception as e:
            QMessageBox.warning(self, self.tr("Warning"), 
                              self.tr(f"Error while loading reference data: {e}"))

    def update_statistics(self):
        """Updates statistics"""
        try:
            # Statistiques générales
            today = date.today()
            rapport = self.mouvement_controller.generer_rapport_activite(today, today)
            
            if rapport['success']:
                stats = rapport['rapport']
                stats_text = f"""
<b>Today's statistics:</b><br>
• Total movements: {stats['total_mouvements']}<br>
• Entries: {stats['total_entrees']} ({stats['quantite_entree_totale']} units)<br>
• Exits: {stats['total_sorties']} ({stats['quantite_sortie_totale']} units)<br>
• Total value: {stats['valeur_totale']:.2f} €
                """
                self.stats_text.setHtml(stats_text)
            
        except Exception as e:
            self.stats_text.setText(f"Error while computing statistics: {e}")

    def on_selection_changed(self):
        """Handles table selection changes"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            mouvement_id = self.table.item(current_row, 0).text()
            if mouvement_id:
                try:
                    mouvement = self.mouvement_controller.obtenir_mouvement(int(mouvement_id))
                    if mouvement:
                        self.show_movement_details(mouvement)
                except Exception as e:
                    self.details_text.setText(f"Error while loading details: {e}")

    def show_movement_details(self, mouvement):
        """Displays details of a movement"""
        details_html = f"""
<b>Movement #{mouvement['id']}</b><br>
<b>Date:</b> {mouvement.get('date_mouvement', 'N/A')}<br>
<b>Part:</b> {mouvement.get('piece_reference', '')} - {mouvement.get('piece_nom', '')}<br>
<b>Type:</b> {mouvement.get('type_mouvement_nom', '')}<br>
<b>Quantity:</b> {mouvement.get('quantite', '')} units<br>
<b>Stock before:</b> {mouvement.get('stock_avant', '')}<br>
<b>Stock after:</b> {mouvement.get('stock_apres', '')}<br>
<b>Source location:</b> {mouvement.get('emplacement_source_nom', 'N/A')}<br>
<b>Destination location:</b> {mouvement.get('emplacement_destination_nom', 'N/A')}<br>
<b>User:</b> {mouvement.get('utilisateur_nom', 'N/A')}<br>
<b>Reference:</b> {mouvement.get('reference_document', 'N/A')}<br>
<b>Unit cost:</b> {mouvement.get('cout_unitaire', 'N/A')}<br>
<b>Total cost:</b> {mouvement.get('cout_total', 'N/A')}<br>
<b>Comment:</b> {mouvement.get('commentaire', 'N/A')}
        """
        self.details_text.setHtml(details_html)

    # === Actions des menus ===

    def show_all_movements(self):
        """Shows all movements"""
        self.refresh_data()

    def show_entries_only(self):
        """Shows entries only"""
        try:
            mouvements = self.mouvement_controller.lister_mouvements()
            entrees = [m for m in mouvements if m.get('impact_stock') == 1]
            self.populate_table(entrees)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), str(e))

    def show_exits_only(self):
        """Shows exits only"""
        try:
            mouvements = self.mouvement_controller.lister_mouvements()
            sorties = [m for m in mouvements if m.get('impact_stock') == -1]
            self.populate_table(sorties)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), str(e))

    def show_reception_only(self):
        """Shows reception movements only"""
        try:
            mouvements = self.mouvement_controller.lister_mouvements()
            receptions = [m for m in mouvements 
                         if any(keyword in m.get('type_mouvement', '') 
                               for keyword in ['RECEPTION', 'MISE_EN_STOCK', 'SORTIE_RECEPTION', 'RETOUR_RECEPTION'])]
            self.populate_table(receptions)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), str(e))
    
    def show_neutral_only(self):
        """Shows neutral movements only (impact = 0)"""
        try:
            mouvements = self.mouvement_controller.lister_mouvements()
            neutres = [m for m in mouvements if m.get('impact_stock') == 0]
            self.populate_table(neutres)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), str(e))

    def show_transfers_only(self):
        """Shows transfers only"""
        try:
            mouvements = self.mouvement_controller.lister_mouvements()
            transferts = [m for m in mouvements if 'TRANSFERT' in m.get('type_mouvement', '')]
            self.populate_table(transferts)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), str(e))

    def show_today_movements(self):
        """Shows today's movements"""
        try:
            today = date.today()
            filtres = {'date_debut': today, 'date_fin': today}
            mouvements = self.mouvement_controller.lister_mouvements(filtres)
            self.populate_table(mouvements)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), str(e))

    def apply_filters(self):
        """Applies selected filters"""
        try:
            filtres = {}
            
            # Filtre par pièce
            piece_id = self.piece_filter.currentData()
            if piece_id:
                filtres['piece_id'] = piece_id
            
            # Filtre par date
            date_debut = self.date_from.date().toPython()
            date_fin = self.date_to.date().toPython()
            filtres['date_debut'] = date_debut
            filtres['date_fin'] = date_fin
            
            mouvements = self.mouvement_controller.lister_mouvements(filtres)
            self.populate_table(mouvements)
            
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), str(e))

    # === Actions des boutons ===

    def new_entry(self):
        """New stock entry"""
        try:
            pieces = self.mouvement_controller.obtenir_pieces_disponibles()
            types_entree = self.mouvement_controller.obtenir_types_mouvement('entree')
            emplacements = self.mouvement_controller.obtenir_emplacements_disponibles()
            
            dialog = MouvementDialog(self, 'entree', pieces, types_entree, emplacements)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                result = self.mouvement_controller.effectuer_entree_stock(**data)
                
                if result['success']:
                    QMessageBox.information(self, self.tr("Success"), result['message'])
                    self.refresh_data()
                else:
                    QMessageBox.critical(self, self.tr("Error"), result['message'])
                    
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), str(e))

    def new_exit(self):
        """New stock exit"""
        try:
            pieces = self.mouvement_controller.obtenir_pieces_disponibles()
            types_sortie = self.mouvement_controller.obtenir_types_mouvement('sortie')
            emplacements = self.mouvement_controller.obtenir_emplacements_disponibles()
            
            dialog = MouvementDialog(self, 'sortie', pieces, types_sortie, emplacements)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                result = self.mouvement_controller.effectuer_sortie_stock(**data)
                
                if result['success']:
                    QMessageBox.information(self, self.tr("Success"), result['message'])
                    self.refresh_data()
                else:
                    QMessageBox.critical(self, self.tr("Error"), result['message'])
                    
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), str(e))

    def new_transfer(self):
        """New transfer"""
        try:
            pieces = self.mouvement_controller.obtenir_pieces_disponibles()
            emplacements = self.mouvement_controller.obtenir_emplacements_disponibles()
            
            dialog = MouvementDialog(self, 'transfert', pieces, [], emplacements)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                result = self.mouvement_controller.effectuer_transfert(**data)
                
                if result['success']:
                    QMessageBox.information(self, self.tr("Success"), result['message'])
                    self.refresh_data()
                else:
                    QMessageBox.critical(self, self.tr("Error"), result['message'])
                    
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), str(e))

    def inventory_adjustment(self):
        """Inventory adjustment"""
        try:
            pieces = self.mouvement_controller.obtenir_pieces_disponibles()
            
            dialog = MouvementDialog(self, 'inventaire', pieces, [], [])
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                result = self.mouvement_controller.effectuer_ajustement_inventaire(**data)
                
                if result['success']:
                    QMessageBox.information(self, self.tr("Success"), result['message'])
                    self.refresh_data()
                else:
                    QMessageBox.critical(self, self.tr("Error"), result['message'])
                    
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), str(e))

    def cancel_movement(self):
        """Cancels a selected movement"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, self.tr("No selection"), 
                              self.tr("Please select a movement to cancel."))
            return
        
        mouvement_id = int(self.table.item(current_row, 0).text())
        
        reply = QMessageBox.question(self, self.tr("Confirmation"), 
                                   self.tr("Are you sure you want to cancel this movement?"),
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                result = self.mouvement_controller.annuler_mouvement(mouvement_id)
                
                if result['success']:
                    QMessageBox.information(self, self.tr("Success"), result['message'])
                    self.refresh_data()
                else:
                    QMessageBox.critical(self, self.tr("Error"), result['message'])
                    
            except Exception as e:
                QMessageBox.critical(self, self.tr("Error"), str(e))

    def quick_entry(self):
        """Quick entry"""
        piece_id = self.quick_piece_combo.currentData()
        quantite = self.quick_quantity_spin.value()
        
        if not piece_id:
            QMessageBox.warning(self, self.tr("Selection required"), 
                              self.tr("Please select a part."))
            return
        
        try:
            result = self.mouvement_controller.effectuer_entree_stock(
                piece_id=piece_id,
                quantite=quantite,
                type_mouvement='ENTREE_ACHAT',
                commentaire='Quick entry'
            )
            
            if result['success']:
                QMessageBox.information(self, self.tr("Success"), result['message'])
                self.refresh_data()
                self.quick_quantity_spin.setValue(1)
            else:
                QMessageBox.critical(self, self.tr("Error"), result['message'])
                
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), str(e))

    def generate_activity_report(self):
        """Generates an activity report"""
        # TODO: Implémenter la génération de rapport
        QMessageBox.information(self, self.tr("Information"), 
                              self.tr("Report feature to be implemented"))

    def show_low_stock(self):
        """Shows a simple report of parts with low stock"""
        try:
            result = self.mouvement_controller.obtenir_pieces_stock_faible()
            if result.get('success'):
                pieces = result.get('pieces', []) or []
                if not pieces:
                    QMessageBox.information(self, self.tr("Low stock"), self.tr("No low stock parts."))
                    return

                # Build a concise list (limit to first 50 items for readability)
                lines = []
                for p in pieces[:50]:
                    ref = p.get('reference', '')
                    nom = p.get('nom', '')
                    stock = p.get('stock_actuel') if p.get('stock_actuel') is not None else p.get('stock', '')
                    seuil = p.get('seuil_alerte') if p.get('seuil_alerte') is not None else p.get('seuil', '')
                    lines.append(f"- {ref} - {nom}: {stock} (threshold: {seuil})")

                details = "<br>".join(lines)
                header = self.tr(f"{len(pieces)} part(s) with low stock:")
                QMessageBox.information(self, self.tr("Low stock parts"), f"{header}<br><br>{details}")
            else:
                QMessageBox.critical(self, self.tr("Error"), result.get('error', 'Unknown error'))
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), str(e))

    # === Reception Workflow ===
    def new_reception(self):
        """New parts reception"""
        try:
            pieces = self.mouvement_controller.obtenir_pieces_disponibles()
            types_reception = self.mouvement_controller.obtenir_types_mouvement('neutre')
            emplacements = self.mouvement_controller.obtenir_emplacements_disponibles()
            
            dialog = ReceptionWorkflowDialog(self, pieces, types_reception, emplacements)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                result = self.mouvement_controller.effectuer_reception_achat(**data)
                
                if result['success']:
                    QMessageBox.information(self, self.tr("Success"), 
                                          self.tr(f"Reception completed: {result['message']}"))
                    self.refresh_data()
                else:
                    QMessageBox.critical(self, self.tr("Error"), result['message'])
                    
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), 
                               self.tr(f"Error during reception: {e}"))

    def mise_en_stock(self):
        """Put in stock from reception"""
        try:
            pieces = self.mouvement_controller.obtenir_pieces_disponibles()
            emplacements = self.mouvement_controller.obtenir_emplacements_disponibles()
            
            dialog = MiseEnStockDialog(self, pieces, emplacements)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                result = self.mouvement_controller.effectuer_mise_en_stock(**data)
                
                if result['success']:
                    QMessageBox.information(self, self.tr("Success"), 
                                          self.tr(f"Put in stock completed: {result['message']}"))
                    self.refresh_data()
                else:
                    QMessageBox.critical(self, self.tr("Error"), result['message'])
                    
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), 
                               self.tr(f"Error during put in stock: {e}"))

    # === Move all to Waste ===
    def move_all_to_waste(self):
        """Open a small dialog to select part and destination 'waste' emplacement, then transfer all stock there."""
        try:
            pieces = self.mouvement_controller.obtenir_pieces_disponibles()
            emplacements = self.mouvement_controller.obtenir_emplacements_disponibles()

            dialog = MoveToWasteDialog(self, pieces, emplacements)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                piece_id = data.get('piece_id')
                dest_id = data.get('emplacement_destination_id')
                if not piece_id or not dest_id:
                    QMessageBox.warning(self, self.tr("Validation"), self.tr("Please select a part and a destination location."))
                    return
                result = self.mouvement_controller.transferer_tout_vers_emplacement(
                    piece_id=piece_id,
                    emplacement_destination_id=dest_id,
                    commentaire='Move all stock to Waste')
                if result.get('success'):
                    count = result.get('count', 0)
                    QMessageBox.information(self, self.tr("Success"), self.tr(f"Moved from {count} location(s) to Waste."))
                    self.refresh_data()
                else:
                    QMessageBox.critical(self, self.tr("Error"), result.get('message', 'Error during transfer'))
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), self.tr(f"Error during move to waste: {e}"))

class MoveToWasteDialog(QDialog):
    def __init__(self, parent, pieces, emplacements):
        super().__init__(parent)
        self.pieces = pieces or []
        self.emplacements = emplacements or []
        self.setWindowTitle(self.tr("Move all stock to Waste"))
        self.resize(480, 220)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Part selection
        self.piece_combo = QComboBox()
        self.piece_combo.addItem(self.tr("Select a part..."), None)
        for p in self.pieces:
            text = f"{p['reference']} - {p['nom']} (Stock: {p.get('stock_actuel', 0)})"
            self.piece_combo.addItem(text, p['id_piece'])
        form.addRow(self.tr("Part:"), self.piece_combo)

        # Destination emplacement selection (prefilter)
        self.dest_combo = QComboBox()
        candidates = self._filter_waste_candidates(self.emplacements)
        self.dest_combo.addItem(self.tr("Select destination..."), None)
        for e in candidates:
            label = e['nom']
            if e.get('allee'):
                label += f" - {e['allee']}"
            self.dest_combo.addItem(label, e['id'])
        form.addRow(self.tr("Destination location:"), self.dest_combo)

        layout.addLayout(form)

        btns = QHBoxLayout()
        self.ok_btn = QPushButton(self.tr("Validate"))
        self.cancel_btn = QPushButton(self.tr("Cancel"))
        self.ok_btn.clicked.connect(self._on_validate)
        self.cancel_btn.clicked.connect(self.reject)
        btns.addStretch(1)
        btns.addWidget(self.ok_btn)
        btns.addWidget(self.cancel_btn)
        layout.addLayout(btns)

        # Preselect first candidate if any
        if candidates:
            self.dest_combo.setCurrentIndex(1)

    def _filter_waste_candidates(self, emplacements):
        """Return emplacements whose name looks like waste/poubelle/dechet (case-insensitive)."""
        needles = ['waste', 'poubelle', 'déchet', 'dechet', 'scrap']
        result = []
        for e in emplacements:
            name = (e.get('nom') or '').lower()
            if any(n in name for n in needles):
                result.append(e)
        # Fallback to all if none matched
        return result or emplacements

    def _on_validate(self):
        if not self.piece_combo.currentData() or not self.dest_combo.currentData():
            QMessageBox.warning(self, self.tr("Validation"), self.tr("Please select a part and a destination location."))
            return
        self.accept()

    def get_data(self):
        return {
            'piece_id': self.piece_combo.currentData(),
            'emplacement_destination_id': self.dest_combo.currentData(),
        }

