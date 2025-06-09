from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QComboBox, 
                             QSpinBox, QDoubleSpinBox, QLineEdit, QPushButton,
                             QDialogButtonBox, QMessageBox)
from PySide6.QtCore import Qt

class LigneCommandeDialog(QDialog):
    def __init__(self, db, piece_data=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.piece_data = piece_data or {}
        self.setWindowTitle("Modifier une ligne" if piece_data else "Nouvelle ligne")
        self.setMinimumWidth(400)
        
        self.init_ui()
        self.load_pieces()
        
        if piece_data:
            self.load_piece_data()
    
    def init_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        # Sélection de la pièce
        self.piece_combo = QComboBox()
        self.piece_combo.setEditable(True)
        form_layout.addRow("Pièce:", self.piece_combo)
        
        # Champs pour les détails de la pièce (en lecture seule)
        self.reference = QLineEdit()
        self.reference.setReadOnly(True)
        form_layout.addRow("Référence:", self.reference)
        
        self.designation = QLineEdit()
        self.designation.setReadOnly(True)
        form_layout.addRow("Désignation:", self.designation)
        
        # Quantité
        self.quantite = QSpinBox()
        self.quantite.setMinimum(1)
        self.quantite.setMaximum(9999)
        form_layout.addRow("Quantité:", self.quantite)
        
        # Prix unitaire
        self.prix_unitaire = QDoubleSpinBox()
        self.prix_unitaire.setMinimum(0)
        self.prix_unitaire.setMaximum(999999.99)
        self.prix_unitaire.setPrefix("€ ")
        form_layout.addRow("Prix unitaire HT:", self.prix_unitaire)
        
        # Description libre
        self.description = QLineEdit()
        form_layout.addRow("Description:", self.description)
        
        # Boutons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.validate)
        button_box.rejected.connect(self.reject)
        
        # Connexion du changement de pièce
        self.piece_combo.currentIndexChanged.connect(self.on_piece_changed)
        
        layout.addLayout(form_layout)
        layout.addWidget(button_box)
        self.setLayout(layout)
    
    def load_pieces(self):
        """Charge la liste des pièces depuis la base de données"""
        print("Début du chargement des pièces...")
        try:
            with self.db.conn.cursor() as cur:
                print("Connexion à la base de données établie")
                
                # Vérifier le contenu de la table piece
                cur.execute("SELECT COUNT(*) FROM piece")
                count = cur.fetchone()[0]
                print(f"Nombre total de pièces dans la table: {count}")
                
                # Afficher les premières lignes pour le débogage
                if count > 0:
                    cur.execute("SELECT id_piece, reference, nom, statut, stock_actuel FROM piece LIMIT 5")
                    print("\nExemple de pièces dans la table:")
                    for row in cur.fetchall():
                        print(f"ID: {row[0]}, Réf: {row[1]}, Nom: {row[2]}, Statut: {row[3]}, Stock: {row[4]}")
                
                # Vérifier d'abord si la table existe
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE  table_schema = 'public'
                        AND    table_name   = 'piece'
                    );
                """)
                table_exists = cur.fetchone()[0]
                
                if not table_exists:
                    QMessageBox.warning(
                        self,
                        "Table manquante",
                        "La table 'piece' n'existe pas dans la base de données."
                    )
                    return
                
                # Récupérer la liste des pièces actives avec leur stock disponible
                query = """
                    SELECT 
                        p.id_piece, 
                        p.reference, 
                        p.nom, 
                        COALESCE(p.prix_unitaire, 0) as prix_unitaire, 
                        p.stock_actuel,
                        p.stock_alerte,
                        p.unite,
                        p.categorie,
                        p.statut
                    FROM piece p
                    WHERE (LOWER(p.statut) = 'actif' OR p.statut IS NULL)  -- Accepter les pièces sans statut
                    AND (p.stock_actuel > 0 OR p.stock_actuel IS NULL)  -- Accepter les pièces sans stock défini
                    ORDER BY p.reference
                """
                print("Exécution de la requête SQL:", query)
                cur.execute(query)
                rows = cur.fetchall()
                print(f"{len(rows)} pièces trouvées dans la base de données")
                
                self.pieces = []
                self.piece_combo.clear()
                self.piece_combo.addItem("Sélectionner une pièce", None)
                
                for row in rows:
                    try:
                        id_piece, reference, nom, prix_unitaire, stock_actuel, stock_alerte, unite, categorie, statut = row
                        print(f"Traitement de la pièce: {reference} - {nom} (ID: {id_piece})")
                        
                        # Créer le dictionnaire de la pièce avec toutes les informations
                        piece = {
                            'id': id_piece,
                            'reference': reference or '',
                            'nom': nom or '',
                            'prix': float(prix_unitaire) if prix_unitaire is not None else 0.0,
                            'stock': int(stock_actuel) if stock_actuel is not None else 0,
                            'stock_alerte': int(stock_alerte) if stock_alerte is not None else 0,
                            'unite': unite or 'pièce',
                            'categorie': categorie or 'Non catégorisé',
                            'statut': statut or 'Actif'
                        }
                        
                        # Ajouter la pièce à la liste
                        self.pieces.append(piece)
                        
                        # Ajouter la pièce à la liste déroulante
                        display_text = f"{piece['reference']} - {piece['nom']} ({piece['stock']} {piece['unite']})"
                        print(f"Ajout au combobox: {display_text}")
                        self.piece_combo.addItem(display_text, id_piece)
                        
                    except Exception as e:
                        print(f"Erreur lors du traitement d'une pièce: {str(e)}")
                        import traceback
                        traceback.print_exc()
                    
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Impossible de charger la liste des pièces :\n{str(e)}"
            )
    
    def load_piece_data(self):
        if not self.piece_data:
            return
            
        # À implémenter: Charger les données de la pièce sélectionnée
        pass
    
    def on_piece_changed(self, index):
        # Récupérer l'ID de la pièce sélectionnée
        piece_id = self.piece_combo.currentData()
        
        # Réinitialiser les champs si aucune pièce n'est sélectionnée
        if not piece_id:
            self.reference.clear()
            self.designation.clear()
            self.quantite.setValue(1)
            self.prix_unitaire.setValue(0.0)
            return
            
        # Trouver la pièce sélectionnée
        piece = next((p for p in self.pieces if p['id'] == piece_id), None)
        if not piece:
            return
            
        # Mettre à jour les champs avec les informations de la pièce
        self.reference.setText(piece['reference'])
        self.designation.setText(piece['nom'])
        
        # Utiliser le prix de la pièce comme valeur par défaut
        prix_piece = piece.get('prix', 0.0)
        self.prix_unitaire.setValue(prix_piece)
        
        # Définir la quantité maximale en fonction du stock disponible
        stock_disponible = piece.get('stock', 0)
        stock_alerte = piece.get('stock_alerte', 0)
        
        # Configurer le spinbox de quantité
        self.quantite.setMaximum(max(1, stock_disponible))
        self.quantite.setValue(1)
        
        # Si le stock est faible ou épuisé, afficher un message d'information
        if stock_disponible <= stock_alerte or stock_disponible <= 5:
            message = f"Stock limité : {stock_disponible} {piece.get('unite', 'pièce')} disponible(s)"
            if stock_disponible <= 0:
                message = "Stock épuisé !"
                
            QMessageBox.warning(
                self,
                "Alerte stock",
                f"{message}. Le stock d'alerte est de {stock_alerte} {piece.get('unite', 'pièce')}."
            )
    
    def validate(self):
        # Vérifier qu'une pièce est sélectionnée
        piece_id = self.piece_combo.currentData()
        if not piece_id:
            QMessageBox.warning(
                self, 
                "Sélection requise", 
                "Veuillez sélectionner une pièce dans la liste."
            )
            return False
            
        # Vérifier que la quantité est valide
        quantite = self.quantite.value()
        if quantite <= 0:
            QMessageBox.warning(
                self, 
                "Quantité invalide", 
                "La quantité doit être supérieure à zéro."
            )
            return False
            
        # Vérifier le stock disponible
        piece = next((p for p in getattr(self, 'pieces', []) if p['id'] == piece_id), None)
        if piece:
            stock_disponible = int(piece.get('stock', 0))
            if quantite > stock_disponible:
                QMessageBox.warning(
                    self,
                    "Stock insuffisant",
                    f"Stock insuffisant. Il ne reste que {stock_disponible} pièce(s) en stock."
                )
                return False
        
        # Vérifier que le prix est valide
        if self.prix_unitaire.value() <= 0:
            QMessageBox.warning(
                self,
                "Prix invalide",
                "Le prix unitaire doit être supérieur à zéro."
            )
            return False
            
        # Toutes les validations sont passées
        self.accept()
    
    def get_data(self):
        """Retourne un dictionnaire avec les données du formulaire"""
        return {
            'piece_id': self.piece_combo.currentData(),
            'piece_reference': self.reference.text(),
            'piece_nom': self.designation.text(),
            'quantite_commandee': self.quantite.value(),
            'prix_unitaire_ht': self.prix_unitaire.value(),
            'description_libre': self.description.text()
        }
