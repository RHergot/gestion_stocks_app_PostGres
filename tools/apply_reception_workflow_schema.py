#!/usr/bin/env python3
"""
Script pour appliquer le schéma de workflow de réception
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from APP.services.db import Database
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def apply_reception_workflow_schema():
    """Applique le schéma de workflow de réception"""
    try:
        db = Database()
        db.connect()
        
        logger.info("=== Application du schéma de workflow de réception ===")
        
        # Lire et exécuter le script de schéma
        with open('database/reception_workflow_schema.sql', 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        with db.conn.cursor() as cur:
            # Exécuter le schéma
            cur.execute(schema_sql)
            db.conn.commit()
            
        logger.info("✅ Schéma de workflow de réception appliqué avec succès")
        
        # Vérifier que les tables ont été créées
        with db.conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name IN ('lot_reception', 'mise_en_stock_detail')
                ORDER BY table_name;
            """)
            tables = cur.fetchall()
            
            logger.info(f"✅ Tables créées: {[t[0] for t in tables]}")
        
        # Vérifier les nouvelles vues
        with db.conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.views 
                WHERE table_name IN ('v_lots_reception', 'v_stock_reception', 'v_mise_en_stock_detail')
                ORDER BY table_name;
            """)
            vues = cur.fetchall()
            logger.info(f"✅ Vues créées: {[v[0] for v in vues]}")
        
        # Vérifier les nouvelles fonctions
        with db.conn.cursor() as cur:
            cur.execute("""
                SELECT routine_name 
                FROM information_schema.routines 
                WHERE routine_name IN ('generer_numero_lot', 'get_emplacement_reception_defaut')
                AND routine_type = 'FUNCTION'
                ORDER BY routine_name;
            """)
            fonctions = cur.fetchall()
            logger.info(f"✅ Fonctions créées: {[f[0] for f in fonctions]}")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'application du schéma: {e}")
        return False

def main():
    """Fonction principale"""
    try:
        logger.info("🚀 Démarrage de l'application du schéma de workflow de réception")
        
        if not apply_reception_workflow_schema():
            logger.error("❌ Échec de l'application du schéma")
            return False
        
        logger.info("🎉 Schéma de workflow de réception appliqué avec succès!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur générale: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)