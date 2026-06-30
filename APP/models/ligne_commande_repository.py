from psycopg2.extras import RealDictCursor
import logging
import traceback

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LigneCommandeRepository:
    # Colonnes autorisées pour les requêtes UPDATE dynamiques
    ALLOWED_COLUMNS = frozenset({
        'piece_id', 'description_libre', 'quantite_commandee', 'prix_unitaire_ht',
        'quantite_recue', 'quantite_defectueuse', 'commentaire_reception', 'statut_ligne',
    })

    def __init__(self, db):
        self.db = db

    def get_lignes_by_commande(self, commande_id):
        """
        Récupère toutes les lignes de commande pour une commande donnée.
        
        Args:
            commande_id (int): L'ID de la commande
            
        Returns:
            list: Liste des lignes de commande avec les informations des pièces associées
        """
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT l.*, p.reference AS piece_reference, p.nom AS piece_nom
                FROM ligne_commande l
                LEFT JOIN piece p ON l.piece_id = p.id_piece
                WHERE l.commande_id = %s
                ORDER BY l.id_ligne ASC;
            ''', (commande_id,))
            return cur.fetchall()
            
    def get_lignes_by_commande_id(self, commande_id):
        """
        Alias de get_lignes_by_commande pour la cohérence avec le reste du code.
        
        Args:
            commande_id (int): L'ID de la commande
            
        Returns:
            list: Liste des lignes de commande avec les informations des pièces associées
        """
        return self.get_lignes_by_commande(commande_id)
        
    def add_ligne_commande(self, ligne_data):
        """
        Ajoute une nouvelle ligne de commande.
        
        Args:
            ligne_data (dict): Dictionnaire contenant les données de la ligne de commande
                - commande_id (int): ID de la commande
                - piece_id (int): ID de la pièce (peut être None si description_libre est fournie)
                - description_libre (str, optionnel): Description pour les pièces non cataloguées
                - quantite_commandee (int): Quantité commandée
                - prix_unitaire_ht (float): Prix unitaire HT
                
        Returns:
            int: L'ID de la ligne de commande créée
            
        Raises:
            Exception: En cas d'erreur lors de l'insertion
        """
        query = """
            INSERT INTO ligne_commande (
                commande_id, 
                piece_id, 
                description_libre, 
                quantite_commandee, 
                prix_unitaire_ht
            ) VALUES (
                %(commande_id)s, 
                %(piece_id)s, 
                %(description_libre)s, 
                %(quantite_commandee)s, 
                %(prix_unitaire_ht)s
            ) RETURNING id_ligne;
        """
        
        with self.db.conn.cursor() as cur:
            try:
                # S'assurer que les champs requis sont présents
                required_fields = ['commande_id', 'piece_id', 'quantite_commandee', 'prix_unitaire_ht']
                for field in required_fields:
                    if field not in ligne_data:
                        raise KeyError(f"Le champ requis '{field}' est manquant")
                
                # S'assurer que piece_id est un entier
                if isinstance(ligne_data['piece_id'], dict):
                    if 'piece_id' in ligne_data['piece_id']:
                        ligne_data['piece_id'] = ligne_data['piece_id']['piece_id']
                    elif 'id_piece' in ligne_data['piece_id']:
                        ligne_data['piece_id'] = ligne_data['piece_id']['id_piece']
                    else:
                        raise ValueError("Impossible d'extraire l'ID de pièce du dictionnaire")
                
                # S'assurer que description_libre est présent
                if 'description_libre' not in ligne_data:
                    ligne_data['description_libre'] = None
                
                # Debug des champs
                for k, v in ligne_data.items():
                    print(f"[DEBUG] Champ {k}: valeur={v}, type={type(v)}")
                
                # Exécution de la requête
                cur.execute(query, ligne_data)
                ligne_id = cur.fetchone()[0]
                self.db.conn.commit()
                logger.info(f"Ligne de commande ajoutée avec succès, ID: {ligne_id}")
                return ligne_id
            except Exception as e:
                self.db.conn.rollback()
                logger.error(f"Erreur lors de l'ajout de la ligne de commande: {str(e)}")
                logger.error(f"Erreur complète: {traceback.format_exc()}")
                raise
    
    def update_ligne_commande(self, ligne_id, ligne_data):
        """
        Met à jour une ligne de commande existante.
        
        Args:
            ligne_id (int): ID de la ligne à mettre à jour
            ligne_data (dict): Dictionnaire contenant les champs à mettre à jour
                - piece_id (int, optionnel): ID de la pièce
                - description_libre (str, optionnel): Description pour les pièces non cataloguées
                - quantite_commandee (int, optionnel): Quantité commandée
                - prix_unitaire_ht (float, optionnel): Prix unitaire HT
                
        Returns:
            bool: True si la mise à jour a réussi, False sinon
        """
        if not ligne_data:
            return False
            
        set_clauses = []
        params = {'ligne_id': ligne_id}
        
        if 'piece_id' in ligne_data:
            set_clauses.append("piece_id = %(piece_id)s")
            params['piece_id'] = ligne_data['piece_id']
            
        if 'description_libre' in ligne_data:
            set_clauses.append("description_libre = %(description_libre)s")
            params['description_libre'] = ligne_data['description_libre']
            
        if 'quantite_commandee' in ligne_data:
            set_clauses.append("quantite_commandee = %(quantite_commandee)s")
            params['quantite_commandee'] = ligne_data['quantite_commandee']
            
        if 'prix_unitaire_ht' in ligne_data:
            set_clauses.append("prix_unitaire_ht = %(prix_unitaire_ht)s")
            params['prix_unitaire_ht'] = ligne_data['prix_unitaire_ht']
        
        # Champs de réception
        if 'quantite_recue' in ligne_data:
            set_clauses.append("quantite_recue = %(quantite_recue)s")
            params['quantite_recue'] = ligne_data['quantite_recue']
            
        if 'quantite_defectueuse' in ligne_data:
            set_clauses.append("quantite_defectueuse = %(quantite_defectueuse)s")
            params['quantite_defectueuse'] = ligne_data['quantite_defectueuse']
            
        if 'date_derniere_reception' in ligne_data:
            set_clauses.append("date_derniere_reception = %(date_derniere_reception)s")
            params['date_derniere_reception'] = ligne_data['date_derniere_reception']
            
        if 'commentaire_reception' in ligne_data:
            set_clauses.append("commentaire_reception = %(commentaire_reception)s")
            params['commentaire_reception'] = ligne_data['commentaire_reception']
            
        if 'statut_ligne' in ligne_data:
            set_clauses.append("statut_ligne = %(statut_ligne)s")
            params['statut_ligne'] = ligne_data['statut_ligne']
            
        if not set_clauses:
            return False

        # Validation de sécurité : les noms de colonnes dans set_clauses proviennent
        # de chaînes hardcodées (lignes 137-173) — vérification paranoïaque.
        for clause in set_clauses:
            col_name = clause.split(' = ')[0]
            if col_name not in self.ALLOWED_COLUMNS:
                raise ValueError(f"Colonne non autorisée dans UPDATE ligne_commande: {col_name}")

        query = f"""
            UPDATE ligne_commande 
            SET {', '.join(set_clauses)}
            WHERE id_ligne = %(ligne_id)s
            RETURNING id_ligne;
        """
        
        with self.db.conn.cursor() as cur:
            try:
                cur.execute(query, params)
                if cur.rowcount == 0:
                    logger.warning(f"Aucune ligne de commande trouvée avec l'ID: {ligne_id}")
                    return False
                self.db.conn.commit()
                logger.info(f"Ligne de commande {ligne_id} mise à jour avec succès")
                return True
            except Exception as e:
                self.db.conn.rollback()
                logger.error(f"Erreur lors de la mise à jour de la ligne de commande {ligne_id}: {str(e)}")
                return False
    
    def delete_ligne_commande(self, ligne_id):
        """
        Supprime une ligne de commande.
        
        Args:
            ligne_id (int): ID de la ligne à supprimer
            
        Returns:
            bool: True si la suppression a réussi, False sinon
        """
        query = """
            DELETE FROM ligne_commande 
            WHERE id_ligne = %s
            RETURNING id_ligne;
        """
        
        with self.db.conn.cursor() as cur:
            try:
                cur.execute(query, (ligne_id,))
                if cur.rowcount == 0:
                    logger.warning(f"Aucune ligne de commande trouvée avec l'ID: {ligne_id}")
                    return False
                self.db.conn.commit()
                logger.info(f"Ligne de commande {ligne_id} supprimée avec succès")
                return True
            except Exception as e:
                self.db.conn.rollback()
                logger.error(f"Erreur lors de la suppression de la ligne de commande {ligne_id}: {str(e)}")
                return False
    
    def delete_lignes_by_commande_id(self, commande_id):
        """
        Supprime toutes les lignes de commande associées à une commande.
        Args:
            commande_id (int): L'ID de la commande
        Returns:
            int: Le nombre de lignes supprimées
        """
        query = """
            DELETE FROM ligne_commande
            WHERE commande_id = %s;
        """
        with self.db.conn.cursor() as cur:
            try:
                cur.execute(query, (commande_id,))
                count = cur.rowcount
                self.db.conn.commit()
                logger.info(f"{count} lignes supprimées pour la commande {commande_id}")
                return count
            except Exception as e:
                self.db.conn.rollback()
                logger.error(f"Erreur lors de la suppression des lignes de la commande {commande_id}: {str(e)}")
                raise

    def get_ligne_commande_by_id(self, ligne_id):
        """
        Récupère une ligne de commande par son ID.
        
        Args:
            ligne_id (int): ID de la ligne à récupérer
            
        Returns:
            dict: Les données de la ligne de commande ou None si non trouvée
        """
        query = """
            SELECT l.*, p.reference AS piece_reference, p.nom AS piece_nom
            FROM ligne_commande l
            LEFT JOIN piece p ON l.piece_id = p.id_piece
            WHERE l.id_ligne = %s;
        """
        
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (ligne_id,))
            return cur.fetchone()
