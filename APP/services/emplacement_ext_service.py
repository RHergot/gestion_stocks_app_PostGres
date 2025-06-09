from APP.services.db import Database
from APP.models.emplacement_ext_repository import EmplacementExtRepository
from typing import Dict, List, Optional

class EmplacementExtService:
    """Service pour la gestion des extensions d'emplacements"""
    
    def __init__(self, db: Database):
        self.db = db
        self.repository = EmplacementExtRepository(db)

    def get_emplacement_complet(self, emplacement_id: int) -> Dict:
        """Récupère un emplacement avec toutes ses données étendues"""
        try:
            # Récupérer les données de base
            from APP.models.emplacement_repository import EmplacementRepository
            emplacement_repo = EmplacementRepository(self.db)
            emplacement_base = emplacement_repo.get_emplacement_by_id(emplacement_id)
            
            if not emplacement_base:
                return {}
            
            # Récupérer les données étendues
            emplacement_ext = self.repository.get_emplacement_ext_by_id(emplacement_id)
            
            # Récupérer le stock
            stock_items = self.repository.get_stock_by_emplacement(emplacement_id)
            
            # Combiner toutes les données
            result = dict(emplacement_base)
            if emplacement_ext:
                result.update(dict(emplacement_ext))
            
            result['stock_items'] = stock_items
            result['nb_pieces_differentes'] = len(stock_items)
            result['quantite_totale'] = sum(item['quantite'] for item in stock_items)
            
            return result
            
        except Exception as e:
            print(f"[ERREUR] Impossible de récupérer l'emplacement complet {emplacement_id}: {e}")
            return {}

    def creer_ou_modifier_emplacement_ext(self, emplacement_id: int, data: Dict) -> bool:
        """Crée ou modifie les données étendues d'un emplacement"""
        try:
            # Vérifier si les données étendues existent déjà
            existing = self.repository.get_emplacement_ext_by_id(emplacement_id)
            
            if existing:
                return self.repository.update_emplacement_ext(emplacement_id, data)
            else:
                return self.repository.create_emplacement_ext(emplacement_id, data)
                
        except Exception as e:
            print(f"[ERREUR] Impossible de créer/modifier l'emplacement étendu {emplacement_id}: {e}")
            return False

    def get_tous_emplacements_detail(self) -> List[Dict]:
        """Récupère tous les emplacements avec leurs détails"""
        try:
            return self.repository.get_all_emplacements_detail()
        except Exception as e:
            print(f"[ERREUR] Impossible de récupérer les emplacements détaillés: {e}")
            return []

    def get_emplacements_avec_capacite(self) -> List[Dict]:
        """Récupère les emplacements avec leurs informations de capacité"""
        try:
            return self.repository.get_emplacements_capacite()
        except Exception as e:
            print(f"[ERREUR] Impossible de récupérer les capacités des emplacements: {e}")
            return []

    def ajouter_stock_piece(self, emplacement_id: int, piece_id: int, 
                           quantite: int, commentaire: str = None) -> bool:
        """Ajoute du stock d'une pièce dans un emplacement"""
        try:
            if quantite <= 0:
                raise ValueError("La quantité doit être positive")
            
            return self.repository.ajouter_stock_emplacement(
                emplacement_id, piece_id, quantite, commentaire
            )
            
        except Exception as e:
            print(f"[ERREUR] Impossible d'ajouter le stock: {e}")
            return False

    def retirer_stock_piece(self, emplacement_id: int, piece_id: int, 
                           quantite: int, commentaire: str = None) -> bool:
        """Retire du stock d'une pièce d'un emplacement"""
        try:
            if quantite <= 0:
                raise ValueError("La quantité doit être positive")
            
            return self.repository.retirer_stock_emplacement(
                emplacement_id, piece_id, quantite, commentaire
            )
            
        except Exception as e:
            print(f"[ERREUR] Impossible de retirer le stock: {e}")
            return False

    def transferer_stock(self, piece_id: int, emplacement_source_id: int, 
                        emplacement_destination_id: int, quantite: int, 
                        commentaire: str = None) -> bool:
        """Transfère du stock entre emplacements"""
        try:
            if quantite <= 0:
                raise ValueError("La quantité doit être positive")
            
            if emplacement_source_id == emplacement_destination_id:
                raise ValueError("L'emplacement source et destination doivent être différents")
            
            return self.repository.deplacer_stock(
                piece_id, emplacement_source_id, emplacement_destination_id, 
                quantite, commentaire
            )
            
        except Exception as e:
            print(f"[ERREUR] Impossible de transférer le stock: {e}")
            return False

    def get_stock_piece_par_emplacement(self, piece_id: int) -> List[Dict]:
        """Récupère la répartition d'une pièce dans tous les emplacements"""
        try:
            return self.repository.get_piece_emplacements(piece_id)
        except Exception as e:
            print(f"[ERREUR] Impossible de récupérer la répartition de la pièce {piece_id}: {e}")
            return []

    def get_emplacements_libres(self, capacite_min: float = None) -> List[Dict]:
        """Récupère les emplacements avec de la capacité libre"""
        try:
            return self.repository.get_emplacements_libres(capacite_min)
        except Exception as e:
            print(f"[ERREUR] Impossible de récupérer les emplacements libres: {e}")
            return []

    def rechercher_piece(self, terme_recherche: str) -> List[Dict]:
        """Recherche une pièce dans tous les emplacements"""
        try:
            if not terme_recherche or len(terme_recherche.strip()) < 2:
                return []
            
            return self.repository.rechercher_piece_dans_emplacements(terme_recherche.strip())
        except Exception as e:
            print(f"[ERREUR] Impossible de rechercher la pièce '{terme_recherche}': {e}")
            return []

    def get_statistiques_emplacement(self, emplacement_id: int) -> Dict:
        """Récupère les statistiques détaillées d'un emplacement"""
        try:
            return self.repository.get_statistiques_emplacement(emplacement_id)
        except Exception as e:
            print(f"[ERREUR] Impossible de récupérer les statistiques de l'emplacement {emplacement_id}: {e}")
            return {}

    def valider_dimensions(self, longueur: float, hauteur: float, profondeur: float) -> bool:
        """Valide les dimensions d'un emplacement"""
        try:
            if longueur <= 0 or hauteur <= 0 or profondeur <= 0:
                return False
            
            # Vérifications de cohérence (dimensions raisonnables)
            if longueur > 10000 or hauteur > 10000 or profondeur > 10000:  # 100m max
                return False
            
            return True
        except:
            return False

    def calculer_volume(self, longueur: float, hauteur: float, profondeur: float) -> float:
        """Calcule le volume en cm³"""
        try:
            if self.valider_dimensions(longueur, hauteur, profondeur):
                return longueur * hauteur * profondeur
            return 0.0
        except:
            return 0.0

    def suggerer_emplacement_pour_piece(self, piece_id: int, quantite: int) -> List[Dict]:
        """Suggère les meilleurs emplacements pour stocker une pièce"""
        try:
            # Récupérer les emplacements où la pièce est déjà stockée
            emplacements_existants = self.get_stock_piece_par_emplacement(piece_id)
            
            # Récupérer les emplacements libres
            emplacements_libres = self.get_emplacements_libres(quantite)
            
            suggestions = []
            
            # Priorité 1: Emplacements où la pièce existe déjà
            for emp in emplacements_existants:
                suggestions.append({
                    **emp,
                    'priorite': 1,
                    'raison': f'Pièce déjà présente ({emp["quantite"]} unités)'
                })
            
            # Priorité 2: Emplacements libres avec capacité suffisante
            for emp in emplacements_libres:
                if not any(s['emplacement_id'] == emp['id'] for s in suggestions):
                    suggestions.append({
                        **emp,
                        'priorite': 2,
                        'raison': f'Capacité libre: {emp.get("capacite_restante", "illimitée")}'
                    })
            
            # Trier par priorité puis par capacité restante
            suggestions.sort(key=lambda x: (x['priorite'], -(x.get('capacite_restante') or float('inf'))))
            
            return suggestions[:10]  # Limiter à 10 suggestions
            
        except Exception as e:
            print(f"[ERREUR] Impossible de suggérer des emplacements pour la pièce {piece_id}: {e}")
            return []

    def nettoyer_stocks_vides(self) -> int:
        """Nettoie tous les enregistrements de stock à zéro"""
        try:
            return self.repository.nettoyer_stocks_zero()
        except Exception as e:
            print(f"[ERREUR] Impossible de nettoyer les stocks vides: {e}")
            return 0

    def verifier_coherence_stock_global(self) -> List[Dict]:
        """Vérifie la cohérence entre stock global et stock par emplacement"""
        try:
            with self.db.conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        p.id_piece,
                        p.reference,
                        p.nom,
                        p.stock_actuel,
                        COALESCE(SUM(es.quantite), 0) as total_emplacements,
                        p.stock_actuel - COALESCE(SUM(es.quantite), 0) as difference
                    FROM piece p
                    LEFT JOIN emplacement_stock es ON p.id_piece = es.piece_id
                    GROUP BY p.id_piece, p.reference, p.nom, p.stock_actuel
                    HAVING p.stock_actuel != COALESCE(SUM(es.quantite), 0)
                    ORDER BY ABS(p.stock_actuel - COALESCE(SUM(es.quantite), 0)) DESC
                """)
                
                results = []
                for row in cur.fetchall():
                    results.append({
                        'piece_id': row[0],
                        'reference': row[1],
                        'nom': row[2],
                        'stock_global': row[3],
                        'total_emplacements': row[4],
                        'difference': row[5]
                    })
                
                return results
                
        except Exception as e:
            print(f"[ERREUR] Impossible de vérifier la cohérence des stocks: {e}")
            return []