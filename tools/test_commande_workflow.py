#!/usr/bin/env python3
"""
Script de test pour vérifier le workflow des commandes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from APP.services.db import Database
from APP.models.commande_repository import CommandeRepository
from APP.models.ligne_commande_repository import LigneCommandeRepository
from APP.services.mouvement_service import MouvementService

def test_commande_workflow():
    """Test du workflow complet des commandes"""
    
    print("=== Test du workflow des commandes ===\n")
    
    # Connexion à la base de données
    db = Database()
    try:
        db.connect()
    except Exception as e:
        print(f"❌ Impossible de se connecter à la base de données: {e}")
        return False
    
    print("✅ Connexion à la base de données réussie")
    
    # Initialisation des repositories
    commande_repo = CommandeRepository(db)
    ligne_repo = LigneCommandeRepository(db)
    mouvement_service = MouvementService(db)
    
    try:
        # 1. Récupérer une commande de test
        print("\n1. Récupération d'une commande de test...")
        commandes = commande_repo.get_all_commandes()
        
        if not commandes:
            print("❌ Aucune commande trouvée dans la base de données")
            return False
        
        # Prendre la première commande en statut Brouillon
        commande_test = None
        for cmd in commandes:
            if cmd['statut'] == 'Brouillon':
                commande_test = cmd
                break
        
        if not commande_test:
            print("❌ Aucune commande en statut 'Brouillon' trouvée")
            return False
        
        print(f"✅ Commande trouvée: ID={commande_test['id_commande']}, Numéro={commande_test['numero_commande']}")
        
        # 2. Vérifier les lignes de commande
        print("\n2. Vérification des lignes de commande...")
        lignes = ligne_repo.get_lignes_by_commande(commande_test['id_commande'])
        
        if not lignes:
            print("❌ Aucune ligne de commande trouvée")
            return False
        
        print(f"✅ {len(lignes)} lignes de commande trouvées")
        for ligne in lignes:
            print(f"   - Pièce ID: {ligne['piece_id']}, Quantité: {ligne['quantite_commandee']}")
        
        # 3. Test de transition de statut: Brouillon -> Validee
        print("\n3. Test de transition: Brouillon -> Validee...")
        success = commande_repo.update_commande(
            commande_test['id_commande'], 
            {'statut': 'Validee'}
        )
        
        if success:
            print("✅ Transition vers 'Validee' réussie")
        else:
            print("❌ Échec de la transition vers 'Validee'")
            return False
        
        # 4. Test de transition: Validee -> Envoyee
        print("\n4. Test de transition: Validee -> Envoyee...")
        success = commande_repo.update_commande(
            commande_test['id_commande'], 
            {'statut': 'Envoyee'}
        )
        
        if success:
            print("✅ Transition vers 'Envoyee' réussie")
        else:
            print("❌ Échec de la transition vers 'Envoyee'")
            return False
        
        # 5. Test de livraison avec création de mouvements
        print("\n5. Test de livraison avec création de mouvements...")
        
        # Récupérer le type de mouvement ENTREE_ACHAT
        types_mouvement = mouvement_service.get_all_types_mouvement()
        type_entree_achat = next((t for t in types_mouvement if t['nom'] == 'ENTREE_ACHAT'), None)
        
        if not type_entree_achat:
            print("❌ Type de mouvement ENTREE_ACHAT non trouvé")
            return False
        
        print(f"✅ Type de mouvement ENTREE_ACHAT trouvé: ID={type_entree_achat['id']}")
        
        # Créer les mouvements pour chaque ligne
        mouvements_crees = []
        for ligne in lignes:
            try:
                mouvement_id = mouvement_service.creer_mouvement_entree(
                    piece_id=ligne['piece_id'],
                    quantite=ligne['quantite_commandee'],
                    type_mouvement_id=type_entree_achat['id'],
                    reference_document=f"CMD-{commande_test['numero_commande']}",
                    commentaire=f"Test livraison commande {commande_test['numero_commande']}",
                    cout_unitaire=ligne.get('prix_unitaire_ht')
                )
                mouvements_crees.append(mouvement_id)
                print(f"✅ Mouvement créé: ID={mouvement_id} pour pièce {ligne['piece_id']}")
                
            except Exception as e:
                print(f"❌ Erreur lors de la création du mouvement pour la pièce {ligne['piece_id']}: {e}")
                return False
        
        # Marquer la commande comme livrée
        from datetime import datetime
        success = commande_repo.update_commande(
            commande_test['id_commande'], 
            {
                'statut': 'Livree',
                'date_livraison_reelle': datetime.now().strftime('%Y-%m-%d')
            }
        )
        
        if success:
            print("✅ Commande marquée comme livrée")
        else:
            print("❌ Échec du marquage de livraison")
            return False
        
        # 6. Vérification finale
        print("\n6. Vérification finale...")
        commande_finale = commande_repo.get_commande_by_id(commande_test['id_commande'])
        
        if commande_finale['statut'] == 'Livree':
            print("✅ Statut final correct: Livree")
        else:
            print(f"❌ Statut final incorrect: {commande_finale['statut']}")
            return False
        
        print(f"✅ Date de livraison réelle: {commande_finale['date_livraison_reelle']}")
        print(f"✅ {len(mouvements_crees)} mouvements de stock créés")
        
        print("\n🎉 Test du workflow complet réussi!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if db.conn:
            db.conn.close()

def test_types_mouvement():
    """Test de vérification des types de mouvement"""
    
    print("\n=== Vérification des types de mouvement ===\n")
    
    db = Database()
    try:
        db.connect()
    except Exception as e:
        print(f"❌ Impossible de se connecter à la base de données: {e}")
        return False
    
    try:
        mouvement_service = MouvementService(db)
        types = mouvement_service.get_all_types_mouvement()
        
        print(f"Types de mouvement disponibles ({len(types)}):")
        for type_mv in types:
            impact = "Entrée" if type_mv['impact_stock'] == 1 else "Sortie"
            print(f"  - {type_mv['nom']}: {type_mv['description']} ({impact})")
        
        # Vérifier que ENTREE_ACHAT existe
        entree_achat = next((t for t in types if t['nom'] == 'ENTREE_ACHAT'), None)
        if entree_achat:
            print(f"\n✅ Type ENTREE_ACHAT trouvé: ID={entree_achat['id']}")
            return True
        else:
            print("\n❌ Type ENTREE_ACHAT non trouvé")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    finally:
        if db.conn:
            db.conn.close()

if __name__ == "__main__":
    print("Test des fonctionnalités de gestion des commandes\n")
    
    # Test des types de mouvement
    if not test_types_mouvement():
        print("\n❌ Échec du test des types de mouvement")
        sys.exit(1)
    
    # Test du workflow complet
    if not test_commande_workflow():
        print("\n❌ Échec du test du workflow")
        sys.exit(1)
    
    print("\n✅ Tous les tests sont passés avec succès!")