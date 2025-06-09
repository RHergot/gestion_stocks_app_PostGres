#!/usr/bin/env python3
"""
Script pour vérifier la structure de la table commande
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
            # Structure de la table commande
            cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'commande' 
                ORDER BY ordinal_position;
            """)
            columns = cur.fetchall()
            print('Structure de la table commande:')
            for col in columns:
                print(f'  - {col["column_name"]}: {col["data_type"]} (nullable: {col["is_nullable"]}, default: {col["column_default"]})')
            
            # Contraintes CHECK sur la table commande
            cur.execute("""
                SELECT conname, pg_get_constraintdef(oid) as definition
                FROM pg_constraint 
                WHERE conrelid = 'commande'::regclass 
                AND contype = 'c';
            """)
            constraints = cur.fetchall()
            if constraints:
                print('\nContraintes CHECK:')
                for constraint in constraints:
                    print(f'  - {constraint["conname"]}: {constraint["definition"]}')
            
            # Quelques exemples de données
            cur.execute('SELECT * FROM commande LIMIT 3;')
            rows = cur.fetchall()
            print(f'\nExemples de données ({len(rows)} lignes):')
            for row in rows:
                print(f'  {dict(row)}')
                
        conn.close()
        
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    main()