import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

class Database:
    def __init__(self):
        self.conn = None
        # Charger les variables d'environnement depuis le .env à la racine du projet
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
        print(f"Chargement du fichier .env depuis : {os.path.abspath(env_path)}")
        
        # Vérifier si le fichier .env existe
        if not os.path.exists(env_path):
            print("ATTENTION: Le fichier .env n'existe pas à l'emplacement spécifié!")
        else:
            print("Fichier .env trouvé avec succès")
            
        # Charger les variables d'environnement
        load_dotenv(env_path, override=True)
        
        # Afficher toutes les variables d'environnement chargées (pour débogage)
        print("\nVariables d'environnement chargées :")
        for key, value in os.environ.items():
            if key.startswith('POSTGRES_'):
                print(f"{key} = {value}")
        print()
        
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
            # Afficher les paramètres de connexion (sans le mot de passe pour des raisons de sécurité)
            print("\n" + "="*80)
            print("Tentative de connexion à la base de données avec les paramètres :")
            print(f"- Hôte: {self.db_config['host']}")
            print(f"- Port: {self.db_config['port']}")
            print(f"- Base de données: {self.db_config['dbname']}")
            print(f"- Utilisateur: {self.db_config['user']}")
            
            # Établir la connexion
            self.conn = psycopg2.connect(**self.db_config)
            print("✅ Connexion à la base de données établie avec succès!")
            print("="*80 + "\n")
            return self.conn
            
        except Exception as e:
            print("\n" + "!"*80)
            print("ERREUR: Impossible de se connecter à la base de données")
            print(f"Détails: {str(e)}")
            print("Vérifiez vos paramètres de connexion dans le fichier .env")
            print("!"*80 + "\n")
            raise

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            print("Connexion à la base de données fermée")

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
            print(f"\nErreur lors de l'exécution de la requête: {str(e)}")
            if self.conn:
                self.conn.rollback()
            raise

    def commit(self):
        if self.conn:
            self.conn.commit()
            print("Transaction validée avec succès")
