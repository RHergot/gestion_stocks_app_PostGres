#!/usr/bin/env python3
"""
Script de test de connexion à la base de données PostgreSQL.
Ce script tente de se connecter à la base de données en utilisant les paramètres
du fichier .env et affiche des informations sur la connexion.
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

def test_connection(host, port, dbname, user, password, **options):
    """Tente de se connecter à la base de données PostgreSQL et retourne les informations de connexion."""
    try:
        # Construction des paramètres de connexion
        conn_params = {
            'host': host,
            'port': port,
            'dbname': dbname,
            'user': user,
            'password': password,
            **options  # Ajoute les options supplémentaires (comme sslmode)
        }
        
        print("\nTentative de connexion avec les paramètres suivants :")
        print(f"- Hôte: {host}")
        print(f"- Port: {port}")
        print(f"- Base de données: {dbname}")
        print(f"- Utilisateur: {user}")
        print(f"- Options supplémentaires: {options or 'Aucune'}")
        
        # Tentative de connexion
        conn = psycopg2.connect(**conn_params)
        
        # Récupération des informations de la base de données
        with conn.cursor() as cur:
            # Version de PostgreSQL
            cur.execute("SELECT version();")
            pg_version = cur.fetchone()[0]
            
            # Nom de la base de données actuelle
            cur.execute("SELECT current_database();")
            db_name = cur.fetchone()[0]
            
            # Utilisateur actuel
            cur.execute("SELECT current_user;")
            current_user = cur.fetchone()[0]
            
            # Liste des bases de données disponibles
            cur.execute("""
                SELECT datname 
                FROM pg_database 
                WHERE datistemplate = false 
                ORDER BY datname;
            """)
            databases = [db[0] for db in cur.fetchall()]
            
            # Liste des tables dans la base de données actuelle
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            tables = [table[0] for table in cur.fetchall()]
            
            # Affichage des informations
            print("\n" + "="*80)
            print("CONNEXION RÉUSSIE !")
            print("="*80)
            print(f"\nVersion de PostgreSQL : {pg_version}")
            print(f"Base de données connectée : {db_name}")
            print(f"Utilisateur actuel : {current_user}")
            
            print("\nBases de données disponibles :")
            for db in databases:
                print(f"- {db}")
                
            print("\nTables dans la base actuelle :")
            for table in tables:
                print(f"- {table}")
            
            return True
            
    except Exception as e:
        print("\n" + "!"*80)
        print("ERREUR DE CONNEXION")
        print("!"*80)
        print(f"\nErreur détaillée : {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()
            print("\nConnexion fermée.")

def main():
    # Chemin absolu vers le fichier .env
    env_path = os.path.abspath('.env')
    print(f"Chargement du fichier .env depuis : {env_path}")
    
    # Vérifier si le fichier .env existe
    if not os.path.exists(env_path):
        print(f"ERREUR : Le fichier {env_path} n'existe pas.")
        print("Assurez-vous d'avoir créé le fichier .env à partir de .env.example")
        return 1
    
    # Charger les variables d'environnement depuis .env
    load_dotenv(env_path, override=True)
    
    # Afficher les variables chargées pour le débogage (mot de passe masqué)
    print("\nVariables d'environnement chargées :")
    for key, value in os.environ.items():
        if key.startswith('POSTGRES_'):
            if 'PASSWORD' in key.upper():
                print(f"{key} = ***")
            else:
                print(f"{key} = {value}")
    
    # Récupération des paramètres de connexion
    host = os.getenv('POSTGRES_HOST')
    port = os.getenv('POSTGRES_PORT', '5432')
    dbname = os.getenv('POSTGRES_DB')
    user = os.getenv('POSTGRES_USER')
    password = os.getenv('POSTGRES_PASSWORD')
    
    # Options supplémentaires (comme sslmode)
    options = {}
    if os.getenv('POSTGRES_OPTIONS'):
        for opt in os.getenv('POSTGRES_OPTIONS').split():
            if '=' in opt:
                key, value = opt.split('=', 1)
                options[key] = value
    
    # Vérification des paramètres obligatoires
    if not all([host, dbname, user, password]):
        print("\nERREUR : Paramètres de connexion manquants dans le fichier .env")
        print("Assurez-vous que les variables suivantes sont définies :")
        print("- POSTGRES_HOST")
        print("- POSTGRES_DB")
        print("- POSTGRES_USER")
        print("- POSTGRES_PASSWORD")
        print("\nUtilisez le fichier .env.example comme modèle.")
        return 1
    
    # Test de connexion
    success = test_connection(host, port, dbname, user, password, **options)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
