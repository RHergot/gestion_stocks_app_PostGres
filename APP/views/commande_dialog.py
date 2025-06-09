from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, 
                             QSpinBox, QPushButton, QMessageBox, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QLabel, QGroupBox,
                             QFrame, QWidget)
from PySide6.QtCore import Qt, QDate, Signal
from datetime import datetime

class CommandeDialog(QDialog):
    # Signal émis quand une commande est livrée pour rafraîchir la vue
    commande_livree = Signal()
    
    def __init__(self, db, commande_data=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.commande_data = commande_data or {}
        self.is_editing = bool(commande_data)
        self.setWindowTitle("Éditer une commande" if commande_data else "Nouvelle commande")
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
        
        # Groupe pour les informations de base de la commande
        info_group = QGroupBox("Informations de la commande")
        info_layout = QFormLayout()
        
        # Numéro de commande
        self.numero_commande = QLineEdit()
        info_layout.addRow("Numéro de commande:", self.numero_commande)
        
        # Fournisseur
        self.fournisseur_combo = QComboBox()
        info_layout.addRow("Fournisseur:", self.fournisseur_combo)
        
        # Dates
        self.date_commande = QDateEdit(calendarPopup=True)
        self.date_commande.setDate(QDate.currentDate())
        self.date_livraison_prevue = QDateEdit(calendarPopup=True)
        self.date_livraison_prevue.setDate(QDate.currentDate().addDays(14))
        
        info_layout.addRow("Date de commande:", self.date_commande)
        info_layout.addRow("Date livraison prévue:", self.date_livraison_prevue)
        
        # Statut
        self.statut_combo = QComboBox()
        self.statut_combo.addItems(["Brouillon", "Validee", "Envoyee", "Partielle", "Livree", "Annulee"])
        info_layout.addRow("Statut:", self.statut_combo)
        
        # Montants
        self.total_ht = QDoubleSpinBox()
        self.total_ht.setMaximum(999999.99)
        self.total_ht.setPrefix("€ ")
        
        self.frais_port = QDoubleSpinBox()
        self.frais_port.setMaximum(9999.99)
        self.frais_port.setPrefix("€ ")
        
        info_layout.addRow("Total HT:", self.total_ht)
        info_layout.addRow("Frais de port:", self.frais_port)
        
        # Référence fournisseur
        self.reference_fournisseur = QLineEdit()
        info_layout.addRow("Réf. fournisseur:", self.reference_fournisseur)
        
        # Mode de paiement
        self.mode_paiement = QComboBox()
        self.mode_paiement.addItems(["Virement", "Chèque", "Carte", "Prélèvement", "Autre"])
        info_layout.addRow("Mode de paiement:", self.mode_paiement)
        
        # Notes
        self.notes = QLineEdit()
        info_layout.addRow("Notes:", self.notes)
        
        info_group.setLayout(info_layout)
        
        # Groupe pour les lignes de commande
        self.lignes_group = QGroupBox("Lignes de commande")
        lignes_layout = QVBoxLayout()
        
        # Créer d'abord les boutons
        self.add_ligne_btn = QPushButton("Ajouter une ligne")
        self.edit_ligne_btn = QPushButton("Modifier")
        self.del_ligne_btn = QPushButton("Supprimer")
        
        # Désactiver les boutons d'édition et suppression initialement
        self.edit_ligne_btn.setEnabled(False)
        self.del_ligne_btn.setEnabled(False)
        
        # Boutons d'action pour les lignes
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.add_ligne_btn)
        btn_layout.addWidget(self.edit_ligne_btn)
        btn_layout.addWidget(self.del_ligne_btn)
        
        # Tableau des lignes de commande
        self.lignes_table = QTableWidget()
        self.lignes_table.setColumnCount(6)  # 6 colonnes
        self.lignes_table.setHorizontalHeaderLabels([
            "Référence", 
            "Désignation", 
            "Qté", 
            "Prix unitaire", 
            "Total",
            "Description"
        ])
        self.lignes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.lignes_table.horizontalHeader().setStretchLastSection(True)  # Étirer la dernière colonne
        # Connexion pour activer/désactiver dynamiquement les boutons selon la sélection
        self.lignes_table.itemSelectionChanged.connect(self.on_ligne_selection_changed)
        
        lignes_layout.addWidget(self.lignes_table)
        lignes_layout.addLayout(btn_layout)
        self.lignes_group.setLayout(lignes_layout)
        
        # Section pour les actions de statut
        self.status_label = QLabel("<b>Actions sur la commande :</b>")
        self.status_widget = QWidget()
        self.status_layout = QHBoxLayout()
        
        # Boutons de gestion des statuts
        self.confirmer_btn = QPushButton("Confirmer")
        self.confirmer_btn.setToolTip("Passer de Brouillon à Validée")
        
        self.envoyer_btn = QPushButton("Envoyer")
        self.envoyer_btn.setToolTip("Passer de Validée à Envoyée")
        
        self.livrer_btn = QPushButton("Livrer")
        self.livrer_btn.setToolTip("Passer d'Envoyée à Livrée et créer les mouvements de stock")
        
        self.copier_btn = QPushButton("Copier")
        self.copier_btn.setToolTip("Créer une nouvelle commande avec les mêmes lignes")
        
        self.annuler_btn = QPushButton("Annuler commande")
        self.annuler_btn.setToolTip("Annuler la commande (devient inaccessible)")
        self.annuler_btn.setStyleSheet("QPushButton { background-color: #ff6b6b; color: white; }")
        
        # Ajouter les boutons au layout
        self.status_layout.addWidget(self.confirmer_btn)
        self.status_layout.addWidget(self.envoyer_btn)
        self.status_layout.addWidget(self.livrer_btn)
        self.status_layout.addWidget(self.copier_btn)
        self.status_layout.addStretch()
        self.status_layout.addWidget(self.annuler_btn)
        
        self.status_widget.setLayout(self.status_layout)
        
        # Séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        
        # Boutons de la boîte de dialogue
        button_box = QHBoxLayout()
        self.save_btn = QPushButton("Enregistrer")
        self.cancel_btn = QPushButton("Fermer")
        
        button_box.addStretch()
        button_box.addWidget(self.save_btn)
        button_box.addWidget(self.cancel_btn)
        
        # Ajout des groupes au layout principal
        layout.addWidget(info_group)
        layout.addWidget(self.lignes_group)
        
        # Toujours ajouter le séparateur et la section de statut
        layout.addWidget(separator)
        layout.addWidget(self.status_label)
        layout.addWidget(self.status_widget)
        
        # Contrôler la visibilité selon le mode
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
        
        # Connexions des signaux
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.add_ligne_btn.clicked.connect(self.add_ligne)
        self.edit_ligne_btn.clicked.connect(self.edit_ligne)
        self.del_ligne_btn.clicked.connect(self.del_ligne)
        
        # Connexions des boutons de statut (seulement en mode édition)
        if self.is_editing:
            self.confirmer_btn.clicked.connect(self.confirmer_commande)
            self.envoyer_btn.clicked.connect(self.envoyer_commande)
            self.livrer_btn.clicked.connect(self.livrer_commande)
            self.copier_btn.clicked.connect(self.copier_commande)
            self.annuler_btn.clicked.connect(self.annuler_commande)
    
    def load_fournisseurs(self):
        """Charge la liste des fournisseurs depuis la base de données"""
        try:
            print("Tentative de chargement des fournisseurs...")
            with self.db.conn.cursor() as cur:
                # Vérifier d'abord si la table existe (en minuscules)
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE  table_schema = 'public'
                        AND    table_name   = 'fournisseur'
                    );
                """)
                table_exists = cur.fetchone()[0]
                
                if not table_exists:
                    print("La table 'fournisseur' n'existe pas, tentative de création...")
                    # Créer la table si elle n'existe pas
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS fournisseur (
                            id_fournisseur SERIAL PRIMARY KEY,
                            nom TEXT NOT NULL UNIQUE,
                            contact TEXT,
                            adresse TEXT,
                            telephone TEXT,
                            email TEXT,
                            delai_livraison_moyen_j INTEGER,
                            devise TEXT DEFAULT 'EUR',
                            note_qualite REAL,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                        
                        -- Créer un fournisseur par défaut
                        INSERT INTO fournisseur (nom, telephone, email)
                        VALUES ('Fournisseur par défaut', '0102030405', 'contact@fournisseur.fr')
                        ON CONFLICT (nom) DO NOTHING;
                    """)
                    self.db.conn.commit()
                    print("Table 'fournisseur' créée avec succès avec un fournisseur par défaut")
                
                # Requête pour récupérer les fournisseurs
                query = """
                    SELECT id_fournisseur, nom, COALESCE(telephone, '') as reference
                    FROM fournisseur 
                    ORDER BY nom
                """
                
                print(f"Exécution de la requête: {query}")
                cur.execute(query)
                fournisseurs = cur.fetchall()
                
                print(f"{len(fournisseurs)} fournisseurs trouvés")
                
                self.fournisseur_combo.clear()
                for id_fournisseur, nom, reference in fournisseurs:
                    display_text = f"{nom} ({reference})" if reference else nom
                    self.fournisseur_combo.addItem(display_text, userData=id_fournisseur)
                
                # Sélectionner le premier fournisseur par défaut s'il y en a
                if self.fournisseur_combo.count() > 0:
                    self.fournisseur_combo.setCurrentIndex(0)
                else:
                    print("Aucun fournisseur trouvé dans la base de données")
                    self.fournisseur_combo.addItem("Aucun fournisseur disponible", None)
                    
        except Exception as e:
            error_msg = f"Impossible de charger la liste des fournisseurs :\n{str(e)}"
            print(error_msg)
            QMessageBox.critical(
                self, 
                "Erreur de chargement", 
                error_msg
            )
            # Ajouter un fournisseur vide pour éviter les erreurs
            self.fournisseur_combo.addItem("Aucun fournisseur disponible", None)
    
    def parse_date(self, date_str):
        """Convertit une chaîne de date en objet QDate"""
        if not date_str:
            return None
            
        try:
            # Essayer différents formats de date
            formats = [
                '%Y-%m-%d %H:%M:%S',  # Format SQL standard avec heure
                '%Y-%m-%d',            # Format SQL date seule
                '%d/%m/%Y %H:%M:%S',   # Format français avec heure
                '%d/%m/%Y'              # Format français date seule
            ]
            
            # Si c'est déjà un objet date ou datetime
            if hasattr(date_str, 'year') and hasattr(date_str, 'month') and hasattr(date_str, 'day'):
                return QDate(date_str.year, date_str.month, date_str.day)
                
            # Sinon, essayer de parser la chaîne
            for fmt in formats:
                try:
                    dt = datetime.strptime(str(date_str), fmt)
                    return QDate(dt.year, dt.month, dt.day)
                except ValueError:
                    continue
                    
            print(f"[WARNING] Format de date non reconnu: {date_str}")
            return None
            
        except Exception as e:
            print(f"[ERREUR] Erreur lors du parsing de la date {date_str}: {str(e)}")
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
                "Erreur de chargement", 
                f"Impossible de charger les données de la commande :\n{str(e)}"
            )
    
    def load_lignes_commande(self):
        """Charge les lignes de commande depuis la base de données"""
        if not self.commande_data or 'id_commande' not in self.commande_data:
            return
            
        try:
            # Récupérer les lignes de commande depuis la base de données
            from ..models.ligne_commande_repository import LigneCommandeRepository
            repo = LigneCommandeRepository(self.db)
            lignes = repo.get_lignes_by_commande(self.commande_data['id_commande'])
            
            # Vider le tableau
            self.lignes_table.setRowCount(0)
            
            # Remplir le tableau avec les lignes
            for ligne in lignes:
                row = self.lignes_table.rowCount()
                self.lignes_table.insertRow(row)
                
                # Calculer le total
                quantite = ligne.get('quantite_commandee', 0)
                prix_unitaire = float(ligne.get('prix_unitaire_ht', 0))
                total = quantite * prix_unitaire
                
                # Créer les cellules avec les données
                cells = [
                    QTableWidgetItem(ligne.get('piece_reference', '')),  # Référence
                    QTableWidgetItem(ligne.get('piece_nom', '')),        # Désignation
                    QTableWidgetItem(str(quantite)),                      # Quantité
                    QTableWidgetItem(f"{prix_unitaire:.2f} €"),         # Prix unitaire
                    QTableWidgetItem(f"{total:.2f} €"),                 # Total
                    QTableWidgetItem(ligne.get('description_libre', ''))  # Description
                ]
                
                # Ajouter les cellules au tableau
                for col, cell in enumerate(cells):
                    self.lignes_table.setItem(row, col, cell)
                    
                    # Stocker les données brutes dans la première cellule pour référence future
                    if col == 0:
                        cell.setData(Qt.UserRole, {
                            'piece_id': ligne.get('piece_id'),
                            'piece_reference': ligne.get('piece_reference', ''),
                            'piece_nom': ligne.get('piece_nom', ''),
                            'quantite_commandee': quantite,
                            'prix_unitaire_ht': prix_unitaire,
                            'description_libre': ligne.get('description_libre', '')
                        })
                
                # Activer les boutons d'édition et de suppression
                self.edit_ligne_btn.setEnabled(True)
                self.del_ligne_btn.setEnabled(True)
                
            # Ajuster la largeur des colonnes
            self.lignes_table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.warning(
                self, 
                "Erreur de chargement", 
                f"Impossible de charger les lignes de commande :\n{str(e)}"
            )
    
    def add_ligne(self):
        """Ouvre la boîte de dialogue pour ajouter une nouvelle ligne de commande"""
        from .ligne_commande_dialog import LigneCommandeDialog
        
        dialog = LigneCommandeDialog(self.db, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                # Calculer le total
                total = data['quantite_commandee'] * data['prix_unitaire_ht']
                
                # Ajouter la nouvelle ligne au tableau
                row = self.lignes_table.rowCount()
                self.lignes_table.insertRow(row)
                
                # Créer les cellules avec les données
                cells = [
                    QTableWidgetItem(data['piece_reference']),  # Référence
                    QTableWidgetItem(data['piece_nom']),        # Désignation
                    QTableWidgetItem(str(data['quantite_commandee'])),  # Quantité
                    QTableWidgetItem(f"{data['prix_unitaire_ht']:.2f} €"),  # Prix unitaire
                    QTableWidgetItem(f"{total:.2f} €"),  # Total
                    QTableWidgetItem(data.get('description_libre', ''))  # Description
                ]
                
                # Ajouter les cellules au tableau
                for col, cell in enumerate(cells):
                    self.lignes_table.setItem(row, col, cell)
                    
                    # Stocker les données brutes dans la première cellule pour référence future
                    if col == 0:
                        cell.setData(Qt.UserRole, data)
                
                # Ajuster la largeur des colonnes
                self.lignes_table.resizeColumnsToContents()
                
                # Activer les boutons d'édition et de suppression
                self.edit_ligne_btn.setEnabled(True)
                self.del_ligne_btn.setEnabled(True)
    
    def get_lignes_data(self):
        """Retourne une liste des lignes de commande"""
        lignes = []
        for row in range(self.lignes_table.rowCount()):
            data = self.lignes_table.item(row, 0).data(Qt.UserRole)
            if data:
                # Extraction robuste des primitives
                # Extraction robuste de l'identifiant de la pièce
                if isinstance(data['piece_id'], dict):
                    piece_id = data['piece_id'].get('piece_id') or data['piece_id'].get('id_piece')
                else:
                    piece_id = data['piece_id']
                quantite = data['quantite_commandee']
                if isinstance(quantite, dict):
                    quantite = list(quantite.values())[0]
                prix_unitaire = data['prix_unitaire_ht']
                if isinstance(prix_unitaire, dict):
                    prix_unitaire = list(prix_unitaire.values())[0]
                description = data.get('description_libre', None)
                if isinstance(description, dict):
                    description = list(description.values())[0]
                ligne_data = {
                    'piece_id': piece_id,
                    'quantite_commandee': quantite,
                    'prix_unitaire_ht': float(prix_unitaire),
                    'description_libre': description or None
                }
                lignes.append({k: v for k, v in ligne_data.items() if v is not None})
        return lignes
    
    def edit_ligne(self):
        """Ouvre la boîte de dialogue pour modifier la ligne sélectionnée"""
        row = self.lignes_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aucune sélection", "Veuillez sélectionner une ligne à modifier.")
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
        """Supprime la ligne sélectionnée du tableau des lignes de commande"""
        row = self.lignes_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aucune sélection", "Veuillez sélectionner une ligne à supprimer.")
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
        Retourne un dictionnaire avec les données du formulaire
        
        Returns:
            dict: Les données du formulaire ou None si la validation échoue
        """
        # Valider qu'un fournisseur est sélectionné
        fournisseur_id = self.fournisseur_combo.currentData()
        if not fournisseur_id:
            QMessageBox.warning(
                self,
                "Champ requis",
                "Veuillez sélectionner un fournisseur."
            )
            return None
            
        # Valider que des lignes de commande sont présentes
        lignes = self.get_lignes_data()
        if not lignes:
            QMessageBox.warning(
                self,
                "Commande vide",
                "Veuillez ajouter au moins une ligne de commande."
            )
            return None
            
        # Valider le numéro de commande
        numero_commande = self.numero_commande.text().strip()
        if not numero_commande:
            QMessageBox.warning(
                self,
                "Champ requis",
                "Veuillez saisir un numéro de commande."
            )
            return None
        
        # Calculer le total HT à partir des lignes
        total_ht = sum(ligne['prix_unitaire_ht'] * ligne['quantite_commandee'] for ligne in lignes)
        
        # Valeurs par défaut pour une nouvelle commande
        self.fields = {
            'fournisseur_id': None,
            'numero_commande': '',
            'date_commande': datetime.now().strftime('%Y-%m-%d'),
            'date_livraison_prevue': '',
            'statut': 'Brouillon',  # Utilisation d'une valeur valide selon la contrainte CHECK
            'total_ht': 0.0,
            'frais_port': 0.0,
            'reference_fournisseur': '',
            'mode_paiement': '',
            'notes_commande': ''
        }
        
        # S'assurer que le statut est valide
        statut = self.statut_combo.currentText()
        statuts_valides = ['Brouillon', 'Validee', 'Envoyee', 'Partielle', 'Livree', 'Annulee']
        if statut not in statuts_valides:
            statut = 'Brouillon'  # Valeur par défaut si le statut n'est pas valide
            
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
        
        # Ajouter l'ID si on est en mode édition
        if self.commande_data and 'id_commande' in self.commande_data:
            data['id_commande'] = self.commande_data['id_commande']
        
        return data
    
    def get_lignes_data(self):
        """Retourne une liste des lignes de commande"""
        lignes = []
        for row in range(self.lignes_table.rowCount()):
            # Récupérer les données brutes de la pièce
            piece_data = self.lignes_table.item(row, 0).data(Qt.UserRole)
            
            # Si piece_data est un dictionnaire, extraire l'ID
            if isinstance(piece_data, dict):
                piece_id = piece_data.get('piece_id')
                # Si piece_id est un dictionnaire (au cas où), extraire l'ID depuis le dictionnaire
                if isinstance(piece_id, dict):
                    piece_id = piece_id.get('id_piece') or piece_id.get('piece_id')
            else:
                piece_id = piece_data
            
            ligne = {
                'piece_id': piece_id,  # ID de la pièce extrait correctement
                'piece_reference': self.lignes_table.item(row, 0).text(),
                'piece_nom': self.lignes_table.item(row, 1).text(),
                'quantite_commandee': int(self.lignes_table.item(row, 2).text()),
                'prix_unitaire_ht': float(self.lignes_table.item(row, 3).text().replace('€', '').strip()),
                'description_libre': piece_data.get('description_libre', '') if isinstance(piece_data, dict) else ''
            }
            lignes.append(ligne)
        return lignes
    
    def update_status_buttons(self):
        """Met à jour la visibilité et l'état des boutons selon le statut actuel"""
        if not self.is_editing:
            return
            
        statut = self.commande_data.get('statut', 'Brouillon')
        print(f"[DEBUG] update_status_buttons: statut={statut}, is_editing={self.is_editing}")
        
        # S'assurer que le widget est visible
        if hasattr(self, 'status_widget'):
            self.status_widget.setVisible(True)
            print(f"[DEBUG] Widget de statut rendu visible: {self.status_widget.isVisible()}")
        
        # Désactiver tous les boutons par défaut
        self.confirmer_btn.setEnabled(False)
        self.envoyer_btn.setEnabled(False)
        self.livrer_btn.setEnabled(False)
        self.copier_btn.setEnabled(True)  # Toujours disponible
        self.annuler_btn.setEnabled(False)
        
        # Activer les boutons selon le statut
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
            # Commande terminée, seule la copie est possible
            pass
        elif statut == 'Annulee':
            # Commande annulée, seule la copie est possible
            pass
    
    def confirmer_commande(self):
        """Passe la commande de Brouillon à Validée"""
        if self._changer_statut('Validee'):
            QMessageBox.information(self, "Succès", "Commande confirmée avec succès.")
            self.update_status_buttons()
    
    def envoyer_commande(self):
        """Passe la commande de Validée à Envoyée"""
        if self._changer_statut('Envoyee'):
            QMessageBox.information(self, "Succès", "Commande envoyée au fournisseur.")
            self.update_status_buttons()
    
    def livrer_commande(self):
        """Passe la commande d'Envoyée à Livrée et crée les mouvements de stock"""
        reply = QMessageBox.question(
            self, 
            "Confirmer la livraison", 
            "Êtes-vous sûr de vouloir marquer cette commande comme livrée ?\n"
            "Cela créera automatiquement les mouvements d'entrée en stock.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Changer le statut
                if self._changer_statut('Livree'):
                    # Créer les mouvements de stock
                    self._creer_mouvements_livraison()
                    QMessageBox.information(
                        self, 
                        "Succès", 
                        "Commande livrée avec succès.\nLes mouvements de stock ont été créés."
                    )
                    self.update_status_buttons()
                    self.commande_livree.emit()  # Émettre le signal pour rafraîchir la vue
            except Exception as e:
                QMessageBox.critical(
                    self, 
                    "Erreur", 
                    f"Erreur lors de la livraison de la commande :\n{str(e)}"
                )
    
    def copier_commande(self):
        """Crée une nouvelle commande avec les mêmes lignes"""
        reply = QMessageBox.question(
            self, 
            "Copier la commande", 
            "Voulez-vous créer une nouvelle commande avec les mêmes lignes ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self._creer_copie_commande()
                QMessageBox.information(
                    self, 
                    "Succès", 
                    "Nouvelle commande créée avec succès."
                )
            except Exception as e:
                QMessageBox.critical(
                    self, 
                    "Erreur", 
                    f"Erreur lors de la copie de la commande :\n{str(e)}"
                )
    
    def annuler_commande(self):
        """Annule la commande"""
        reply = QMessageBox.question(
            self, 
            "Annuler la commande", 
            "Êtes-vous sûr de vouloir annuler cette commande ?\n"
            "Cette action est irréversible.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self._changer_statut('Annulee'):
                QMessageBox.information(self, "Succès", "Commande annulée.")
                self.update_status_buttons()
    
    def _changer_statut(self, nouveau_statut):
        """Change le statut de la commande dans la base de données"""
        try:
            from ..models.commande_repository import CommandeRepository
            repo = CommandeRepository(self.db)
            
            # Mettre à jour le statut
            commande_data = {'statut': nouveau_statut}
            if nouveau_statut == 'Livree':
                commande_data['date_livraison_reelle'] = datetime.now().strftime('%Y-%m-%d')
            
            success = repo.update_commande(self.commande_data['id_commande'], commande_data)
            
            if success:
                # Mettre à jour les données locales
                self.commande_data['statut'] = nouveau_statut
                if nouveau_statut == 'Livree':
                    self.commande_data['date_livraison_reelle'] = commande_data['date_livraison_reelle']
                
                # Mettre à jour l'affichage du statut
                index = self.statut_combo.findText(nouveau_statut, Qt.MatchFixedString)
                if index >= 0:
                    self.statut_combo.setCurrentIndex(index)
                
                return True
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de changer le statut de la commande.")
                return False
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du changement de statut :\n{str(e)}")
            return False
    
    def _creer_mouvements_livraison(self):
        """Crée les mouvements de stock pour la livraison de la commande"""
        try:
            from ..services.mouvement_service import MouvementService
            from ..models.ligne_commande_repository import LigneCommandeRepository
            
            mouvement_service = MouvementService(self.db)
            ligne_repo = LigneCommandeRepository(self.db)
            
            # Récupérer les lignes de commande
            lignes = ligne_repo.get_lignes_by_commande(self.commande_data['id_commande'])
            
            # Récupérer le type de mouvement ENTREE_ACHAT
            types_mouvement = mouvement_service.get_all_types_mouvement()
            type_entree_achat = next((t for t in types_mouvement if t['nom'] == 'ENTREE_ACHAT'), None)
            
            if not type_entree_achat:
                raise ValueError("Type de mouvement ENTREE_ACHAT non trouvé")
            
            # Créer un mouvement pour chaque ligne de commande
            for ligne in lignes:
                mouvement_service.creer_mouvement_entree(
                    piece_id=ligne['piece_id'],
                    quantite=ligne['quantite_commandee'],
                    type_mouvement_id=type_entree_achat['id'],
                    reference_document=f"CMD-{self.commande_data['numero_commande']}",
                    commentaire=f"Livraison commande {self.commande_data['numero_commande']}",
                    cout_unitaire=ligne.get('prix_unitaire_ht')
                )
            
            print(f"Mouvements de stock créés pour {len(lignes)} lignes de commande")
            
        except Exception as e:
            print(f"Erreur lors de la création des mouvements : {str(e)}")
            raise
    
    def _creer_copie_commande(self):
        """Crée une copie de la commande avec un nouveau numéro"""
        try:
            from ..models.commande_repository import CommandeRepository
            from ..models.ligne_commande_repository import LigneCommandeRepository
            
            commande_repo = CommandeRepository(self.db)
            ligne_repo = LigneCommandeRepository(self.db)
            
            # Générer un nouveau numéro de commande
            nouveau_numero = self._generer_nouveau_numero()
            
            # Préparer les données de la nouvelle commande
            nouvelle_commande_data = {
                'numero_commande': nouveau_numero,
                'fournisseur_id': self.commande_data['fournisseur_id'],
                'createur_id': commande_repo.get_default_user_id(),
                'date_commande': datetime.now().strftime('%Y-%m-%d'),
                'date_livraison_prevue': self.commande_data.get('date_livraison_prevue'),
                'statut': 'Brouillon',
                'total_ht': self.commande_data.get('total_ht', 0),
                'frais_port': self.commande_data.get('frais_port', 0),
                'reference_fournisseur': self.commande_data.get('reference_fournisseur'),
                'mode_paiement': self.commande_data.get('mode_paiement'),
                'notes_commande': f"Copie de la commande {self.commande_data['numero_commande']}"
            }
            
            # Créer la nouvelle commande
            nouvelle_commande_id = commande_repo.add_commande(nouvelle_commande_data)
            
            # Récupérer et copier les lignes de commande
            lignes_originales = ligne_repo.get_lignes_by_commande(self.commande_data['id_commande'])
            
            for ligne in lignes_originales:
                nouvelle_ligne_data = {
                    'commande_id': nouvelle_commande_id,
                    'piece_id': ligne['piece_id'],
                    'quantite_commandee': ligne['quantite_commandee'],
                    'prix_unitaire_ht': ligne['prix_unitaire_ht'],
                    'description_libre': ligne.get('description_libre')
                }
                ligne_repo.add_ligne_commande(nouvelle_ligne_data)
            
            print(f"Nouvelle commande créée avec l'ID {nouvelle_commande_id} et le numéro {nouveau_numero}")
            
        except Exception as e:
            print(f"Erreur lors de la copie : {str(e)}")
            raise
    
    def _generer_nouveau_numero(self):
        """Génère un nouveau numéro de commande unique"""
        try:
            from ..models.commande_repository import CommandeRepository
            repo = CommandeRepository(self.db)
            
            # Récupérer toutes les commandes pour trouver le prochain numéro
            commandes = repo.get_all_commandes()
            
            # Extraire les numéros numériques
            numeros = []
            for cmd in commandes:
                try:
                    numero = int(cmd['numero_commande'])
                    numeros.append(numero)
                except (ValueError, TypeError):
                    continue
            
            # Générer le prochain numéro
            if numeros:
                prochain_numero = max(numeros) + 1
            else:
                prochain_numero = 1
            
            return str(prochain_numero)
            
        except Exception as e:
            # En cas d'erreur, utiliser un timestamp
            return f"CMD-{int(datetime.now().timestamp())}"
