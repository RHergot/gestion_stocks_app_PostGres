#!/usr/bin/env python3
"""
Script pour vérifier le contenu des tables de mouvements
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
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:            # Vérifier les types de mouvement
            cur.execute('SELECT * FROM type_mouvement ORDER BY id;')
            types = cur.fetchall()
            print('Types de mouvement disponibles:')
            for t in types:
                if t['impact_stock'] == 1:
                    impact = 'Entrée (+)'
                elif t['impact_stock'] == -1:
                    impact = 'Sortie (-)'
                else:
                    impact = 'Neutre (0)'
                print(f'  {t["id"]}: {t["nom"]} - {impact}')
                print(f'     {t["description"]}')
            
            # Vérifier les mouvements
            cur.execute('SELECT * FROM mouvement_stock;')
            mouvements = cur.fetchall()
            print(f'\nMouvements dans la base ({len(mouvements)}):')
            for m in mouvements:
                print(f'  ID {m["id"]}: Pièce {m["piece_id"]}, Type {m["type_mouvement_id"]}, Qté {m["quantite"]}')
                print(f'    Stock avant: {m["stock_avant"]} -> après: {m["stock_apres"]}')
                if m["commentaire"]:
                    print(f'    Commentaire: {m["commentaire"]}')
            
            # Vérifier les vues
            print(f'\nTest de la vue v_mouvement_stats:')
            cur.execute('SELECT * FROM v_mouvement_stats LIMIT 3;')
            stats = cur.fetchall()
            for stat in stats:
                print(f'  Pièce {stat["piece_nom"]}: {stat["nb_mouvements"]} mouvements')
                
        conn.close()
        
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    main()
