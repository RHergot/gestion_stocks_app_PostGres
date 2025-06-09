#!/usr/bin/env python3
"""
Script d'initialisation des tables de mouvements de stock
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys
from dotenv import load_dotenv

def get_db_connection():
    """Établit la connexion à la base de données"""
    try:
        # Charger les variables d'environnement
        load_dotenv()
        
        # Définir les options de connexion pour éviter les problèmes d'encodage
        connection_params = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'database': os.getenv('POSTGRES_DB', 'gmao_industrie_data'),
            'user': os.getenv('POSTGRES_USER', 'gmao_app_user'),
            'password': os.getenv('POSTGRES_PASSWORD', ''),
            'port': os.getenv('POSTGRES_PORT', '5432'),
            'client_encoding': 'utf8',
            'options': '-c client_encoding=UTF8'
        }
        
        print(f"Tentative de connexion à la base de données:")
        print(f"  Host: {connection_params['host']}")
        print(f"  Database: {connection_params['database']}")
        print(f"  User: {connection_params['user']}")
        print(f"  Port: {connection_params['port']}")
        
        conn = psycopg2.connect(**connection_params)
        print("✓ Connexion établie avec succès")
        return conn
    except psycopg2.Error as e:
        print(f"Erreur de connexion à la base de données: {e}")
        return None

def execute_sql_file(conn, file_path):
    """Exécute un fichier SQL"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        with conn.cursor() as cur:
            cur.execute(sql_content)
        
        conn.commit()
        print(f"✓ Fichier SQL exécuté avec succès: {file_path}")
        return True
        
    except Exception as e:
        print(f"✗ Erreur lors de l'exécution du fichier {file_path}: {e}")
        conn.rollback()
        return False

def verify_tables_creation(conn):
    """Vérifie que les tables ont été créées correctement"""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Vérifier l'existence des tables
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('type_mouvement', 'mouvement_stock');
            """)
            tables = [row['table_name'] for row in cur.fetchall()]
            
            print("\n=== Vérification des tables ===")
            for table in ['type_mouvement', 'mouvement_stock']:
                if table in tables:
                    print(f"✓ Table {table} créée")
                else:
                    print(f"✗ Table {table} manquante")
            
            # Vérifier les types de mouvement
            cur.execute("SELECT COUNT(*) as count FROM type_mouvement;")
            count = cur.fetchone()['count']
            print(f"✓ {count} types de mouvement insérés")
            
            # Vérifier les vues
            cur.execute("""
                SELECT table_name 
                FROM information_schema.views 
                WHERE table_schema = 'public' 
                AND table_name IN ('v_mouvement_stats', 'v_historique_mouvements');
            """)
            views = [row['table_name'] for row in cur.fetchall()]
            
            print("\n=== Vérification des vues ===")
            for view in ['v_mouvement_stats', 'v_historique_mouvements']:
                if view in views:
                    print(f"✓ Vue {view} créée")
                else:
                    print(f"✗ Vue {view} manquante")
            
            return len(tables) == 2 and len(views) == 2
            
    except Exception as e:
        print(f"Erreur lors de la vérification: {e}")
        return False

def create_sample_movements(conn):
    """Crée quelques mouvements d'exemple"""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Récupérer une pièce existante
            cur.execute("SELECT id_piece, stock_actuel FROM piece LIMIT 1;")
            piece = cur.fetchone()
            
            if not piece:
                print("Aucune pièce trouvée pour créer des mouvements d'exemple")
                return False
            
            # Récupérer le type d'entrée
            cur.execute("SELECT id FROM type_mouvement WHERE nom = 'ENTREE_ACHAT';")
            type_entree = cur.fetchone()
            
            if type_entree:
                # Créer un mouvement d'entrée d'exemple
                stock_avant = piece['stock_actuel']
                quantite = 10
                stock_apres = stock_avant + quantite
                
                cur.execute("""
                    INSERT INTO mouvement_stock (
                        piece_id, type_mouvement_id, quantite, 
                        stock_avant, stock_apres, commentaire
                    ) VALUES (%s, %s, %s, %s, %s, %s);
                """, (
                    piece['id_piece'], type_entree['id'], quantite,
                    stock_avant, stock_apres, 
                    'Mouvement d\'exemple créé lors de l\'initialisation'
                ))
                
                # Mettre à jour le stock de la pièce
                cur.execute("""
                    UPDATE piece SET stock_actuel = %s WHERE id_piece = %s;
                """, (stock_apres, piece['id_piece']))
                
                conn.commit()
                print(f"✓ Mouvement d'exemple créé pour la pièce ID {piece['id_piece']}")
                return True
            
    except Exception as e:
        print(f"Erreur lors de la création des mouvements d'exemple: {e}")
        conn.rollback()
        return False

def main():
    """Fonction principale"""
    print("=== Initialisation des tables de mouvements de stock ===\n")
    
    # Connexion à la base de données
    conn = get_db_connection()
    if not conn:
        print("Impossible de se connecter à la base de données")
        sys.exit(1)
    
    try:
        # Chemin vers le fichier SQL de migration
        sql_file = os.path.join(os.path.dirname(__file__), 'database', 'mouvement_schema_migration.sql')
        
        if not os.path.exists(sql_file):
            print(f"Fichier SQL non trouvé: {sql_file}")
            sys.exit(1)
        
        # Exécuter le fichier SQL
        print("1. Création des tables et vues...")
        if not execute_sql_file(conn, sql_file):
            print("Échec de la création des tables")
            sys.exit(1)
        
        # Vérifier la création
        print("\n2. Vérification de la création...")
        if not verify_tables_creation(conn):
            print("Certaines tables ou vues n'ont pas été créées correctement")
        
        # Créer des mouvements d'exemple
        print("\n3. Création de mouvements d'exemple...")
        create_sample_movements(conn)
        
        print("\n=== Initialisation terminée avec succès ===")
        
    except Exception as e:
        print(f"Erreur générale: {e}")
        sys.exit(1)
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()