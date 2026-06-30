from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QLabel, 
    QHBoxLayout, QPushButton, QToolBar, QMessageBox,
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit,
    QDateEdit, QComboBox, QDoubleSpinBox, QSpinBox,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView
)
from PySide6.QtCore import Qt, QSize, QDate
from PySide6.QtGui import QAction, QIcon

from APP.models.commande_repository import CommandeRepository
from APP.models.ligne_commande_repository import LigneCommandeRepository
from APP.models.fournisseur_repository import FournisseurRepository
from APP.models.piece_repository import PieceRepository
from APP.models.commande_table_model import CommandeTableModel, LigneCommandeTableModel
from APP.controllers.commande_controller import CommandeController
from APP.services.commande_service import get_all_commandes_clean
from datetime import datetime

from .commande_dialog import CommandeDialog
from .ligne_commande_dialog import LigneCommandeDialog

class CommandeView(QWidget):
    def __init__(self, commandes, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Orders Management")
        self.setMinimumSize(1200, 800)
        
        # Initialisation des repositories
        self.commande_repo = CommandeRepository(db)
        self.ligne_commande_repo = LigneCommandeRepository(db)
        self.commande_controller = CommandeController(db, self.commande_repo, self.ligne_commande_repo)
        self.fournisseur_repo = FournisseurRepository(db)
        self.piece_repo = PieceRepository(db)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Toolbar
        self.toolbar = QToolBar("Tools")
        
        # New order button
        new_action = QAction(QIcon.fromTheme("document-new"), "New order", self)
        new_action.triggered.connect(self.nouvelle_commande)
        self.toolbar.addAction(new_action)
        
        # Edit button
        self.edit_action = QAction(QIcon.fromTheme("document-edit"), "Edit", self)
        self.edit_action.triggered.connect(self.editer_commande)
        self.edit_action.setEnabled(False)
        self.toolbar.addAction(self.edit_action)
        
        # Delete button
        self.delete_action = QAction(QIcon.fromTheme("edit-delete"), "Delete", self)
        self.delete_action.triggered.connect(self.supprimer_commande)
        self.delete_action.setEnabled(False)
        self.toolbar.addAction(self.delete_action)
        
        self.toolbar.addSeparator()
        
        # Filter button
        filter_action = QAction(QIcon.fromTheme("view-filter"), "Filter", self)
        filter_action.triggered.connect(self.show_filter_dialog)
        self.toolbar.addAction(filter_action)
        
        # Export button
        export_action = QAction(QIcon.fromTheme("document-export"), "Export", self)
        export_action.triggered.connect(self.export_data)
        self.toolbar.addAction(export_action)
        
        # Refresh button
        refresh_action = QAction(QIcon.fromTheme("view-refresh"), "Refresh", self)
        refresh_action.triggered.connect(self.refresh_data)
        self.toolbar.addAction(refresh_action)
        
        main_layout.addWidget(self.toolbar)
        
        # Stocke une référence au layout principal pour les mises à jour
        self.main_layout = main_layout

        # Tableau principal
        self.table = QTableView()
        self.model = CommandeTableModel(commandes)
        self.table.setModel(self.model)
        
        # Configuration des en-têtes
        header = self.table.horizontalHeader()
        
        # Définit les largeurs de colonnes personnalisées (en pixels)
        column_widths = {
            "id_commande": 60,          # ID
            "numero_commande": 120,     # N° Commande
            "fournisseur_nom": 150,     # Fournisseur
            "createur_nom": 120,        # Créateur
            "date_commande": 100,       # Date commande
            "date_livraison_prevue": 120,  # Livraison prévue
            "date_livraison_reelle": 120, # Livraison réelle
            "statut": 100,              # Statut
            "total_ht": 90,             # Total HT
            "frais_port": 80,           # Frais port
            "reference_fournisseur": 120, # Réf. fournisseur
            "mode_paiement": 100,       # Mode paiement
            # Les colonnes suivantes seront masquées par défaut
            "notes_commande": 0,        # Notes (masquée)
            "created_at": 0,             # Créé le (masquée)
            "updated_at": 0              # Modifié le (masquée)
        }
        
        # Applique les largeurs de colonnes
        for idx, key in enumerate(self.model.headers):
            if key in column_widths:
                width = column_widths[key]
                if width > 0:  # Si largeur > 0, on définit la largeur
                    self.table.setColumnWidth(idx, width)
                else:  # Sinon on masque la colonne
                    self.table.setColumnHidden(idx, True)
        
        # Configuration du header
        header.setStretchLastSection(True)  # Étire la dernière colonne visible
        header.setVisible(True)  # Force l'affichage des en-têtes
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #f0f0f0;
                font-weight: bold;
                padding: 4px;
                border: 1px solid #d0d0d0;
            }
        """)
        
        # Active le tri
        self.table.setSortingEnabled(True)
        
        # Affiche les lignes alternées pour une meilleure lisibilité
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableView {
                alternate-background-color: #f9f9f9;
                gridline-color: #e0e0e0;
            }
            QTableView::item {
                padding: 4px;
            }
        """)
        
        # Configuration de la sélection
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        
        # Ajout du tableau au layout avec un facteur d'étirement
        main_layout.addWidget(QLabel("<b>Orders list:</b>"))
        main_layout.addWidget(self.table, 1)  # Le facteur 1 permet l'étirement

        # Section des boutons de gestion des commandes
        self.create_status_buttons_section(main_layout)

        # Tableau secondaire pour les lignes de commande
        lignes_group = QWidget()
        lignes_layout = QVBoxLayout(lignes_group)
        lignes_layout.setContentsMargins(0, 0, 0, 0)
        
        # Titre du groupe
        title_label = QLabel("<b>Lines of the selected order:</b>")
        lignes_layout.addWidget(title_label)
        
        # Création du tableau
        self.ligne_table = QTableView()
        self.ligne_model = LigneCommandeTableModel([])
        self.ligne_table.setModel(self.ligne_model)
        
        # Configuration des en-têtes
        ligne_header = self.ligne_table.horizontalHeader()
        
        # Définit les largeurs de colonnes personnalisées (en pixels)
        ligne_column_widths = {
            "id_ligne": 60,           # ID Ligne
            "piece_reference": 120,   # Réf. pièce
            "piece_nom": 200,         # Nom pièce
            "description_libre": 0,   # Description (masquée par défaut)
            "quantite_commandee": 80, # Qté commandée
            "prix_unitaire_ht": 90,   # PU HT
            "quantite_recue": 80,     # Qté reçue
            "date_reception": 100,    # Date réception
            "statut_ligne": 100,      # Statut
            "commande_id": 0,         # ID Commande (masquée)
            "piece_id": 0              # ID Pièce (masquée)
        }
        
        # Applique les largeurs de colonnes
        for idx, key in enumerate(self.ligne_model.headers):
            if key in ligne_column_widths:
                width = ligne_column_widths[key]
                if width > 0:  # Si largeur > 0, on définit la largeur
                    self.ligne_table.setColumnWidth(idx, width)
                else:  # Sinon on masque la colonne
                    self.ligne_table.setColumnHidden(idx, True)
        
        # Configuration du header
        ligne_header.setStretchLastSection(True)
        ligne_header.setStyleSheet("""
            QHeaderView::section {
                background-color: #e8e8e8;
                font-weight: bold;
                padding: 4px;
                border: 1px solid #d0d0d0;
                font-size: 11px;
            }
        """)
        
        # Style du tableau
        self.ligne_table.setStyleSheet("""
            QTableView {
                alternate-background-color: #f5f5f5;
                gridline-color: #e0e0e0;
                font-size: 11px;
            }
            QTableView::item {
                padding: 2px 4px;
            }
        """)
        
        # Configuration de la sélection
        self.ligne_table.setSelectionBehavior(QTableView.SelectRows)
        self.ligne_table.setSelectionMode(QTableView.SingleSelection)
        
        # Ajuste la hauteur pour afficher 3 lignes
        row_height = self.ligne_table.verticalHeader().defaultSectionSize()
        header_height = self.ligne_table.horizontalHeader().height()
        self.ligne_table.setMinimumHeight(row_height * 3 + header_height + 4)
        self.ligne_table.setMaximumHeight(row_height * 5 + header_height + 4)  # Maximum 5 lignes avec barre de défilement
        
        # Ajout du tableau au layout
        lignes_layout.addWidget(self.ligne_table)
        
        # Ajout du groupe au layout principal
        main_layout.addWidget(lignes_group)

        # Rafraîchir les lignes quand sélection change
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)
    
    def create_status_buttons_section(self, main_layout):
        """Crée la section des boutons de gestion des statuts de commande"""
        # Label pour la section
        status_label = QLabel("<b>Actions on the selected order:</b>")
        main_layout.addWidget(status_label)
        
        # Widget conteneur pour les boutons
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 5, 0, 5)
        
        # Status management buttons
        self.confirmer_btn = QPushButton("Confirm")
        self.confirmer_btn.setToolTip("Move from 'Brouillon' to 'Validee'")
        self.confirmer_btn.clicked.connect(self.confirmer_commande_selectionnee)
        
        self.envoyer_btn = QPushButton("Send")
        self.envoyer_btn.setToolTip("Move from 'Validee' to 'Envoyee'")
        self.envoyer_btn.clicked.connect(self.envoyer_commande_selectionnee)
        
        self.livrer_btn = QPushButton("Deliver")
        self.livrer_btn.setToolTip("Move from 'Envoyee' to 'Livree' and create stock movements")
        self.livrer_btn.clicked.connect(self.livrer_commande_selectionnee)
        
        self.copier_btn = QPushButton("Copy")
        self.copier_btn.setToolTip("Create a new order with the same lines")
        self.copier_btn.clicked.connect(self.copier_commande_selectionnee)
        
        self.annuler_commande_btn = QPushButton("Cancel order")
        self.annuler_commande_btn.setToolTip("Cancel the order (becomes inaccessible)")
        self.annuler_commande_btn.setStyleSheet("QPushButton { background-color: #ff6b6b; color: white; }")
        self.annuler_commande_btn.clicked.connect(self.annuler_commande_selectionnee)
        
        # Ajouter les boutons au layout
        status_layout.addWidget(self.confirmer_btn)
        status_layout.addWidget(self.envoyer_btn)
        status_layout.addWidget(self.livrer_btn)
        status_layout.addWidget(self.copier_btn)
        status_layout.addStretch()  # Espace flexible
        status_layout.addWidget(self.annuler_commande_btn)
        
        # Désactiver tous les boutons par défaut
        self.update_status_buttons_state()
        
        # Ajouter le widget au layout principal
        main_layout.addWidget(status_widget)

    def update_lignes_commande(self):
        """Met à jour le tableau des lignes de commande pour la commande sélectionnée."""
        if not hasattr(self, 'db') or not self.db:
            print("[ERROR] No database connection")
            return
            
        # Récupère l'ID de la commande sélectionnée
        commande_id = self.get_selected_commande_id()
        
        # Si aucune commande sélectionnée, vide le tableau des lignes
        if not commande_id:
            self.ligne_model = LigneCommandeTableModel([])
            self.ligne_table.setModel(self.ligne_model)
            self.ligne_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            self.ligne_table.horizontalHeader().setStretchLastSection(True)
            return
            
        print(f"[DEBUG] Loading lines for order ID: {commande_id}")
        
        try:
            # Récupère les lignes de commande depuis le repository
            lignes = self.ligne_commande_repo.get_lignes_by_commande_id(commande_id)
            print(f"[DEBUG] {len(lignes)} lines retrieved for order {commande_id}")
            
            # Met à jour le modèle avec les nouvelles données
            self.ligne_model = LigneCommandeTableModel(lignes)
            self.ligne_table.setModel(self.ligne_model)
            
            # Réapplique les paramètres d'affichage
            header = self.ligne_table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.ResizeToContents)
            header.setStretchLastSection(True)
            
            # Ajuste la hauteur du tableau en fonction du nombre de lignes (max 5)
            row_height = self.ligne_table.verticalHeader().defaultSectionSize()
            header_height = self.ligne_table.horizontalHeader().height()
            max_visible_rows = 5  # Augmenté à 5 pour une meilleure visibilité
            
            # Calcule la hauteur totale nécessaire
            visible_rows = min(len(lignes), max_visible_rows)
            total_height = (row_height * visible_rows) + header_height + 8  # +8 pour la marge
            
            # Si pas de lignes, on garde une hauteur minimale pour l'en-tête
            if visible_rows == 0:
                total_height = header_height + 8
                
            self.ligne_table.setMinimumHeight(total_height)
            self.ligne_table.setMaximumHeight(total_height)
            
            # Force la mise à jour de l'affichage
            self.ligne_table.viewport().update()
            
        except Exception as e:
            print(f"[ERROR] Unable to load order lines: {str(e)}")
            # Show an error message to the user
            QMessageBox.critical(self, "Error", 
                f"Unable to load order lines:\n{str(e)}")
            
            # Affiche un tableau vide en cas d'erreur
            self.ligne_model = LigneCommandeTableModel([])
            self.ligne_table.setModel(self.ligne_model)
            
    def refresh_data(self):
        """Rafraîchit les données depuis la base de données."""
        print("[DEBUG] refresh_data method called")
        
        if not hasattr(self, 'db') or not self.db:
            print("[ERROR] Cannot refresh: no database connection")
            return False
            
        print("[DEBUG] Refreshing data...")
        
        try:
            # Réimporte le service pour éviter les problèmes de rechargement
            from APP.services.commande_service import get_all_commandes_clean
            
            # Récupère les données mises à jour
            updated_commandes = get_all_commandes_clean(self.db)
            
            if updated_commandes is None:
                print("[ERROR] No data received during refresh")
                return False
                
            print(f"[DEBUG] {len(updated_commandes)} orders loaded")
            
            # Sauvegarde la position de défilement actuelle
            scroll_position = self.table.verticalScrollBar().value()
            
            # Met à jour le modèle avec les nouvelles données
            self.model = CommandeTableModel(updated_commandes)
            self.table.setModel(self.model)
            
            # Réapplique les paramètres d'affichage
            header = self.table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.ResizeToContents)
            header.setStretchLastSection(True)
            header.setStyleSheet("::section{background-color: #f0f0f0; font-weight: bold;}")
            
            # Réactive le tri
            self.table.setSortingEnabled(True)
            
            # Restaure la position de défilement
            self.table.verticalScrollBar().setValue(scroll_position)
            
            # Rafraîchit l'affichage
            self.table.viewport().update()
            
            # Met à jour la vue des lignes si nécessaire
            if hasattr(self, 'ligne_table') and hasattr(self, 'ligne_model'):
                self.ligne_model = LigneCommandeTableModel([])
                self.ligne_table.setModel(self.ligne_model)
            
            print("[DEBUG] Data refreshed successfully")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to refresh data: {str(e)}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", 
                f"Unable to refresh data:\n{str(e)}")
            return False
            
    def on_selection_changed(self):
        """Active ou désactive les boutons en fonction de la sélection"""
        has_selection = self.table.selectionModel().hasSelection()
        self.edit_action.setEnabled(has_selection)
        self.delete_action.setEnabled(has_selection)
        
        # Mettre à jour l'état des boutons de statut
        self.update_status_buttons_state()
        
        # Mettre à jour les lignes de commande
        self.update_lignes_commande()
    
    def get_selected_commande_id(self):
        """Récupère l'ID de la commande sélectionnée"""
        selection = self.table.selectionModel().selectedRows()
        if not selection:
            return None
            
        index = selection[0]
        if not index.isValid():
            return None
            
        return self.model.commandes[index.row()].get('id_commande')
    
    def nouvelle_commande(self):
        """Ouvre la boîte de dialogue pour créer une nouvelle commande"""
        dialog = CommandeDialog(self.db, parent=self)
        if dialog.exec() == QDialog.Accepted:
            # Récupérer les données du formulaire
            data = dialog.get_data()
            
            # Si data est None, c'est qu'il y a eu une erreur de validation
            if data is None:
                return
            
            try:
                # Récupérer l'ID de l'utilisateur Admin par défaut
                createur_id = self.commande_repo.get_default_user_id()
                
                # Vérifier que l'ID de l'utilisateur est valide
                if not createur_id:
                    raise ValueError("Unable to determine the user for order creation")
                
                # Ajouter l'ID du créateur aux données
                data['createur_id'] = createur_id
                
                # Créer la commande dans la base de données
                commande_id = self.commande_repo.add_commande(data)
                
                # Ajouter les lignes de commande
                import pprint
                for ligne in data.get('lignes', []):
                    ligne['commande_id'] = commande_id
                    
                    # S'assurer que piece_id est un entier et non un dictionnaire
                    if isinstance(ligne.get('piece_id'), dict):
                        piece_id_dict = ligne['piece_id']
                        # Extraire l'ID de la pièce du dictionnaire
                        piece_id = piece_id_dict.get('piece_id') or piece_id_dict.get('id_piece')
                        if piece_id is not None:
                            ligne['piece_id'] = piece_id
                    
                    print("[DEBUG] Ligne envoyée à add_ligne_commande:", pprint.pformat(ligne))
                    self.ligne_commande_repo.add_ligne_commande(ligne)
                
                # Rafraîchir l'affichage
                self.refresh_data()
                
                # Sélectionner la nouvelle commande
                self.select_commande(commande_id)
                
                QMessageBox.information(self, "Success", "The order has been created successfully.")
                
            except Exception as e:
                QMessageBox.critical(
                    self, 
                    "Error", 
                    f"An error occurred while creating the order:\n{str(e)}"
                )
                # Show full traceback for debugging
                import traceback
                print(f"Full error: {traceback.format_exc()}")
    
    def editer_commande(self):
        """Ouvre la boîte de dialogue pour modifier la commande sélectionnée"""
        commande_id = self.get_selected_commande_id()
        if not commande_id:
            return
            
        try:
            # Récupérer les données de la commande
            commande = self.commande_repo.get_commande_by_id(commande_id)
            if not commande:
                QMessageBox.warning(self, "Error", "Order not found.")
                return
                
            # Récupérer les lignes de commande
            lignes = self.ligne_commande_repo.get_lignes_by_commande_id(commande_id)
            commande['lignes'] = lignes
            
            # Ouvrir la boîte de dialogue
            dialog = CommandeDialog(self.db, commande, self)
            # Connecter le signal de livraison pour rafraîchir la vue
            dialog.commande_livree.connect(self.refresh_data)
            
            if dialog.exec() == QDialog.Accepted:
                # Mettre à jour la commande
                data = dialog.get_data()
                self.commande_repo.update_commande(commande_id, data)
                
                # Mettre à jour les lignes de commande
                # Supprimer les anciennes lignes
                self.ligne_commande_repo.delete_lignes_by_commande_id(commande_id)
                
                # Ajouter les nouvelles lignes
                for ligne in data.get('lignes', []):
                    # Nettoyer le piece_id si c'est un dictionnaire
                    if isinstance(ligne.get('piece_id'), dict):
                        piece_data = ligne['piece_id']
                        if 'piece_id' in piece_data:
                            ligne['piece_id'] = piece_data['piece_id']
                        elif 'id_piece' in piece_data:
                            ligne['piece_id'] = piece_data['id_piece']
                        else:
                            # Si on ne peut pas extraire l'ID, on met None
                            ligne['piece_id'] = None
                    
                    ligne['commande_id'] = commande_id
                    self.ligne_commande_repo.add_ligne_commande(ligne)
                
                # Rafraîchir l'affichage
                self.refresh_data()
                
                # Resélectionner la commande
                self.select_commande(commande_id)
                
                QMessageBox.information(self, "Success", "Order updated successfully.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                f"An error occurred while editing the order:\n{str(e)}")
    
    def supprimer_commande(self):
        """Supprime la commande sélectionnée après confirmation"""
        commande_id = self.get_selected_commande_id()
        if not commande_id:
            return
            
        # Ask for confirmation
        reply = QMessageBox.question(
            self, 
            'Confirm deletion',
            'Are you sure you want to delete this order?\nThis will also delete all associated order lines.',
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Delete the order (and its lines via CASCADE or logic in the repository)
                success = self.commande_repo.delete_commande(commande_id)
                
                if success:
                    # Refresh display
                    self.refresh_data()
                    QMessageBox.information(self, "Success", "The order and its lines have been successfully deleted.")
                else:
                    QMessageBox.warning(self, "Warning", "The order could not be found or deleted.")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", 
                    f"An error occurred while deleting the order:\n{str(e)}")
    
    def select_commande(self, commande_id):
        """Selects an order in the table"""
        if not commande_id:
            return
            
        for row in range(self.model.rowCount()):
            idx = self.model.index(row, 0)
            if self.model.data(idx, Qt.UserRole) == commande_id:
                self.table.selectRow(row)
                self.table.scrollTo(idx)
                break
    
    def show_filter_dialog(self):
        """Displays the filter dialog"""
        QMessageBox.information(self, "Filters", "Filtering functionality to be implemented.")
    
    def export_data(self):
        """Exports data to CSV or Excel"""
        QMessageBox.information(self, "Export", "Export functionality to be implemented.")
    
    # === Methods for order status management ===
    
    def get_selected_commande_data(self):
        """Gets the complete data of the selected order"""
        commande_id = self.get_selected_commande_id()
        if not commande_id:
            return None
        
        try:
            return self.commande_repo.get_commande_by_id(commande_id)
        except Exception as e:
            print(f"[ERROR] Unable to retrieve order {commande_id}: {e}")
            return None
    
    def update_status_buttons_state(self):
        """Updates the status buttons based on the selected order's status"""
        # Check that the buttons exist
        if not hasattr(self, 'confirmer_btn'):
            return
        
        # Disable all buttons by default
        self.confirmer_btn.setEnabled(False)
        self.envoyer_btn.setEnabled(False)
        self.livrer_btn.setEnabled(False)
        self.copier_btn.setEnabled(False)
        self.annuler_commande_btn.setEnabled(False)
        
        # Get the selected order
        commande = self.get_selected_commande_data()
        if not commande:
            return
        
        statut = commande.get('statut', '')
        
        # Enable buttons based on status
        if statut == 'Brouillon':
            self.confirmer_btn.setEnabled(True)
            self.copier_btn.setEnabled(True)
            self.annuler_commande_btn.setEnabled(True)
        elif statut == 'Validee':
            self.envoyer_btn.setEnabled(True)
            self.copier_btn.setEnabled(True)
            self.annuler_commande_btn.setEnabled(True)
        elif statut == 'Envoyee':
            self.livrer_btn.setEnabled(True)
            self.copier_btn.setEnabled(True)
            self.annuler_commande_btn.setEnabled(True)
        elif statut == 'Partielle':
            # Partially delivered order, can continue receiving
            self.livrer_btn.setEnabled(True)
            self.copier_btn.setEnabled(True)
            self.annuler_commande_btn.setEnabled(True)
        elif statut == 'Livree':
            # Delivered order, only copying is possible
            self.copier_btn.setEnabled(True)
        elif statut == 'Annulee':
            # Canceled order, only copying is possible
            self.copier_btn.setEnabled(True)
        else:
            # Unknown status, only copying is possible
            self.copier_btn.setEnabled(True)
    
    def confirmer_commande_selectionnee(self):
        """Confirms the selected order (Brouillon → Validée)"""
        commande = self.get_selected_commande_data()
        if not commande:
            QMessageBox.warning(self, "Error", "No order selected.")
            return
        
        if commande['statut'] != 'Brouillon':
            QMessageBox.warning(self, "Error", "Only orders with status 'Brouillon' can be confirmed.")
            return
        
        if self._changer_statut_commande(commande['id_commande'], 'Validee'):
            QMessageBox.information(self, "Success", f"Order {commande['numero_commande']} successfully confirmed.")
            self.refresh_data()
    
    def envoyer_commande_selectionnee(self):
        """Sends the selected order (Validée → Envoyée)"""
        commande = self.get_selected_commande_data()
        if not commande:
            QMessageBox.warning(self, "Error", "No order selected.")
            return
        
        if commande['statut'] != 'Validee':
            QMessageBox.warning(self, "Error", "Only orders with status 'Validee' can be sent.")
            return
        
        if self._changer_statut_commande(commande['id_commande'], 'Envoyee'):
            QMessageBox.information(self, "Success", f"Order {commande['numero_commande']} sent to the supplier.")
            self.refresh_data()
    
    def livrer_commande_selectionnee(self):
        """Opens the delivery dialog to process the detailed delivery"""
        commande = self.get_selected_commande_data()
        if not commande:
            QMessageBox.warning(self, "Error", "No order selected.")
            return
        
        if commande['statut'] not in ['Envoyee', 'Partielle']:
            QMessageBox.warning(self, "Error", "Only orders with status 'Envoyee' or 'Partielle' can be received.")
            return
        
        try:
            # Open the delivery dialog
            from .reception_dialog import ReceptionDialog
            
            dialog = ReceptionDialog(self.db, commande, self)
            
            if dialog.exec() == QDialog.Accepted:
                # Get the delivery summary
                summary = dialog.get_reception_summary()
                
                QMessageBox.information(
                    self, 
                    "Reception completed", 
                    f"Reception of order {commande['numero_commande']} completed successfully.\n\n"
                    f"• Lines processed: {summary['lignes_traitees']}\n"
                    f"• Total items: {summary['total_pieces']}\n"
                    f"• Items in good condition: {summary['pieces_bon_etat']}\n"
                    f"• Defective items: {summary['pieces_defectueuses']}\n\n"
                    "Stock movements were created automatically."
                )
                
                # Refresh the view
                self.refresh_data()
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error", 
                f"Error while opening the delivery dialog:\n{str(e)}"
            )
    
    def copier_commande_selectionnee(self):
        """Copies the selected order"""
        commande = self.get_selected_commande_data()
        if not commande:
            QMessageBox.warning(self, "Error", "No order selected.")
            return
        
        reply = QMessageBox.question(
            self, 
            "Copy order", 
            f"Do you want to create a new order based on order {commande['numero_commande']}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                result = self._creer_copie_commande(commande)
                if result is None:
                    return
                QMessageBox.information(
                    self, 
                    "Success", 
                    "New order created successfully."
                )
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(
                    self, 
                    "Error", 
                    f"Error while copying the order:\n{str(e)}"
                )
    
    def annuler_commande_selectionnee(self):
        """Cancels the selected order"""
        commande = self.get_selected_commande_data()
        if not commande:
            QMessageBox.warning(self, "Error", "No order selected.")
            return
        
        if commande['statut'] in ['Livree', 'Annulee']:
            QMessageBox.warning(self, "Error", "This order cannot be canceled.")
            return
        
        reply = QMessageBox.question(
            self, 
            "Cancel order", 
            f"Are you sure you want to cancel order {commande['numero_commande']}?\n"
            "This action is irreversible.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self._changer_statut_commande(commande['id_commande'], 'Annulee'):
                QMessageBox.information(self, "Success", f"Order {commande['numero_commande']} canceled.")
                self.refresh_data()
    
    def _changer_statut_commande(self, commande_id, nouveau_statut, with_delivery_date=False):
        """Changes the status of an order (delegates to controller)."""
        try:
            self.commande_controller.changer_statut(commande_id, nouveau_statut)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error while changing status:\n{str(e)}")
            return False
    
    def _creer_mouvements_livraison(self, commande):
        """Creates stock movements for the delivery (delegates to controller)."""
        return self.commande_controller.creer_mouvements_livraison(commande)
    
    def _creer_copie_commande(self, commande_originale):
        """Crée une copie de la commande (delegates to controller)."""
        try:
            return self.commande_controller.creer_copie_commande(commande_originale)
        except ValueError as e:
            QMessageBox.warning(self, self.tr("Error"), self.tr(str(e)))
            return None
    
    def _generer_nouveau_numero(self):
        """Génère un nouveau numéro de commande unique (via SQL MAX pour O(1))."""
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
            from datetime import datetime
            return f"CMD-{int(datetime.now().timestamp())}"
