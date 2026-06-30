import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# NOTE — Pattern d'accès DB recommandé :
#   Préférer db.execute(query, params) qui gère automatiquement le curseur et les commits.
#   Éviter db.conn.cursor() directement dans les repositories/services.
#   Le pattern db.execute() offre : RealDictCursor automatique, commit/rollback géré,
#   et une interface uniforme pour toute l'application.

class Database:
    def __init__(self):
        self.conn = None
        # Charger les variables d'environnement depuis le .env à la racine du projet
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
        logger.debug("Chargement du fichier .env depuis : %s", os.path.abspath(env_path))
        
        # Vérifier si le fichier .env existe
        if not os.path.exists(env_path):
            logger.warning("Le fichier .env n'existe pas à l'emplacement spécifié!")
        else:
            logger.debug("Fichier .env trouvé avec succès")
            
        # Charger les variables d'environnement
        load_dotenv(env_path, override=True)
        
        # Log des variables d'environnement chargées (mot de passe masqué)
        for key, value in os.environ.items():
            if key.startswith('POSTGRES_'):
                if 'PASSWORD' in key.upper():
                    logger.debug("%s = ***", key)
                else:
                    logger.debug("%s = %s", key, value)
        
        # Récupération des paramètres de connexion
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
            'dbname': os.getenv('POSTGRES_DB', 'gmao_industrie_data'),
            'user': os.getenv('POSTGRES_USER', 'gmao_app_user'),
            'password': os.getenv('POSTGRES_PASSWORD', '')
        }

    def connect(self):
        try:
            logger.info("Tentative de connexion à la base de données: hôte=%s port=%s db=%s user=%s",
                        self.db_config['host'], self.db_config['port'],
                        self.db_config['dbname'], self.db_config['user'])
            
            # Établir la connexion
            self.conn = psycopg2.connect(**self.db_config)
            logger.info("Connexion à la base de données établie avec succès")
            return self.conn
            
        except Exception as e:
            logger.error("Impossible de se connecter à la base de données: %s", e)
            raise

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Connexion à la base de données fermée")

    def execute(self, query, params=None):
        try:
            if not self.conn:
                self.connect()
                
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                # Commit automatique pour les requêtes d'écriture
                if query.strip().lower().startswith(("insert", "update", "delete")):
                    self.conn.commit()
                if cur.description:
                    return cur.fetchall()
                return None
        except Exception as e:
            logger.error("Erreur lors de l'exécution de la requête: %s", e)
            if self.conn:
                self.conn.rollback()
            raise

    def commit(self):
        if self.conn:
            self.conn.commit()
            logger.debug("Transaction validée avec succès")
