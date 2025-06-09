#!/usr/bin/env python3
"""
Vérification de la structure de la table ligne_commande
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from APP.services.db import Database

def check_ligne_commande_structure():
    """Vérifie la structure de la table ligne_commande"""
    db = None
    try:
        print("🔍 Vérification de la structure de ligne_commande")
        print("=" * 50)
        
        db = Database()
        db.connect()
        
        with db.conn.cursor() as cur:
            # Structure de la table
            cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default 
                FROM information_schema.columns 
                WHERE table_name = 'ligne_commande' 
                ORDER BY ordinal_position
            """)
            
            columns = cur.fetchall()
            
            print("📋 Colonnes de la table ligne_commande:")
            for col_name, data_type, nullable, default in columns:
                null_str = "NULL" if nullable == "YES" else "NOT NULL"
                default_str = f" DEFAULT {default}" if default else ""
                print(f"   - {col_name}: {data_type} {null_str}{default_str}")
            
            # Vérifier si les colonnes de réception existent
            reception_columns = ['quantite_recue', 'quantite_defectueuse', 'date_derniere_reception', 'commentaire_reception']
            existing_columns = [col[0] for col in columns]
            
            print(f"\n🔍 Vérification des colonnes de réception:")
            for col in reception_columns:
                if col in existing_columns:
                    print(f"   ✅ {col}: Présente")
                else:
                    print(f"   ❌ {col}: MANQUANTE")
            
            # Vérifier les données d'une ligne spécifique
            print(f"\n📊 Données de la ligne 21:")
            cur.execute("SELECT * FROM ligne_commande WHERE id_ligne = 21")
            ligne_data = cur.fetchone()
            
            if ligne_data:
                col_names = [desc[0] for desc in cur.description]
                for i, value in enumerate(ligne_data):
                    print(f"   - {col_names[i]}: {value}")
            else:
                print("   ❌ Ligne 21 non trouvée")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        if db:
            db.close()

if __name__ == "__main__":
    check_ligne_commande_structure()