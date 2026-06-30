from psycopg2.extras import RealDictCursor
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CommandeRepository:
    # Colonnes autorisées pour les requêtes dynamiques (INSERT/UPDATE)
    # Toute colonne interpolée dans une requête DOIT figurer dans cette liste.
    ALLOWED_COLUMNS = frozenset({
        'numero_commande', 'fournisseur_id', 'createur_id', 'date_commande',
        'date_livraison_prevue', 'date_livraison_reelle', 'statut', 'total_ht',
        'frais_port', 'reference_fournisseur', 'mode_paiement', 'notes_commande',
        'updated_at',
    })

    def __init__(self, db):
        self.db = db

    def get_all_commandes(self):
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT 
                    c.id_commande,
                    c.numero_commande,
                    c.date_commande,
                    c.date_livraison_prevue,
                    c.date_livraison_reelle,
                    c.statut,
                    c.total_ht,
                    c.frais_port,
                    c.reference_fournisseur,
                    c.mode_paiement,
                    c.notes_commande,
                    c.created_at,
                    c.updated_at,
                    f.nom AS fournisseur_nom,
                    u.login AS createur_nom
                FROM commande c
                LEFT JOIN fournisseur f ON c.fournisseur_id = f.id_fournisseur
                LEFT JOIN utilisateur u ON c.createur_id = u.id_utilisateur
                ORDER BY c.date_commande DESC, c.id_commande DESC;
            ''')
            return cur.fetchall()
            
    def add_commande(self, commande_data):
        """
        Ajoute une nouvelle commande dans la base de données.
        
        Args:
            commande_data (dict): Dictionnaire contenant les données de la commande
            
        Returns:
            int: L'ID de la commande créée
            
        Raises:
            Exception: En cas d'erreur lors de l'insertion
        """
        # Définir les valeurs par défaut pour les champs optionnels
        defaults = {
            'date_livraison_reelle': None,
            'frais_port': 0.0,
            'reference_fournisseur': '',
            'notes_commande': ''
        }
        
        # Fusionner avec les données fournies (les valeurs fournies écrasent les valeurs par défaut)
        commande_data = {**defaults, **commande_data}
        
        # Préparer la requête dynamiquement en fonction des champs fournis
        fields = [
            'numero_commande', 'fournisseur_id', 'createur_id', 'date_commande',
            'date_livraison_prevue', 'date_livraison_reelle', 'statut', 'total_ht',
            'frais_port', 'reference_fournisseur', 'mode_paiement', 'notes_commande'
        ]
        
        # Filtrer les champs qui sont dans les données
        fields = [f for f in fields if f in commande_data]
        # Validation de sécurité : tous les champs doivent être dans la whitelist
        for f in fields:
            if f not in self.ALLOWED_COLUMNS:
                raise ValueError(f"Colonne non autorisée dans INSERT commande: {f}")
        
        # Créer les placeholders pour la requête
        placeholders = [f'%({f})s' for f in fields]
        
        query = f"""
            INSERT INTO commande (
                {', '.join(fields)}
            ) VALUES (
                {', '.join(placeholders)}
            ) RETURNING id_commande;
        """
        
        logger.debug(f"Requête d'insertion: {query}")
        logger.debug(f"Données: {commande_data}")
        
        with self.db.conn.cursor() as cur:
            try:
                cur.execute(query, commande_data)
                commande_id = cur.fetchone()[0]
                self.db.conn.commit()
                logger.info(f"Commande créée avec succès, ID: {commande_id}")
                return commande_id
            except Exception as e:
                self.db.conn.rollback()
                logger.error(f"Erreur lors de l'ajout de la commande: {str(e)}")
                raise

    def get_commande_by_id(self, commande_id):
        """
        Récupère une commande par son ID.
        
        Args:
            commande_id (int): L'ID de la commande à récupérer
            
        Returns:
            dict: Les données de la commande ou None si non trouvée
        """
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT 
                    c.*,
                    f.nom AS fournisseur_nom,
                    u.login AS createur_nom
                FROM commande c
                LEFT JOIN fournisseur f ON c.fournisseur_id = f.id_fournisseur
                LEFT JOIN utilisateur u ON c.createur_id = u.id_utilisateur
                WHERE c.id_commande = %s;
            ''', (commande_id,))
            return cur.fetchone()

    def update_commande(self, commande_id, commande_data):
        """
        Met à jour une commande existante (hors lignes de commande).
        Args:
            commande_id (int): L'ID de la commande à mettre à jour
            commande_data (dict): Dictionnaire contenant les données à mettre à jour
        Returns:
            bool: True si la mise à jour a réussi, False sinon
        """
        # Champs autorisés pour la table commande (à ajuster selon votre schéma)
        champs_commande = [
            'numero_commande', 'fournisseur_id', 'date_commande', 'date_livraison_prevue',
            'date_livraison_reelle', 'statut', 'total_ht', 'frais_port',
            'reference_fournisseur', 'mode_paiement', 'notes_commande', 'updated_at'
        ]
        # Ajoute la date de mise à jour
        commande_data['updated_at'] = datetime.now()
        # On ne garde que les champs scalaires autorisés
        cleaned_data = {k: v for k, v in commande_data.items() if k in champs_commande}
        # Validation de sécurité : tous les champs doivent être dans la whitelist
        for k in cleaned_data:
            if k not in self.ALLOWED_COLUMNS:
                raise ValueError(f"Colonne non autorisée dans UPDATE commande: {k}")
        # Prépare la requête
        set_clause = ", ".join([f"{k} = %({k})s" for k in cleaned_data.keys()])
        query = f"""
            UPDATE commande
            SET {set_clause}
            WHERE id_commande = %(commande_id)s
            RETURNING id_commande;
        """
        with self.db.conn.cursor() as cur:
            try:
                cleaned_data['commande_id'] = commande_id
                cur.execute(query, cleaned_data)
                if cur.rowcount > 0:
                    self.db.conn.commit()
                    return True
                return False
            except Exception as e:
                self.db.conn.rollback()
                logger.error(f"[ERREUR] Erreur lors de la mise à jour de la commande: {str(e)}")
                raise

    def delete_commande(self, commande_id):
        """
        Supprime une commande par son ID.
        
        Args:
            commande_id (int): L'ID de la commande à supprimer
            
        Returns:
            bool: True si la suppression a réussi, False sinon
        """
        # D'abord, supprimer les lignes de commande associées
        delete_lignes_query = """
            DELETE FROM ligne_commande
            WHERE commande_id = %s;
        """
        
        # Ensuite, supprimer la commande
        delete_commande_query = """
            DELETE FROM commande
            WHERE id_commande = %s
            RETURNING id_commande;
        """
        
        with self.db.conn.cursor() as cur:
            try:
                # Supprimer d'abord les lignes de commande
                cur.execute(delete_lignes_query, (commande_id,))
                
                # Puis supprimer la commande
                cur.execute(delete_commande_query, (commande_id,))
                
                if cur.rowcount > 0:
                    self.db.conn.commit()
                    logger.info(f"Commande {commande_id} et ses lignes supprimées avec succès")
                    return True
                return False
            except Exception as e:
                self.db.conn.rollback()
                logger.error(f"Erreur lors de la suppression de la commande {commande_id}: {str(e)}")
                raise

    def get_commandes_by_statut(self, statut):
        """
        Récupère toutes les commandes ayant un statut spécifique.
        
        Args:
            statut (str): Le statut des commandes à récupérer
            
        Returns:
            list: Liste des commandes correspondant au statut
        """
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT 
                    c.*,
                    f.nom AS fournisseur_nom,
                    u.login AS createur_nom
                FROM commande c
                LEFT JOIN fournisseur f ON c.fournisseur_id = f.id_fournisseur
                LEFT JOIN utilisateur u ON c.createur_id = u.id_utilisateur
                WHERE c.statut = %s
                ORDER BY c.date_commande DESC, c.id_commande DESC;
            ''', (statut,))
            return cur.fetchall()

    def get_commandes_by_fournisseur(self, fournisseur_id):
        """
        Récupère toutes les commandes d'un fournisseur spécifique.
        
        Args:
            fournisseur_id (int): L'ID du fournisseur
            
        Returns:
            list: Liste des commandes du fournisseur
        """
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT 
                    c.*,
                    f.nom AS fournisseur_nom,
                    u.login AS createur_nom
                FROM commande c
                LEFT JOIN fournisseur f ON c.fournisseur_id = f.id_fournisseur
                LEFT JOIN utilisateur u ON c.createur_id = u.id_utilisateur
                WHERE c.fournisseur_id = %s
                ORDER BY c.date_commande DESC, c.id_commande DESC;
            ''', (fournisseur_id,))
            return cur.fetchall()

    def get_commandes_periode(self, date_debut, date_fin):
        """
        Récupère les commandes sur une période donnée.
        
        Args:
            date_debut (str): Date de début au format 'YYYY-MM-DD'
            date_fin (str): Date de fin au format 'YYYY-MM-DD'
            
        Returns:
            list: Liste des commandes de la période
        """
        with self.db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT 
                    c.*,
                    f.nom AS fournisseur_nom,
                    u.login AS createur_nom
                FROM commande c
                LEFT JOIN fournisseur f ON c.fournisseur_id = f.id_fournisseur
                LEFT JOIN utilisateur u ON c.createur_id = u.id_utilisateur
                WHERE c.date_commande BETWEEN %s AND %s
                ORDER BY c.date_commande DESC, c.id_commande DESC;
            ''', (date_debut, date_fin))
            return cur.fetchall()
            
    def get_default_user_id(self):
        """
        Récupère l'ID de l'utilisateur Admin par défaut.
        
        Returns:
            int or None: L'ID de l'utilisateur Admin, ou None si aucun admin n'existe.
            L'admin doit être créé via l'interface utilisateur (avec mot de passe haché).
        """
        with self.db.conn.cursor() as cur:
            try:
                # Vérifie si l'utilisateur Admin existe
                cur.execute("""
                    SELECT id_utilisateur FROM utilisateur 
                    WHERE login = 'Admin' 
                    ORDER BY id_utilisateur LIMIT 1;
                """)
                
                result = cur.fetchone()
                
                if result:
                    logger.debug("Utilisateur Admin trouvé avec l'ID: %s", result[0])
                    return result[0]
                    
                # Pas d'auto-création — l'admin doit être créé explicitement
                logger.warning("Aucun utilisateur Admin trouvé. Créez un compte admin via l'interface.")
                return None
                
            except Exception as e:
                logger.error(f"Erreur lors de la récupération de l'utilisateur Admin: {e}")
                raise
