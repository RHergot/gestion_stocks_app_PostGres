"""Modèles de données pour les commandes (QAbstractTableModel).

Extrait de commande_view.py — contient CommandeTableModel et LigneCommandeTableModel.
"""
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex

class CommandeTableModel(QAbstractTableModel):
    HEADER_LABELS = {
        "id_commande": "ID",
        "numero_commande": "Order No.",
        "fournisseur_nom": "Supplier",
        "createur_nom": "Creator",
        "date_commande": "Order date",
        "date_livraison_prevue": "Planned delivery",
        "date_livraison_reelle": "Actual delivery",
        "statut": "Status",
        "total_ht": "Total (excl. tax)",
        "frais_port": "Shipping cost",
        "reference_fournisseur": "Supplier ref.",
        "mode_paiement": "Payment method",
        "notes_commande": "Notes",
        "created_at": "Created at",
        "updated_at": "Updated at"
    }

    def __init__(self, commandes):
        super().__init__()
        self.commandes = commandes or []
        
        # Utilise les clés de HEADER_LABELS pour garantir l'ordre et la présence de toutes les colonnes
        self.headers = list(self.HEADER_LABELS.keys())
        
        # Debug log
        if not self.commandes:
            print("[DEBUG] No data provided to order model")
        elif not isinstance(self.commandes[0], dict):
            print(f"[ERROR] Data must be dictionaries, got: {type(self.commandes[0])}")
        else:
            print(f"[DEBUG] Model initialized with {len(self.commandes)} orders")
            print(f"[DEBUG] Model headers: {self.headers}")
            if self.commandes:
                print(f"[DEBUG] First order keys: {list(self.commandes[0].keys())}")

    def rowCount(self, parent=None):
        return len(self.commandes)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
            
        if role == Qt.UserRole:
            # Retourne l'ID de la commande pour la ligne (utilisé par select_commande)
            row = index.row()
            if row < len(self.commandes):
                return self.commandes[row].get("id_commande")
            return None

        if role == Qt.DisplayRole or role == Qt.EditRole:
            row = index.row()
            col = index.column()
            
            if row >= len(self.commandes) or col >= len(self.headers):
                return None
                
            key = self.headers[col]
            commande = self.commandes[row]
            
            # Debug log (only once for first cell)
            if row == 0 and col == 0 and not hasattr(self, '_debug_shown'):
                print(f"[DEBUG] Displaying first cell. Key: {key}, Value: {commande.get(key, 'N/A')}")
                self._debug_shown = True
            
            # Raw value
            value = commande.get(key, "")
            
            # Special formatting for dates
            if key in ["date_commande", "date_livraison_prevue", "date_livraison_reelle", "created_at", "updated_at"] and value:
                try:
                    from datetime import datetime
                    # Try multiple date formats
                    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
                        try:
                            dt = datetime.strptime(str(value).split('.')[0], fmt)  # Remove microseconds
                            # Display as DD/MM/YYYY
                            return dt.strftime("%d/%m/%Y")
                        except ValueError:
                            continue
                except (ValueError, TypeError) as e:
                    print(f"[DEBUG] Date formatting error {key}={value}: {str(e)}")
            
            # Formatage des montants
            elif key in ["total_ht", "frais_port"] and value is not None:
                try:
                    return f"{float(value):.2f} €"
                except (ValueError, TypeError):
                    pass
            
            # Pour les valeurs booléennes
            elif isinstance(value, bool):
                return "Yes" if value else "No"
            
            # Pour les valeurs None, retourne une chaîne vide
            if value is None:
                return ""
                
            # Pour les autres cas, retourne la valeur convertie en chaîne
            return str(value)
            
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section < len(self.headers):
                    key = self.headers[section]
                    return self.HEADER_LABELS.get(key, key)
            else:
                return section + 1
        return None


class LigneCommandeTableModel(QAbstractTableModel):
    HEADER_LABELS = {
        "id_ligne": "Line ID",
        "piece_reference": "Part ref.",
        "piece_nom": "Part name",
        "description_libre": "Description",
        "quantite_commandee": "Qty ordered",
        "prix_unitaire_ht": "Unit price (excl. tax)",
        "quantite_recue": "Qty received",
        "date_reception": "Reception date",
        "statut_ligne": "Status",
        "commande_id": "Order ID",
        "piece_id": "Part ID"
    }

    def __init__(self, lignes):
        super().__init__()
        self.lignes = lignes or []
        
        # Utilise les clés de HEADER_LABELS pour garantir l'ordre et la présence de toutes les colonnes
        self.headers = list(self.HEADER_LABELS.keys())
        
        # Debug log
        if not self.lignes:
            print("[DEBUG] No data provided to order lines model")
        elif not isinstance(self.lignes[0], dict):
            print(f"[ERROR] Line data must be dictionaries, got: {type(self.lignes[0])}")
        elif self.lignes:
            print(f"[DEBUG] Lines model initialized with {len(self.lignes)} rows")
            print(f"[DEBUG] First line keys: {list(self.lignes[0].keys())}")

    def rowCount(self, parent=None):
        return len(self.lignes)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
            
        if role == Qt.UserRole:
            # Retourne l'ID de la commande pour la ligne (utilisé par select_commande)
            row = index.row()
            if row < len(self.commandes):
                return self.commandes[row].get("id_commande")
            return None

        if role == Qt.DisplayRole or role == Qt.EditRole:
            row = index.row()
            col = index.column()
            
            if row >= len(self.lignes) or col >= len(self.headers):
                return None
                
            key = self.headers[col]
            ligne = self.lignes[row]
            
            # Mise en forme spéciale pour certains champs
            value = ligne.get(key, "")
            
            # Formatage des nombres
            if key in ["prix_unitaire_ht"] and value is not None:
                try:
                    return f"{float(value):.2f} €"
                except (ValueError, TypeError):
                    pass
                    
            # Formatage des dates
            if key in ["date_reception"] and value:
                try:
                    from datetime import datetime
                    dt = datetime.strptime(str(value), "%Y-%m-%d")
                    return dt.strftime("%d/%m/%Y")
                except (ValueError, TypeError):
                    pass
                    
            return str(value) if value is not None else ""
            
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section < len(self.headers):
                    key = self.headers[section]
                    return self.HEADER_LABELS.get(key, key)
            else:
                return section + 1
        return None


