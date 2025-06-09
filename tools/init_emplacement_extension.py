#!/usr/bin/env python3
"""
Script d'initialisation des extensions d'emplacements
Crée les tables et structures nécessaires pour la gestion avancée des emplacements
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from APP.services.db import Database
import psycopg2

def init_emplacement_extension():
    """Initialise les extensions d'emplacements"""
    db = None
    try:
        # Connexion à la base de données
        print("🔧 Connexion à la base de données...")
        db = Database()
        db.connect()  # Établir explicitement la connexion
        
        if not db.conn:
            raise Exception("Impossible de se connecter à la base de données")
        
        print("✅ Connexion établie")
        print("🔧 Initialisation des extensions d'emplacements...")
        
        # Lire et exécuter le script SQL
        script_path = os.path.join(os.path.dirname(__file__), 'database', 'emplacement_extension_schema.sql')
        
        with open(script_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Exécuter le script
        with db.conn.cursor() as cur:
            cur.execute(sql_script)
            db.conn.commit()
        
        print("✅ Tables d'extension créées avec succès")
        
        # Vérifier les tables créées
        with db.conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('emplacement_ext', 'emplacement_stock')
                ORDER BY table_name;
            """)
            tables = cur.fetchall()
            
            print(f"📋 Tables créées: {[table[0] for table in tables]}")
        
        # Vérifier les vues créées
        with db.conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.views 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'v_%emplacement%'
                ORDER BY table_name;
            """)
            views = cur.fetchall()
            
            print(f"👁️  Vues créées: {[view[0] for view in views]}")
        
        # Vérifier les fonctions créées
        with db.conn.cursor() as cur:
            cur.execute("""
                SELECT routine_name 
                FROM information_schema.routines 
                WHERE routine_schema = 'public' 
                AND routine_name IN ('deplacer_stock', 'nettoyer_stocks_zero')
                ORDER BY routine_name;
            """)
            functions = cur.fetchall()
            
            print(f"⚙️  Fonctions créées: {[func[0] for func in functions]}")
        
        # Créer quelques emplacements de test avec dimensions
        print("\n🧪 Création d'emplacements de test...")
        create_test_emplacements(db)
        
        print("\n✅ Initialisation terminée avec succès!")
        
    except psycopg2.Error as e:
        print(f"❌ Erreur PostgreSQL: {e}")
        return False
    except FileNotFoundError as e:
        print(f"❌ Fichier SQL non trouvé: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()
    
    return True

def create_test_emplacements(db):
    """Crée quelques emplacements de test avec leurs extensions"""
    try:
        from APP.models.emplacement_repository import EmplacementRepository
        from APP.models.emplacement_ext_repository import EmplacementExtRepository
        
        emplacement_repo = EmplacementRepository(db)
        emplacement_ext_repo = EmplacementExtRepository(db)
        
        # Vérifier s'il y a déjà des emplacements
        emplacements_existants = emplacement_repo.get_all_emplacements()
        
        if not emplacements_existants:
            print("   Création d'emplacements de base...")
            
            # Créer quelques emplacements de base
            emplacements_test = [
                {
                    "magasin_id": 1,
                    "nom": "A1S1L1",
                    "type": "Etagere",
                    "allee": "1",
                    "etagere": "1", 
                    "niveau": "1"
                },
                {
                    "magasin_id": 1,
                    "nom": "A1S1L2",
                    "type": "Etagere",
                    "allee": "1",
                    "etagere": "1",
                    "niveau": "2"
                },
                {
                    "magasin_id": 1,
                    "nom": "A2S1L1",
                    "type": "Etagere",
                    "allee": "2",
                    "etagere": "1",
                    "niveau": "1"
                }
            ]
            
            for emp_data in emplacements_test:
                emplacement_id = emplacement_repo.add_emplacement(emp_data)
                print(f"   ✓ Emplacement créé: {emp_data['nom']} (ID: {emplacement_id})")
        
        # Ajouter les extensions pour tous les emplacements
        emplacements = emplacement_repo.get_all_emplacements()
        
        for emplacement in emplacements:
            emplacement_id = emplacement['id']
            
            # Vérifier si l'extension existe déjà
            existing_ext = emplacement_ext_repo.get_emplacement_ext_by_id(emplacement_id)
            
            if not existing_ext:
                # Créer des dimensions par défaut basées sur le type
                if emplacement.get('type') == 'Etagere':
                    ext_data = {
                        'longueur_cm': 120.0,
                        'hauteur_cm': 40.0,
                        'profondeur_cm': 60.0,
                        'capacite_max_kg': 100.0,
                        'temperature_min_c': 10.0,
                        'temperature_max_c': 30.0,
                        'humidite_max_pct': 80.0,
                        'conditions_speciales': 'Stockage standard',
                        'actif': True
                    }
                else:
                    ext_data = {
                        'longueur_cm': 100.0,
                        'hauteur_cm': 50.0,
                        'profondeur_cm': 50.0,
                        'capacite_max_kg': 50.0,
                        'temperature_min_c': 15.0,
                        'temperature_max_c': 25.0,
                        'humidite_max_pct': 70.0,
                        'conditions_speciales': None,
                        'actif': True
                    }
                
                emplacement_ext_repo.create_emplacement_ext(emplacement_id, ext_data)
                print(f"   ✓ Extension créée pour: {emplacement['nom']}")
        
        print(f"   📦 {len(emplacements)} emplacements configurés avec leurs extensions")
        
    except Exception as e:
        print(f"   ❌ Erreur lors de la création des emplacements de test: {e}")

def verify_installation():
    """Vérifie que l'installation s'est bien déroulée"""
    db = None
    try:
        db = Database()
        db.connect()
        
        print("\n🔍 Vérification de l'installation...")
        
        # Test des vues
        with db.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM v_emplacement_detail")
            count_detail = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM v_emplacement_capacite")
            count_capacite = cur.fetchone()[0]
            
            print(f"   ✓ Vue v_emplacement_detail: {count_detail} enregistrements")
            print(f"   ✓ Vue v_emplacement_capacite: {count_capacite} enregistrements")
        
        # Test des fonctions
        with db.conn.cursor() as cur:
            cur.execute("SELECT nettoyer_stocks_zero()")
            result = cur.fetchone()[0]
            print(f"   ✓ Fonction nettoyer_stocks_zero: {result} stocks nettoyés")
        
        print("   ✅ Installation vérifiée avec succès!")
        
    except Exception as e:
        print(f"   ❌ Erreur lors de la vérification: {e}")
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    print("🚀 Initialisation des extensions d'emplacements")
    print("=" * 50)
    
    success = init_emplacement_extension()
    
    if success:
        verify_installation()
        print("\n🎉 Initialisation terminée avec succès!")
        print("\nVous pouvez maintenant:")
        print("- Utiliser le dialogue d'emplacement avec les dimensions")
        print("- Gérer les stocks par emplacement")
        print("- Effectuer des transferts entre emplacements")
        print("- Consulter les vues de capacité et de stock détaillé")
    else:
        print("\n💥 Échec de l'initialisation")
        sys.exit(1)