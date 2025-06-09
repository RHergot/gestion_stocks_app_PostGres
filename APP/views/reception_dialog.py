from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, 
                             QSpinBox, QPushButton, QMessageBox, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QLabel, QGroupBox,
                             QFrame, QWidget, QCheckBox, QTextEdit)
from PySide6.QtCore import Qt, QDate, Signal
from datetime import datetime

class ReceptionDialog(QDialog):
    """Dialog pour la réception détaillée d'une commande"""
    
    def __init__(self, db, commande_data, parent=None):
        super().__init__(parent)
        self.db = db
        self.commande_data = commande_data
        self.setWindowTitle(f"Réception Commande #{commande_data['numero_commande']}")
        self.setMinimumWidth(1000)
        self.setMinimumHeight(600)
        
        # Données de réception pour chaque ligne
        self.reception_data = {}
        
        self.init_ui()
        self.load_lignes_commande()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Informations de la commande
        info_group = QGroupBox("Informations de la commande")
        info_layout = QFormLayout()
        
        info_layout.addRow("Numéro:", QLabel(self.commande_data['numero_commande']))
        info_layout.addRow("Fournisseur:", QLabel(self.commande_data.get('fournisseur_nom', 'N/A')))
        info_layout.addRow("Date commande:", QLabel(self.commande_data.get('date_commande', 'N/A')))
        info_layout.addRow("Statut actuel:", QLabel(self.commande_data.get('statut', 'N/A')))
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Instructions
        instructions = QLabel(
            "<b>Instructions :</b><br>"
            "• Saisissez la quantité reçue pour chaque ligne<br>"
            "• Cochez 'Bon état' si les pièces sont conformes<br>"
            "• Les pièces défectueuses seront placées en retour fournisseur<br>"
            "• Vous pouvez ajouter des commentaires pour chaque ligne"
        )
        instructions.setStyleSheet("QLabel { background-color: #f0f8ff; padding: 10px; border: 1px solid #ccc; }")
        layout.addWidget(instructions)
        
        # Tableau de réception
        reception_group = QGroupBox("Lignes à réceptionner")
        reception_layout = QVBoxLayout()
        
        self.reception_table = QTableWidget()
        self.reception_table.setColumnCount(8)
        self.reception_table.setHorizontalHeaderLabels([
            "Pièce", 
            "Désignation", 
            "Qté Commandée", 
            "Qté Déjà Reçue",
            "Qté à Réceptionner", 
            "Bon État", 
            "Commentaire",
            "Statut"
        ])
        
        # Configuration du tableau
        header = self.reception_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Pièce
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Désignation
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Qté Commandée
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Qté Déjà Reçue
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Qté à Réceptionner
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Bon État
        header.setSectionResizeMode(6, QHeaderView.Stretch)           # Commentaire
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Statut
        
        reception_layout.addWidget(self.reception_table)
        reception_group.setLayout(reception_layout)
        layout.addWidget(reception_group)
        
        # Résumé
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("QLabel { background-color: #f9f9f9; padding: 10px; border: 1px solid #ddd; }")
        layout.addWidget(self.summary_label)
        
        # Boutons
        button_layout = QHBoxLayout()
        
        self.validate_btn = QPushButton("Valider la réception")
        self.validate_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 10px; }")
        self.validate_btn.clicked.connect(self.validate_reception)
        
        self.cancel_btn = QPushButton("Annuler")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.validate_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_lignes_commande(self):
        """Charge les lignes de commande dans le tableau"""
        try:
            from ..models.ligne_commande_repository import LigneCommandeRepository
            repo = LigneCommandeRepository(self.db)
            lignes = repo.get_lignes_by_commande(self.commande_data['id_commande'])
            
            self.reception_table.setRowCount(len(lignes))
            
            for row, ligne in enumerate(lignes):
                # Stocker les données de la ligne
                ligne_id = ligne['id_ligne']
                self.reception_data[ligne_id] = {
                    'ligne_data': ligne,
                    'quantite_a_receptionner': 0,
                    'bon_etat': True,
                    'commentaire': ''
                }
                
                # Colonne 0: Référence pièce
                ref_item = QTableWidgetItem(ligne.get('piece_reference', 'N/A'))
                ref_item.setFlags(ref_item.flags() & ~Qt.ItemIsEditable)
                self.reception_table.setItem(row, 0, ref_item)
                
                # Colonne 1: Désignation
                nom_item = QTableWidgetItem(ligne.get('piece_nom', ligne.get('description_libre', 'N/A')))
                nom_item.setFlags(nom_item.flags() & ~Qt.ItemIsEditable)
                self.reception_table.setItem(row, 1, nom_item)
                
                # Colonne 2: Quantité commandée
                qte_cmd_item = QTableWidgetItem(str(ligne.get('quantite_commandee', 0)))
                qte_cmd_item.setFlags(qte_cmd_item.flags() & ~Qt.ItemIsEditable)
                self.reception_table.setItem(row, 2, qte_cmd_item)
                
                # Colonne 3: Quantité déjà reçue
                qte_recue = ligne.get('quantite_recue', 0)
                qte_recue_item = QTableWidgetItem(str(qte_recue))
                qte_recue_item.setFlags(qte_recue_item.flags() & ~Qt.ItemIsEditable)
                self.reception_table.setItem(row, 3, qte_recue_item)
                
                # Colonne 4: Quantité à réceptionner (SpinBox)
                qte_restante = ligne.get('quantite_commandee', 0) - qte_recue
                qte_spinbox = QSpinBox()
                qte_spinbox.setMinimum(0)
                qte_spinbox.setMaximum(qte_restante)
                qte_spinbox.setValue(qte_restante)  # Par défaut, tout ce qui reste
                qte_spinbox.valueChanged.connect(lambda v, lid=ligne_id: self.update_reception_data(lid, 'quantite', v))
                self.reception_table.setCellWidget(row, 4, qte_spinbox)
                
                # Colonne 5: Bon état (CheckBox)
                bon_etat_widget = QWidget()
                bon_etat_layout = QHBoxLayout(bon_etat_widget)
                bon_etat_layout.setContentsMargins(0, 0, 0, 0)
                bon_etat_checkbox = QCheckBox()
                bon_etat_checkbox.setChecked(True)  # Par défaut, bon état
                bon_etat_checkbox.stateChanged.connect(lambda state, lid=ligne_id: self.update_reception_data(lid, 'bon_etat', state == Qt.Checked))
                bon_etat_layout.addWidget(bon_etat_checkbox)
                bon_etat_layout.setAlignment(Qt.AlignCenter)
                self.reception_table.setCellWidget(row, 5, bon_etat_widget)
                
                # Colonne 6: Commentaire
                commentaire_edit = QLineEdit()
                commentaire_edit.setPlaceholderText("Commentaire optionnel...")
                commentaire_edit.textChanged.connect(lambda text, lid=ligne_id: self.update_reception_data(lid, 'commentaire', text))
                self.reception_table.setCellWidget(row, 6, commentaire_edit)
                
                # Colonne 7: Statut de la ligne
                statut_actuel = ligne.get('statut_ligne', 'Attente')
                statut_item = QTableWidgetItem(statut_actuel)
                statut_item.setFlags(statut_item.flags() & ~Qt.ItemIsEditable)
                self.reception_table.setItem(row, 7, statut_item)
                
                # Initialiser les données de réception
                self.reception_data[ligne_id]['quantite_a_receptionner'] = qte_restante
            
            self.update_summary()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les lignes de commande :\n{str(e)}")
    
    def update_reception_data(self, ligne_id, field, value):
        """Met à jour les données de réception pour une ligne"""
        if ligne_id in self.reception_data:
            if field == 'quantite':
                self.reception_data[ligne_id]['quantite_a_receptionner'] = value
            elif field == 'bon_etat':
                self.reception_data[ligne_id]['bon_etat'] = value
            elif field == 'commentaire':
                self.reception_data[ligne_id]['commentaire'] = value
            
            self.update_summary()
    
    def update_summary(self):
        """Met à jour le résumé de la réception"""
        total_lignes = len(self.reception_data)
        lignes_avec_reception = sum(1 for data in self.reception_data.values() if data['quantite_a_receptionner'] > 0)
        total_pieces_a_receptionner = sum(data['quantite_a_receptionner'] for data in self.reception_data.values())
        pieces_bon_etat = sum(data['quantite_a_receptionner'] for data in self.reception_data.values() if data['bon_etat'])
        pieces_defectueuses = total_pieces_a_receptionner - pieces_bon_etat
        
        summary_text = f"""
        <b>Résumé de la réception :</b><br>
        • Lignes à traiter : {lignes_avec_reception}/{total_lignes}<br>
        • Total pièces à réceptionner : {total_pieces_a_receptionner}<br>
        • Pièces en bon état : {pieces_bon_etat}<br>
        • Pièces défectueuses : {pieces_defectueuses}
        """
        
        self.summary_label.setText(summary_text)
    
    def validate_reception(self):
        """Valide et traite la réception"""
        try:
            # Vérifier qu'il y a au moins une ligne à réceptionner
            lignes_a_traiter = [data for data in self.reception_data.values() if data['quantite_a_receptionner'] > 0]
            
            if not lignes_a_traiter:
                QMessageBox.warning(self, "Aucune réception", "Aucune quantité à réceptionner n'a été saisie.")
                return
            
            # Demander confirmation
            reply = QMessageBox.question(
                self,
                "Confirmer la réception",
                f"Confirmer la réception de {len(lignes_a_traiter)} ligne(s) ?\n"
                "Cette action créera les mouvements de stock correspondants.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.process_reception()
                self.accept()
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la validation :\n{str(e)}")
    
    def process_reception(self):
        """Traite la réception : met à jour la base de données et crée les mouvements"""
        try:
            from ..models.ligne_commande_repository import LigneCommandeRepository
            from ..services.mouvement_service import MouvementService
            
            ligne_repo = LigneCommandeRepository(self.db)
            mouvement_service = MouvementService(self.db)
            
            # Récupérer les types de mouvement
            types_mouvement = mouvement_service.get_all_types_mouvement()
            type_entree_achat = next((t for t in types_mouvement if t['nom'] == 'ENTREE_ACHAT'), None)
            type_retour_fournisseur = next((t for t in types_mouvement if t['nom'] == 'SORTIE_RETOUR_FOURNISSEUR'), None)
            
            if not type_entree_achat:
                raise ValueError("Type de mouvement ENTREE_ACHAT non trouvé")
            
            # Récupérer l'emplacement pour les pièces défectueuses
            emplacement_defectueux = self.get_emplacement_defectueux()
            
            mouvements_crees = 0
            
            for ligne_id, reception_info in self.reception_data.items():
                quantite = reception_info['quantite_a_receptionner']
                if quantite <= 0:
                    continue
                
                ligne_data = reception_info['ligne_data']
                bon_etat = reception_info['bon_etat']
                commentaire = reception_info['commentaire']
                
                # Mettre à jour la ligne de commande
                nouvelle_quantite_recue = ligne_data.get('quantite_recue', 0) + quantite
                update_data = {
                    'quantite_recue': nouvelle_quantite_recue,
                    'date_derniere_reception': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'commentaire_reception': commentaire
                }
                
                # Si pièces défectueuses, mettre à jour aussi quantite_defectueuse
                if not bon_etat:
                    nouvelle_quantite_defectueuse = ligne_data.get('quantite_defectueuse', 0) + quantite
                    update_data['quantite_defectueuse'] = nouvelle_quantite_defectueuse
                
                ligne_repo.update_ligne_commande(ligne_id, update_data)
                
                # Créer l'historique de réception
                self.create_reception_detail(ligne_id, quantite, 0 if bon_etat else quantite, commentaire)
                
                # Créer les mouvements de stock
                if bon_etat:
                    # Mouvement d'entrée pour les pièces en bon état
                    mouvement_service.creer_mouvement_entree(
                        piece_id=ligne_data['piece_id'],
                        quantite=quantite,
                        type_mouvement_id=type_entree_achat['id'],
                        reference_document=f"CMD-{self.commande_data['numero_commande']}",
                        commentaire=f"Réception commande {self.commande_data['numero_commande']} - {commentaire}",
                        cout_unitaire=ligne_data.get('prix_unitaire_ht')
                    )
                    mouvements_crees += 1
                else:
                    # Mouvement de retour pour les pièces défectueuses
                    if type_retour_fournisseur:
                        mouvement_service.creer_mouvement_sortie(
                            piece_id=ligne_data['piece_id'],
                            quantite=quantite,
                            type_mouvement_id=type_retour_fournisseur['id'],
                            emplacement_source_id=emplacement_defectueux,
                            reference_document=f"CMD-{self.commande_data['numero_commande']}-DEF",
                            commentaire=f"Retour pièces défectueuses - {commentaire}"
                        )
                        mouvements_crees += 1
            
            # Mettre à jour le statut de la commande
            self.update_commande_status()
            
            print(f"[INFO] Réception traitée: {mouvements_crees} mouvements créés")
            
        except Exception as e:
            print(f"[ERREUR] Erreur lors du traitement de la réception: {e}")
            raise
    
    def create_reception_detail(self, ligne_id, quantite_recue, quantite_defectueuse, commentaire):
        """Crée un enregistrement dans l'historique des réceptions"""
        try:
            with self.db.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO reception_detail (
                        ligne_commande_id, quantite_recue, quantite_defectueuse, 
                        utilisateur_id, commentaire
                    ) VALUES (%s, %s, %s, %s, %s)
                """, (ligne_id, quantite_recue, quantite_defectueuse, 1, commentaire))  # TODO: récupérer l'utilisateur actuel
                self.db.conn.commit()
        except Exception as e:
            print(f"[ERREUR] Impossible de créer l'historique de réception: {e}")
    
    def get_emplacement_defectueux(self):
        """Récupère l'ID de l'emplacement pour les pièces défectueuses"""
        try:
            with self.db.conn.cursor() as cur:
                cur.execute("SELECT id FROM emplacement WHERE nom = 'DEFECTUEUX' LIMIT 1")
                result = cur.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"[ERREUR] Impossible de récupérer l'emplacement défectueux: {e}")
            return None
    
    def update_commande_status(self):
        """Met à jour le statut de la commande selon l'état des lignes"""
        try:
            from ..models.ligne_commande_repository import LigneCommandeRepository
            from ..models.commande_repository import CommandeRepository
            
            ligne_repo = LigneCommandeRepository(self.db)
            commande_repo = CommandeRepository(self.db)
            
            # Récupérer toutes les lignes de la commande
            lignes = ligne_repo.get_lignes_by_commande(self.commande_data['id_commande'])
            
            # Calculer le statut global
            total_lignes = len(lignes)
            lignes_completes = 0
            lignes_partielles = 0
            
            for ligne in lignes:
                quantite_commandee = ligne.get('quantite_commandee', 0)
                quantite_recue = ligne.get('quantite_recue', 0)
                quantite_defectueuse = ligne.get('quantite_defectueuse', 0)
                
                if quantite_recue + quantite_defectueuse >= quantite_commandee:
                    lignes_completes += 1
                elif quantite_recue + quantite_defectueuse > 0:
                    lignes_partielles += 1
            
            # Déterminer le nouveau statut
            if lignes_completes == total_lignes:
                nouveau_statut = 'Livree'
            elif lignes_completes > 0 or lignes_partielles > 0:
                nouveau_statut = 'Partielle'
            else:
                nouveau_statut = 'Envoyee'  # Reste en envoyée si rien n'est reçu
            
            # Mettre à jour la commande
            update_data = {'statut': nouveau_statut}
            if nouveau_statut == 'Livree':
                update_data['date_livraison_reelle'] = datetime.now().strftime('%Y-%m-%d')
            
            commande_repo.update_commande(self.commande_data['id_commande'], update_data)
            
            print(f"[INFO] Statut de la commande mis à jour: {nouveau_statut}")
            
        except Exception as e:
            print(f"[ERREUR] Impossible de mettre à jour le statut de la commande: {e}")
    
    def get_reception_summary(self):
        """Retourne un résumé de la réception pour affichage"""
        lignes_traitees = [data for data in self.reception_data.values() if data['quantite_a_receptionner'] > 0]
        total_pieces = sum(data['quantite_a_receptionner'] for data in lignes_traitees)
        pieces_bon_etat = sum(data['quantite_a_receptionner'] for data in lignes_traitees if data['bon_etat'])
        pieces_defectueuses = total_pieces - pieces_bon_etat
        
        return {
            'lignes_traitees': len(lignes_traitees),
            'total_pieces': total_pieces,
            'pieces_bon_etat': pieces_bon_etat,
            'pieces_defectueuses': pieces_defectueuses
        }