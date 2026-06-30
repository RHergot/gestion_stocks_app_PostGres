#!/usr/bin/env python3
"""
Script pour vérifier la structure de la table mouvement_stock
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
            # Vérifier les colonnes de mouvement_stock
            cur.execute("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'mouvement_stock' 
                ORDER BY ordinal_position;
            """)
            columns = cur.fetchall()
            print('Structure de mouvement_stock:')
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
            
            # Vérifier s'il y a des données
            cur.execute("SELECT COUNT(*) as count FROM mouvement_stock;")
            count = cur.fetchone()['count']
            print(f"\nNombre de lignes dans mouvement_stock: {count}")
            
            # Vérifier les contraintes de clés étrangères
            cur.execute("""
                SELECT 
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM 
                    information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                    AND tc.table_name = 'mouvement_stock';
            """)
            fks = cur.fetchall()
            print(f"\nContraintes de clés étrangères:")
            for fk in fks:
                print(f"  - {fk['column_name']} -> {fk['foreign_table_name']}.{fk['foreign_column_name']}")
                
        conn.close()
        
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    main()
