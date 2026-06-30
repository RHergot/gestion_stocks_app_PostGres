#!/usr/bin/env python3
"""
Script pour vérifier l'état de la base de données
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

def main():
    load_dotenv()
    
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST'),
            database=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            port=os.getenv('POSTGRES_PORT'),
            client_encoding='utf8'
        )
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Lister toutes les tables
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            tables = [row['table_name'] for row in cur.fetchall()]
            print('Tables existantes:')
            for table in tables:
                print(f'  - {table}')
            
            # Vérifier si type_mouvement existe
            if 'type_mouvement' in tables:
                cur.execute('SELECT * FROM type_mouvement LIMIT 5;')
                rows = cur.fetchall()
                print(f'\nContenu de type_mouvement ({len(rows)} lignes):')
                for row in rows:
                    print(f'  {dict(row)}')
            else:
                print('\nTable type_mouvement n\'existe pas')
            
            # Vérifier si mouvement_stock existe
            if 'mouvement_stock' in tables:
                cur.execute('SELECT COUNT(*) as count FROM mouvement_stock;')
                count = cur.fetchone()['count']
                print(f'\nTable mouvement_stock: {count} lignes')
            else:
                print('\nTable mouvement_stock n\'existe pas')
                
        conn.close()
        
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    main()
