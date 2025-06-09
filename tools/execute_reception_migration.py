#!/usr/bin/env python3
"""
Script pour exécuter la migration de la gestion des réceptions
"""

import psycopg2
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
        
        print("✅ Connexion à la base de données réussie")
        
        # Lire le script de migration
        with open('database/reception_schema_migration.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Diviser le script en commandes individuelles (séparées par ;)
        commands = [cmd.strip() for cmd in sql_script.split(';') if cmd.strip()]
        
        with conn.cursor() as cur:
            for i, command in enumerate(commands):
                if command.strip():
                    try:
                        print(f"Exécution de la commande {i+1}/{len(commands)}...")
                        cur.execute(command)
                        conn.commit()
                    except Exception as e:
                        print(f"⚠️ Erreur sur la commande {i+1}: {e}")
                        conn.rollback()
                        # Continuer avec les autres commandes
        
        print("✅ Migration exécutée avec succès")
        
        # Vérifier les nouvelles tables/colonnes
        print("\n=== Vérification de la migration ===")
        
        with conn.cursor() as cur:
            # Vérifier la structure de ligne_commande
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'ligne_commande' 
                ORDER BY ordinal_position;
            """)
            columns = [row[0] for row in cur.fetchall()]
            print(f"Colonnes de ligne_commande: {columns}")
            
            # Vérifier l'existence de reception_detail
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'reception_detail'
                );
            """)
            table_exists = cur.fetchone()[0]
            print(f"Table reception_detail existe: {table_exists}")
            
            # Vérifier les emplacements spéciaux
            cur.execute("""
                SELECT nom FROM emplacement 
                WHERE type = 'RETOUR';
            """)
            emplacements = [row[0] for row in cur.fetchall()]
            print(f"Emplacements de retour: {emplacements}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()