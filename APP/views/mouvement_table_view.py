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
        self.setWindowTitle(self.tr("Mouvements de Stock"))
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
        """Crée la barre de menu"""
        self.menu_bar = QMenuBar(self)
        
        # Menu Affichage
        view_menu = self.menu_bar.addMenu(self.tr("Affichage"))
        
        # Tous les mouvements
        all_movements_action = QAction(self.tr("Tous les mouvements"), self)
        all_movements_action.triggered.connect(self.show_all_movements)
        view_menu.addAction(all_movements_action)
        
        view_menu.addSeparator()
        
        # Mouvements d'entrée
        entries_action = QAction(self.tr("Entrées uniquement"), self)
        entries_action.triggered.connect(self.show_entries_only)
        view_menu.addAction(entries_action)
        
        # Mouvements de sortie
        exits_action = QAction(self.tr("Sorties uniquement"), self)
        exits_action.triggered.connect(self.show_exits_only)
        view_menu.addAction(exits_action)
        
        # Transferts
        transfers_action = QAction(self.tr("Transferts uniquement"), self)
        transfers_action.triggered.connect(self.show_transfers_only)
        view_menu.addAction(transfers_action)
        
        view_menu.addSeparator()
        
        # Workflow de réception
        reception_action = QAction(self.tr("Mouvements de réception"), self)
        reception_action.triggered.connect(self.show_reception_only)
        view_menu.addAction(reception_action)
        
        # Mouvements neutres (impact = 0)
        neutral_action = QAction(self.tr("Mouvements neutres"), self)
        neutral_action.triggered.connect(self.show_neutral_only)
        view_menu.addAction(neutral_action)
        
        view_menu.addSeparator()
        
        # Mouvements du jour
        today_action = QAction(self.tr("Mouvements du jour"), self)
        today_action.triggered.connect(self.show_today_movements)
        view_menu.addAction(today_action)
        
        # Menu Rapports
        reports_menu = self.menu_bar.addMenu(self.tr("Rapports"))
        
        # Rapport d'activité
        activity_report_action = QAction(self.tr("Rapport d'activité"), self)
        activity_report_action.triggered.connect(self.generate_activity_report)
        reports_menu.addAction(activity_report_action)
        
        # Stocks faibles
        low_stock_action = QAction(self.tr("Pièces en stock faible"), self)
        low_stock_action.triggered.connect(self.show_low_stock)
        reports_menu.addAction(low_stock_action)
        
        layout.addWidget(self.menu_bar)

    def create_filters(self, layout):
        """Crée la section des filtres"""
        filter_group = QGroupBox(self.tr("Filtres"))
        filter_layout = QFormLayout()
        
        # Filtre par pièce
        self.piece_filter = QComboBox()
        self.piece_filter.addItem(self.tr("Toutes les pièces"), None)
        filter_layout.addRow(self.tr("Pièce:"), self.piece_filter)
        
        # Filtre par type de mouvement
        self.type_filter = QComboBox()
        self.type_filter.addItem(self.tr("Tous les types"), None)
        filter_layout.addRow(self.tr("Type:"), self.type_filter)
        
        # Filtre par date
        date_layout = QHBoxLayout()
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        
        date_layout.addWidget(QLabel(self.tr("Du:")))
        date_layout.addWidget(self.date_from)
        date_layout.addWidget(QLabel(self.tr("Au:")))
        date_layout.addWidget(self.date_to)
        
        filter_layout.addRow(self.tr("Période:"), date_layout)
        
        # Bouton appliquer filtres
        self.apply_filters_btn = QPushButton(self.tr("Appliquer les filtres"))
        self.apply_filters_btn.clicked.connect(self.apply_filters)
        filter_layout.addRow("", self.apply_filters_btn)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

    def create_movements_table(self, layout):
        """Crée la table des mouvements"""
        self.table = QTableWidget(self)
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Date"), self.tr("Pièce"), self.tr("Type"),
            self.tr("Quantité"), self.tr("Stock Avant"), self.tr("Stock Après"),
            self.tr("Emplacement Source"), self.tr("Emplacement Dest."),
            self.tr("Utilisateur"), self.tr("Référence"), self.tr("Coût Total")
        ])
        
        # Configuration de la table
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        
        layout.addWidget(self.table)

    def create_action_buttons(self, layout):
        """Crée les boutons d'action"""
        btn_layout = QHBoxLayout()
        
        # Boutons traditionnels
        self.new_entry_btn = QPushButton(self.tr("Nouvelle Entrée"))
        self.new_exit_btn = QPushButton(self.tr("Nouvelle Sortie"))
        self.new_transfer_btn = QPushButton(self.tr("Nouveau Transfert"))
        self.inventory_btn = QPushButton(self.tr("Ajustement Inventaire"))
        
        # Nouveaux boutons pour workflow de réception
        self.new_reception_btn = QPushButton(self.tr("Réception Pièces"))
        self.mise_en_stock_btn = QPushButton(self.tr("Mise en Stock"))
        
        # Boutons d'action
        self.cancel_btn = QPushButton(self.tr("Annuler Mouvement"))
        self.refresh_btn = QPushButton(self.tr("Actualiser"))
        self.close_btn = QPushButton(self.tr("Fermer"))
        
        # Style des boutons traditionnels
        self.new_entry_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        self.new_exit_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        self.new_transfer_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; }")
        self.inventory_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; }")
        
        # Style des nouveaux boutons de workflow réception
        self.new_reception_btn.setStyleSheet("QPushButton { background-color: #9C27B0; color: white; }")
        self.mise_en_stock_btn.setStyleSheet("QPushButton { background-color: #673AB7; color: white; }")
        
        # Style des boutons d'action
        self.cancel_btn.setStyleSheet("QPushButton { background-color: #9E9E9E; color: white; }")
        
        # Première ligne - opérations traditionnelles
        first_row = QHBoxLayout()
        for btn in [self.new_entry_btn, self.new_exit_btn, self.new_transfer_btn, 
                   self.inventory_btn]:
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
        """Crée le panneau d'actions rapides"""
        quick_group = QGroupBox(self.tr("Actions Rapides"))
        quick_layout = QVBoxLayout()
        
        # Entrée rapide
        entry_layout = QFormLayout()
        self.quick_piece_combo = QComboBox()
        self.quick_quantity_spin = QSpinBox()
        self.quick_quantity_spin.setRange(1, 9999)
        self.quick_entry_btn = QPushButton(self.tr("Entrée Rapide"))
        
        entry_layout.addRow(self.tr("Pièce:"), self.quick_piece_combo)
        entry_layout.addRow(self.tr("Quantité:"), self.quick_quantity_spin)
        entry_layout.addRow("", self.quick_entry_btn)
        
        quick_layout.addLayout(entry_layout)
        quick_group.setLayout(quick_layout)
        layout.addWidget(quick_group)

    def create_movement_details(self, layout):
        """Crée le panneau de détails du mouvement"""
        details_group = QGroupBox(self.tr("Détails du Mouvement"))
        details_layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(200)
        
        details_layout.addWidget(self.details_text)
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)

    def create_statistics_panel(self, layout):
        """Crée le panneau de statistiques"""
        stats_group = QGroupBox(self.tr("Statistiques"))
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
        """Actualise les données"""
        try:
            # Charger les mouvements
            mouvements = self.mouvement_controller.lister_mouvements()
            self.populate_table(mouvements)
            
            # Charger les données pour les combos
            self.load_combo_data()
            
            # Mettre à jour les statistiques
            self.update_statistics()
            
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur"), 
                               self.tr(f"Erreur lors du chargement des données: {e}"))

    def populate_table(self, mouvements):
        """Remplit la table avec les mouvements"""
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
            elif mouvement.get('impact_stock') == 0:  # Neutre (réception)
                # Violet/Magenta avec 75% de transparence (alpha = 64 sur 255)
                background_color = QColor(255, 0, 255, 64)  # Magenta transparent
                text_color = QColor(0, 0, 0)  # Noir
                for col in range(12):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(background_color)
                        item.setForeground(text_color)

    def load_combo_data(self):
        """Charge les données pour les combobox"""
        try:
            # Charger les pièces
            pieces = self.mouvement_controller.obtenir_pieces_disponibles()
            self.piece_filter.clear()
            self.piece_filter.addItem(self.tr("Toutes les pièces"), None)
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
            QMessageBox.warning(self, self.tr("Avertissement"), 
                              self.tr(f"Erreur lors du chargement des données de référence: {e}"))

    def update_statistics(self):
        """Met à jour les statistiques"""
        try:
            # Statistiques générales
            today = date.today()
            rapport = self.mouvement_controller.generer_rapport_activite(today, today)
            
            if rapport['success']:
                stats = rapport['rapport']
                stats_text = f"""
<b>Statistiques du jour:</b><br>
• Total mouvements: {stats['total_mouvements']}<br>
• Entrées: {stats['total_entrees']} ({stats['quantite_entree_totale']} unités)<br>
• Sorties: {stats['total_sorties']} ({stats['quantite_sortie_totale']} unités)<br>
• Valeur totale: {stats['valeur_totale']:.2f} €
                """
                self.stats_text.setHtml(stats_text)
            
        except Exception as e:
            self.stats_text.setText(f"Erreur lors du calcul des statistiques: {e}")

    def on_selection_changed(self):
        """Gère le changement de sélection dans la table"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            mouvement_id = self.table.item(current_row, 0).text()
            if mouvement_id:
                try:
                    mouvement = self.mouvement_controller.obtenir_mouvement(int(mouvement_id))
                    if mouvement:
                        self.show_movement_details(mouvement)
                except Exception as e:
                    self.details_text.setText(f"Erreur lors du chargement des détails: {e}")

    def show_movement_details(self, mouvement):
        """Affiche les détails d'un mouvement"""
        details_html = f"""
<b>Mouvement #{mouvement['id']}</b><br>
<b>Date:</b> {mouvement.get('date_mouvement', 'N/A')}<br>
<b>Pièce:</b> {mouvement.get('piece_reference', '')} - {mouvement.get('piece_nom', '')}<br>
<b>Type:</b> {mouvement.get('type_mouvement_nom', '')}<br>
<b>Quantité:</b> {mouvement.get('quantite', '')} unités<br>
<b>Stock avant:</b> {mouvement.get('stock_avant', '')}<br>
<b>Stock après:</b> {mouvement.get('stock_apres', '')}<br>
<b>Emplacement source:</b> {mouvement.get('emplacement_source_nom', 'N/A')}<br>
<b>Emplacement destination:</b> {mouvement.get('emplacement_destination_nom', 'N/A')}<br>
<b>Utilisateur:</b> {mouvement.get('utilisateur_nom', 'N/A')}<br>
<b>Référence:</b> {mouvement.get('reference_document', 'N/A')}<br>
<b>Coût unitaire:</b> {mouvement.get('cout_unitaire', 'N/A')}<br>
<b>Coût total:</b> {mouvement.get('cout_total', 'N/A')}<br>
<b>Commentaire:</b> {mouvement.get('commentaire', 'N/A')}
        """
        self.details_text.setHtml(details_html)

    # === Actions des menus ===

    def show_all_movements(self):
        """Affiche tous les mouvements"""
        self.refresh_data()

    def show_entries_only(self):
        """Affiche uniquement les entrées"""
        try:
            mouvements = self.mouvement_controller.lister_mouvements()
            entrees = [m for m in mouvements if m.get('impact_stock') == 1]
            self.populate_table(entrees)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur"), str(e))

    def show_exits_only(self):
        """Affiche uniquement les sorties"""
        try:
            mouvements = self.mouvement_controller.lister_mouvements()
            sorties = [m for m in mouvements if m.get('impact_stock') == -1]
            self.populate_table(sorties)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur"), str(e))

    def show_reception_only(self):
        """Affiche uniquement les mouvements de réception"""
        try:
            mouvements = self.mouvement_controller.lister_mouvements()
            receptions = [m for m in mouvements 
                         if any(keyword in m.get('type_mouvement', '') 
                               for keyword in ['RECEPTION', 'MISE_EN_STOCK', 'SORTIE_RECEPTION', 'RETOUR_RECEPTION'])]
            self.populate_table(receptions)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur"), str(e))
    
    def show_neutral_only(self):
        """Affiche uniquement les mouvements neutres (impact = 0)"""
        try:
            mouvements = self.mouvement_controller.lister_mouvements()
            neutres = [m for m in mouvements if m.get('impact_stock') == 0]
            self.populate_table(neutres)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur"), str(e))

    def show_transfers_only(self):
        """Affiche uniquement les transferts"""
        try:
            mouvements = self.mouvement_controller.lister_mouvements()
            transferts = [m for m in mouvements if 'TRANSFERT' in m.get('type_mouvement', '')]
            self.populate_table(transferts)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur"), str(e))

    def show_today_movements(self):
        """Affiche les mouvements du jour"""
        try:
            today = date.today()
            filtres = {'date_debut': today, 'date_fin': today}
            mouvements = self.mouvement_controller.lister_mouvements(filtres)
            self.populate_table(mouvements)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur"), str(e))

    def apply_filters(self):
        """Applique les filtres sélectionnés"""
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
            QMessageBox.critical(self, self.tr("Erreur"), str(e))

    # === Actions des boutons ===

    def new_entry(self):
        """Nouvelle entrée de stock"""
        try:
            pieces = self.mouvement_controller.obtenir_pieces_disponibles()
            types_entree = self.mouvement_controller.obtenir_types_mouvement('entree')
            emplacements = self.mouvement_controller.obtenir_emplacements_disponibles()
            
            dialog = MouvementDialog(self, 'entree', pieces, types_entree, emplacements)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                result = self.mouvement_controller.effectuer_entree_stock(**data)
                
                if result['success']:
                    QMessageBox.information(self, self.tr("Succès"), result['message'])
                    self.refresh_data()
                else:
                    QMessageBox.critical(self, self.tr("Erreur"), result['message'])
                    
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur"), str(e))

    def new_exit(self):
        """Nouvelle sortie de stock"""
        try:
            pieces = self.mouvement_controller.obtenir_pieces_disponibles()
            types_sortie = self.mouvement_controller.obtenir_types_mouvement('sortie')
            emplacements = self.mouvement_controller.obtenir_emplacements_disponibles()
            
            dialog = MouvementDialog(self, 'sortie', pieces, types_sortie, emplacements)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                result = self.mouvement_controller.effectuer_sortie_stock(**data)
                
                if result['success']:
                    QMessageBox.information(self, self.tr("Succès"), result['message'])
                    self.refresh_data()
                else:
                    QMessageBox.critical(self, self.tr("Erreur"), result['message'])
                    
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur"), str(e))

    def new_transfer(self):
        """Nouveau transfert"""
        try:
            pieces = self.mouvement_controller.obtenir_pieces_disponibles()
            emplacements = self.mouvement_controller.obtenir_emplacements_disponibles()
            
            dialog = MouvementDialog(self, 'transfert', pieces, [], emplacements)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                result = self.mouvement_controller.effectuer_transfert(**data)
                
                if result['success']:
                    QMessageBox.information(self, self.tr("Succès"), result['message'])
                    self.refresh_data()
                else:
                    QMessageBox.critical(self, self.tr("Erreur"), result['message'])
                    
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur"), str(e))

    def inventory_adjustment(self):
        """Ajustement d'inventaire"""
        try:
            pieces = self.mouvement_controller.obtenir_pieces_disponibles()
            
            dialog = MouvementDialog(self, 'inventaire', pieces, [], [])
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                result = self.mouvement_controller.effectuer_ajustement_inventaire(**data)
                
                if result['success']:
                    QMessageBox.information(self, self.tr("Succès"), result['message'])
                    self.refresh_data()
                else:
                    QMessageBox.critical(self, self.tr("Erreur"), result['message'])
                    
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur"), str(e))

    def cancel_movement(self):
        """Annule un mouvement sélectionné"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, self.tr("Aucune sélection"), 
                              self.tr("Veuillez sélectionner un mouvement à annuler."))
            return
        
        mouvement_id = int(self.table.item(current_row, 0).text())
        
        reply = QMessageBox.question(self, self.tr("Confirmation"), 
                                   self.tr("Êtes-vous sûr de vouloir annuler ce mouvement ?"),
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                result = self.mouvement_controller.annuler_mouvement(mouvement_id)
                
                if result['success']:
                    QMessageBox.information(self, self.tr("Succès"), result['message'])
                    self.refresh_data()
                else:
                    QMessageBox.critical(self, self.tr("Erreur"), result['message'])
                    
            except Exception as e:
                QMessageBox.critical(self, self.tr("Erreur"), str(e))

    def quick_entry(self):
        """Entrée rapide"""
        piece_id = self.quick_piece_combo.currentData()
        quantite = self.quick_quantity_spin.value()
        
        if not piece_id:
            QMessageBox.warning(self, self.tr("Sélection requise"), 
                              self.tr("Veuillez sélectionner une pièce."))
            return
        
        try:
            result = self.mouvement_controller.effectuer_entree_stock(
                piece_id=piece_id,
                quantite=quantite,
                type_mouvement='ENTREE_ACHAT',
                commentaire='Entrée rapide'
            )
            
            if result['success']:
                QMessageBox.information(self, self.tr("Succès"), result['message'])
                self.refresh_data()
                self.quick_quantity_spin.setValue(1)
            else:
                QMessageBox.critical(self, self.tr("Erreur"), result['message'])
                
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur"), str(e))

    def generate_activity_report(self):
        """Génère un rapport d'activité"""
        # TODO: Implémenter la génération de rapport
        QMessageBox.information(self, self.tr("Information"), 
                              self.tr("Fonctionnalité de rapport à implémenter"))

    def show_low_stock(self):
        """Affiche les pièces en stock faible"""
        try:
            result = self.mouvement_controller.obtenir_pieces_stock_faible()
            if result['success']:
                # TODO: Afficher dans une nouvelle fenêtre ou dialog
                pieces = result['pieces']
                message = f"Nombre de pièces en stock faible: {result['count']}"
                QMessageBox.information(self, self.tr("Stock Faible"), message)
            else:
                QMessageBox.critical(self, self.tr("Erreur"), result['error'])
                
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur"), str(e))

    # === Workflow de Réception ===

    def new_reception(self):
        """Nouvelle réception de pièces"""
        try:
            pieces = self.mouvement_controller.obtenir_pieces_disponibles()
            types_reception = self.mouvement_controller.obtenir_types_mouvement('neutre')
            emplacements = self.mouvement_controller.obtenir_emplacements_disponibles()
            
            dialog = ReceptionWorkflowDialog(self, pieces, types_reception, emplacements)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                result = self.mouvement_controller.effectuer_reception_achat(**data)
                
                if result['success']:
                    QMessageBox.information(self, self.tr("Succès"), 
                                          self.tr(f"Réception effectuée: {result['message']}"))
                    self.refresh_data()
                else:
                    QMessageBox.critical(self, self.tr("Erreur"), result['message'])
                    
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur"), 
                               self.tr(f"Erreur lors de la réception: {e}"))

    def mise_en_stock(self):
        """Mise en stock depuis la réception"""
        try:
            pieces = self.mouvement_controller.obtenir_pieces_disponibles()
            emplacements = self.mouvement_controller.obtenir_emplacements_disponibles()
            
            dialog = MiseEnStockDialog(self, pieces, emplacements)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                result = self.mouvement_controller.effectuer_mise_en_stock(**data)
                
                if result['success']:
                    QMessageBox.information(self, self.tr("Succès"), 
                                          self.tr(f"Mise en stock effectuée: {result['message']}"))
                    self.refresh_data()
                else:
                    QMessageBox.critical(self, self.tr("Erreur"), result['message'])
                    
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur"), 
                               self.tr(f"Erreur lors de la mise en stock: {e}"))