from APP.models.mouvement_repository import MouvementRepository, TypeMouvementRepository
from APP.models.piece_repository import PieceRepository
from APP.models.emplacement_repository import EmplacementRepository
from APP.models.emplacement_ext_repository import EmplacementExtRepository
from datetime import datetime, date
from typing import List, Dict, Optional
import logging

class MouvementService:
    def __init__(self, db):
        self.db = db
        self.mouvement_repo = MouvementRepository(db)
        self.type_mouvement_repo = TypeMouvementRepository(db)
        self.piece_repo = PieceRepository(db)
        self.emplacement_repo = EmplacementRepository(db)
        self.emplacement_ext_repo = EmplacementExtRepository(db)
        self.logger = logging.getLogger(__name__)

    # === Gestion des mouvements ===
    
    def get_all_mouvements(self, limit: int = 1000, offset: int = 0) -> List[Dict]:
        """Récupère tous les mouvements avec pagination"""
        return self.mouvement_repo.get_all_mouvements(limit, offset)

    def get_mouvement_by_id(self, mouvement_id: int) -> Optional[Dict]:
        """Récupère un mouvement par son ID"""
        return self.mouvement_repo.get_mouvement_by_id(mouvement_id)

    def get_historique_piece(self, piece_id: int, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Récupère l'historique des mouvements pour une pièce"""
        return self.mouvement_repo.get_mouvements_by_piece(piece_id, limit, offset)

    def get_mouvements_periode(self, date_debut: date, date_fin: date, limit: int = 1000, offset: int = 0) -> List[Dict]:
        """Récupère les mouvements dans une période donnée"""
        return self.mouvement_repo.get_mouvements_by_date_range(date_debut, date_fin, limit, offset)

    def count_mouvements(self, filtres: Dict = None) -> int:
        """Compte le nombre total de mouvements (pour pagination)."""
        return self.mouvement_repo.count_mouvements(filtres)

    def creer_mouvement_entree(self, piece_id: int, quantite: int, type_mouvement_id: int,
                              emplacement_destination_id: int = None, utilisateur_id: int = None,
                              reference_document: str = None, commentaire: str = None,
                              cout_unitaire: float = None) -> int:
        """Crée un mouvement d'entrée de stock"""
        try:
            # Vérifier que le type de mouvement est bien une entrée
            type_mouvement = self.type_mouvement_repo.get_type_mouvement_by_id(type_mouvement_id)
            if not type_mouvement or type_mouvement['impact_stock'] != 1:
                raise ValueError("Le type de mouvement doit être une entrée (impact_stock = 1)")

            # Récupérer le stock actuel
            stock_avant = self.mouvement_repo.get_stock_actuel_piece(piece_id)
            stock_apres = stock_avant + quantite

            # Créer le mouvement
            mouvement_data = {
                'piece_id': piece_id,
                'type_mouvement_id': type_mouvement_id,
                'quantite': quantite,
                'emplacement_destination_id': emplacement_destination_id,
                'utilisateur_id': utilisateur_id,
                'reference_document': reference_document,
                'commentaire': commentaire,
                'cout_unitaire': cout_unitaire,
                'stock_avant': stock_avant,
                'stock_apres': stock_apres
            }

            mouvement_id = self.mouvement_repo.add_mouvement(mouvement_data)

            # Mettre à jour le stock de la pièce
            self._update_stock_piece(piece_id, stock_apres)

            # Mettre à jour le stock par emplacement si un emplacement est spécifié
            if emplacement_destination_id:
                self._update_stock_emplacement_entree(emplacement_destination_id, piece_id, quantite, commentaire)

            self.logger.info(f"Mouvement d'entrée created: ID={mouvement_id}, Pièce={piece_id}, Quantité={quantite}")
            return mouvement_id

        except Exception as e:
            self.logger.error(f"Error during la création du mouvement d'entrée: {e}")
            raise

    def creer_mouvement_sortie(self, piece_id: int, quantite: int, type_mouvement_id: int,
                              emplacement_source_id: int = None, utilisateur_id: int = None,
                              reference_document: str = None, commentaire: str = None) -> int:
        """Crée un mouvement de sortie de stock"""
        try:
            # Vérifier que le type de mouvement est bien une sortie
            type_mouvement = self.type_mouvement_repo.get_type_mouvement_by_id(type_mouvement_id)
            if not type_mouvement or type_mouvement['impact_stock'] != -1:
                raise ValueError("Le type de mouvement doit être une sortie (impact_stock = -1)")

            # Récupérer le stock actuel
            stock_avant = self.mouvement_repo.get_stock_actuel_piece(piece_id)
            
            # Vérifier la disponibilité du stock global
            if stock_avant < quantite:
                raise ValueError(f"Stock global insuffisant. Stock actuel: {stock_avant}, Quantité demandée: {quantite}")

            # Si un emplacement source est spécifié, vérifier le stock dans cet emplacement
            if emplacement_source_id:
                stock_emplacement = self._get_stock_emplacement(emplacement_source_id, piece_id)
                if stock_emplacement < quantite:
                    raise ValueError(f"Stock insuffisant dans l'emplacement. Stock disponible: {stock_emplacement}, Quantité demandée: {quantite}")

            stock_apres = stock_avant - quantite

            # Créer le mouvement
            mouvement_data = {
                'piece_id': piece_id,
                'type_mouvement_id': type_mouvement_id,
                'quantite': quantite,
                'emplacement_source_id': emplacement_source_id,
                'utilisateur_id': utilisateur_id,
                'reference_document': reference_document,
                'commentaire': commentaire,
                'stock_avant': stock_avant,
                'stock_apres': stock_apres
            }

            mouvement_id = self.mouvement_repo.add_mouvement(mouvement_data)

            # Mettre à jour le stock de la pièce
            self._update_stock_piece(piece_id, stock_apres)

            # Mettre à jour le stock par emplacement si un emplacement est spécifié
            if emplacement_source_id:
                self._update_stock_emplacement_sortie(emplacement_source_id, piece_id, quantite, commentaire)

            self.logger.info(f"Mouvement de sortie created: ID={mouvement_id}, Pièce={piece_id}, Quantité={quantite}")
            return mouvement_id

        except Exception as e:
            self.logger.error(f"Error during la création du mouvement de sortie: {e}")
            raise

    def creer_mouvement_transfert(self, piece_id: int, quantite: int,
                                 emplacement_source_id: int, emplacement_destination_id: int,
                                 utilisateur_id: int = None, reference_document: str = None,
                                 commentaire: str = None) -> List[int]:
        """Crée un transfert entre emplacements (sortie + entrée)"""
        try:
            # Vérifier que les emplacements sont différents
            if emplacement_source_id == emplacement_destination_id:
                raise ValueError("L'emplacement source et destination doivent être différents")

            # Vérifier le stock disponible dans l'emplacement source
            stock_source = self._get_stock_emplacement(emplacement_source_id, piece_id)
            if stock_source < quantite:
                raise ValueError(f"Stock insuffisant dans l'emplacement source. Stock disponible: {stock_source}, Quantité demandée: {quantite}")

            # Utiliser la fonction de transfert atomique de la base de données
            try:
                self.emplacement_ext_repo.deplacer_stock(
                    piece_id, emplacement_source_id, emplacement_destination_id, quantite, commentaire
                )
            except Exception as e:
                raise ValueError(f"Erreur lors du transfert: {e}")

            # Récupérer les types de mouvement pour transfert
            types_mouvement = self.type_mouvement_repo.get_all_types_mouvement()
            type_sortie_transfert = next((t for t in types_mouvement if t['nom'] == 'TRANSFERT_SORTIE'), None)
            type_entree_transfert = next((t for t in types_mouvement if t['nom'] == 'TRANSFERT_ENTREE'), None)

            if not type_sortie_transfert or not type_entree_transfert:
                raise ValueError("Types de mouvement de transfert non trouvés")

            # Récupérer le stock actuel pour les mouvements
            stock_actuel = self.mouvement_repo.get_stock_actuel_piece(piece_id)

            # Créer le mouvement de sortie (sans modifier le stock global ni l'emplacement)
            mouvement_sortie_data = {
                'piece_id': piece_id,
                'type_mouvement_id': type_sortie_transfert['id'],
                'quantite': quantite,
                'emplacement_source_id': emplacement_source_id,
                'utilisateur_id': utilisateur_id,
                'reference_document': reference_document,
                'commentaire': f"Transfert vers emplacement {emplacement_destination_id}. {commentaire or ''}",
                'stock_avant': stock_actuel,
                'stock_apres': stock_actuel  # Pas de changement du stock global pour un transfert
            }

            mouvement_sortie_id = self.mouvement_repo.add_mouvement(mouvement_sortie_data)

            # Créer le mouvement d'entrée (sans modifier le stock global ni l'emplacement)
            mouvement_entree_data = {
                'piece_id': piece_id,
                'type_mouvement_id': type_entree_transfert['id'],
                'quantite': quantite,
                'emplacement_destination_id': emplacement_destination_id,
                'utilisateur_id': utilisateur_id,
                'reference_document': reference_document,
                'commentaire': f"Transfert depuis emplacement {emplacement_source_id}. {commentaire or ''}",
                'stock_avant': stock_actuel,
                'stock_apres': stock_actuel  # Pas de changement du stock global pour un transfert
            }

            mouvement_entree_id = self.mouvement_repo.add_mouvement(mouvement_entree_data)

            self.logger.info(f"Transfert created: Sortie={mouvement_sortie_id}, Entrée={mouvement_entree_id}")
            return [mouvement_sortie_id, mouvement_entree_id]

        except Exception as e:
            self.logger.error(f"Erreur lors du transfert: {e}")
            raise

    def ajustement_inventaire(self, piece_id: int, nouveau_stock: int, utilisateur_id: int = None,
                             commentaire: str = None) -> int:
        """Effectue un ajustement d'inventaire"""
        try:
            stock_actuel = self.mouvement_repo.get_stock_actuel_piece(piece_id)
            difference = nouveau_stock - stock_actuel

            if difference == 0:
                return None  # Pas de mouvement nécessaire

            # Déterminer le type de mouvement
            types_mouvement = self.type_mouvement_repo.get_all_types_mouvement()
            if difference > 0:
                type_mouvement = next((t for t in types_mouvement if t['nom'] == 'ENTREE_INVENTAIRE'), None)
                quantite = difference
            else:
                type_mouvement = next((t for t in types_mouvement if t['nom'] == 'SORTIE_INVENTAIRE'), None)
                quantite = abs(difference)

            if not type_mouvement:
                raise ValueError("Type de mouvement d'inventaire non trouvé")

            # Créer le mouvement d'ajustement
            mouvement_data = {
                'piece_id': piece_id,
                'type_mouvement_id': type_mouvement['id'],
                'quantite': quantite,
                'utilisateur_id': utilisateur_id,
                'commentaire': f"Ajustement inventaire: {stock_actuel} → {nouveau_stock}. {commentaire or ''}",
                'stock_avant': stock_actuel,
                'stock_apres': nouveau_stock
            }

            mouvement_id = self.mouvement_repo.add_mouvement(mouvement_data)

            # Mettre à jour le stock de la pièce
            self._update_stock_piece(piece_id, nouveau_stock)

            self.logger.info(f"Ajustement inventaire: ID={mouvement_id}, Pièce={piece_id}, {stock_actuel}→{nouveau_stock}")
            return mouvement_id

        except Exception as e:
            self.logger.error(f"Error during l'ajustement d'inventaire: {e}")
            raise

    def annuler_mouvement(self, mouvement_id: int, utilisateur_id: int = None,
                         commentaire: str = None) -> int:
        """Annule un mouvement en créant un mouvement inverse"""
        try:
            # Récupérer le mouvement original
            mouvement_original = self.mouvement_repo.get_mouvement_by_id(mouvement_id)
            if not mouvement_original:
                raise ValueError("Mouvement non trouvé")

            # Déterminer le type de mouvement inverse
            types_mouvement = self.type_mouvement_repo.get_all_types_mouvement()
            impact_inverse = -mouvement_original['impact_stock']
            
            # Pour simplifier, on utilise les types d'inventaire pour l'annulation
            if impact_inverse > 0:
                type_inverse = next((t for t in types_mouvement if t['nom'] == 'ENTREE_INVENTAIRE'), None)
            else:
                type_inverse = next((t for t in types_mouvement if t['nom'] == 'SORTIE_INVENTAIRE'), None)

            if not type_inverse:
                raise ValueError("Type de mouvement inverse non trouvé")

            # Créer le mouvement d'annulation
            stock_actuel = self.mouvement_repo.get_stock_actuel_piece(mouvement_original['piece_id'])
            nouveau_stock = stock_actuel + (mouvement_original['quantite'] * impact_inverse)

            mouvement_data = {
                'piece_id': mouvement_original['piece_id'],
                'type_mouvement_id': type_inverse['id'],
                'quantite': mouvement_original['quantite'],
                'utilisateur_id': utilisateur_id,
                'reference_document': f"ANNUL-{mouvement_original.get('reference_document', '')}",
                'commentaire': f"Annulation mouvement #{mouvement_id}. {commentaire or ''}",
                'stock_avant': stock_actuel,
                'stock_apres': nouveau_stock
            }

            mouvement_annulation_id = self.mouvement_repo.add_mouvement(mouvement_data)

            # Mettre à jour le stock
            self._update_stock_piece(mouvement_original['piece_id'], nouveau_stock)

            # Marquer le mouvement original comme annulé
            self.mouvement_repo.delete_mouvement(mouvement_id)

            self.logger.info(f"Mouvement annulé: Original={mouvement_id}, Annulation={mouvement_annulation_id}")
            return mouvement_annulation_id

        except Exception as e:
            self.logger.error(f"Error during l'annulation du mouvement: {e}")
            raise

    # === Gestion des types de mouvement ===

    def get_all_types_mouvement(self) -> List[Dict]:
        """Récupère tous les types de mouvement"""
        return self.type_mouvement_repo.get_all_types_mouvement()

    def get_types_entree(self) -> List[Dict]:
        """Récupère les types de mouvement d'entrée"""
        return self.type_mouvement_repo.get_types_entree()

    def get_types_sortie(self) -> List[Dict]:
        """Récupère les types de mouvement de sortie"""
        return self.type_mouvement_repo.get_types_sortie()

    def get_types_neutre(self) -> List[Dict]:
        """Récupère les types de mouvement neutres (réception)"""
        return self.type_mouvement_repo.get_types_neutre()

    # === Statistiques et rapports ===

    def get_statistiques_piece(self, piece_id: int) -> Dict:
        """Récupère les statistiques de mouvement pour une pièce"""
        stats = self.mouvement_repo.get_statistiques_mouvements(piece_id)
        return {
            'piece_id': piece_id,
            'mouvements_par_type': stats,
            'stock_actuel': self.mouvement_repo.get_stock_actuel_piece(piece_id)
        }

    def get_rapport_activite(self, date_debut: date, date_fin: date) -> Dict:
        """Génère un rapport d'activité pour une période"""
        mouvements = self.get_mouvements_periode(date_debut, date_fin)
        
        # Calculer les statistiques
        total_mouvements = len(mouvements)
        entrees = [m for m in mouvements if m['impact_stock'] == 1]
        sorties = [m for m in mouvements if m['impact_stock'] == -1]
        
        return {
            'periode': {'debut': date_debut, 'fin': date_fin},
            'total_mouvements': total_mouvements,
            'total_entrees': len(entrees),
            'total_sorties': len(sorties),
            'quantite_entree_totale': sum(m['quantite'] for m in entrees),
            'quantite_sortie_totale': sum(m['quantite'] for m in sorties),
            'valeur_totale': sum(m['cout_total'] or 0 for m in mouvements),
            'mouvements': mouvements
        }

    def get_pieces_stock_faible(self) -> List[Dict]:
        """Récupère les pièces avec un stock faible"""
        with self.db.conn.cursor() as cur:
            cur.execute('''
                SELECT p.*, 
                       (p.stock_alerte - p.stock_actuel) as deficit
                FROM piece p
                WHERE p.stock_actuel <= p.stock_alerte
                ORDER BY deficit DESC;
            ''')
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]

    # === Méthodes privées ===

    def _update_stock_piece(self, piece_id: int, nouveau_stock: int) -> None:
        """Met à jour le stock d'une pièce"""
        with self.db.conn.cursor() as cur:
            cur.execute('''
                UPDATE piece SET stock_actuel = %s, updated_at = NOW()
                WHERE id_piece = %s;
            ''', (nouveau_stock, piece_id))
            self.db.conn.commit()

    def _valider_mouvement_data(self, mouvement_data: Dict) -> None:
        """Valide les données d'un mouvement"""
        required_fields = ['piece_id', 'type_mouvement_id', 'quantite', 'stock_avant', 'stock_apres']
        for field in required_fields:
            if field not in mouvement_data:
                raise ValueError(f"Champ requis manquant: {field}")
        
        if mouvement_data['quantite'] <= 0:
            raise ValueError("La quantité doit être positive")
        
        if mouvement_data['stock_avant'] < 0 or mouvement_data['stock_apres'] < 0:
            raise ValueError("Le stock ne peut pas être négatif")

    def _get_stock_emplacement(self, emplacement_id: int, piece_id: int) -> int:
        """Récupère le stock d'une pièce dans un emplacement spécifique"""
        try:
            stock_item = self.emplacement_ext_repo.get_emplacement_stock_item(emplacement_id, piece_id)
            return stock_item['quantite'] if stock_item else 0
        except Exception as e:
            self.logger.error(f"Error during la retrieval du stock emplacement: {e}")
            return 0

    def _update_stock_emplacement_entree(self, emplacement_id: int, piece_id: int, 
                                        quantite: int, commentaire: str = None) -> None:
        """Met à jour le stock d'un emplacement lors d'une entrée"""
        try:
            self.emplacement_ext_repo.ajouter_stock_emplacement(
                emplacement_id, piece_id, quantite, commentaire
            )
            self.logger.debug(f"Stock emplacement updated: +{quantite} pour pièce {piece_id} dans emplacement {emplacement_id}")
        except Exception as e:
            self.logger.error(f"Error during la mise à jour du stock emplacement (entrée): {e}")
            raise

    def _update_stock_emplacement_sortie(self, emplacement_id: int, piece_id: int, 
                                        quantite: int, commentaire: str = None) -> None:
        """Met à jour le stock d'un emplacement lors d'une sortie"""
        try:
            self.emplacement_ext_repo.retirer_stock_emplacement(
                emplacement_id, piece_id, quantite, commentaire
            )
            self.logger.debug(f"Stock emplacement updated: -{quantite} pour pièce {piece_id} dans emplacement {emplacement_id}")
        except Exception as e:
            self.logger.error(f"Error during la mise à jour du stock emplacement (sortie): {e}")
            raise

    # === Nouvelles méthodes pour la gestion des emplacements ===

    def get_stock_par_emplacement(self, emplacement_id: int) -> List[Dict]:
        """Récupère le stock détaillé d'un emplacement"""
        try:
            return self.emplacement_ext_repo.get_stock_by_emplacement(emplacement_id)
        except Exception as e:
            self.logger.error(f"Error during la retrieval du stock par emplacement: {e}")
            return []

    def get_emplacements_piece(self, piece_id: int) -> List[Dict]:
        """Récupère tous les emplacements où se trouve une pi��ce"""
        try:
            return self.emplacement_ext_repo.get_piece_emplacements(piece_id)
        except Exception as e:
            self.logger.error(f"Error during la retrieval des emplacements pour la pièce: {e}")
            return []

    def suggerer_emplacement_pour_entree(self, piece_id: int, quantite: int) -> List[Dict]:
        """Suggère les meilleurs emplacements pour une entrée de stock"""
        try:
            from APP.services.emplacement_ext_service import EmplacementExtService
            service = EmplacementExtService(self.db)
            return service.suggerer_emplacement_pour_piece(piece_id, quantite)
        except Exception as e:
            self.logger.error(f"Error during la suggestion d'emplacements: {e}")
            return []

    def verifier_coherence_stocks(self) -> List[Dict]:
        """Vérifie la cohérence entre stocks globaux et stocks par emplacement"""
        try:
            from APP.services.emplacement_ext_service import EmplacementExtService
            service = EmplacementExtService(self.db)
            return service.verifier_coherence_stock_global()
        except Exception as e:
            self.logger.error(f"Error during la vérification de cohérence: {e}")
            return []

    def corriger_incoherence_stock(self, piece_id: int, forcer_stock_global: bool = True) -> bool:
        """Corrige une incohérence de stock en synchronisant les données"""
        try:
            if forcer_stock_global:
                # Recalculer le stock global à partir des emplacements
                emplacements = self.get_emplacements_piece(piece_id)
                nouveau_stock_global = sum(emp['quantite'] for emp in emplacements)
                self._update_stock_piece(piece_id, nouveau_stock_global)
                self.logger.info(f"Stock global corrigé pour pièce {piece_id}: {nouveau_stock_global}")
            else:
                # Répartir le stock global dans un emplacement par défaut
                stock_global = self.mouvement_repo.get_stock_actuel_piece(piece_id)
                # TODO: Implémenter la logique de répartition
                pass
            
            return True
        except Exception as e:
            self.logger.error(f"Error during la correction d'incohérence: {e}")
            return False

    def vider_piece_de_tous_emplacements(self, piece_id: int, utilisateur_id: int = None,
                                         commentaire: str = None) -> int:
        """Vide la pièce de tous les emplacements en générant des sorties d'inventaire par emplacement.

        Retourne le nombre de mouvements createds.
        """
        try:
            # Récupérer les emplacements où se trouve la pièce
            emplacements = self.get_emplacements_piece(piece_id)

            if not emplacements:
                return 0

            # Trouver le type de mouvement SORTIE_INVENTAIRE
            types_mouvement = self.get_all_types_mouvement()
            type_sortie_inventaire = next((t for t in types_mouvement if t['nom'] == 'SORTIE_INVENTAIRE'), None)
            if not type_sortie_inventaire:
                raise ValueError("Type de mouvement SORTIE_INVENTAIRE non trouvé")

            mouvements_crees = 0
            for emp in emplacements:
                try:
                    quantite = emp.get('quantite') or 0
                    emplacement_id = emp.get('emplacement_id') or emp.get('id')
                    if emplacement_id is None:
                        # Impossible d'identifier l'emplacement dans la vue
                        continue
                    if quantite and quantite > 0:
                        self.creer_mouvement_sortie(
                            piece_id=piece_id,
                            quantite=quantite,
                            type_mouvement_id=type_sortie_inventaire['id'],
                            emplacement_source_id=emplacement_id,
                            utilisateur_id=utilisateur_id,
                            reference_document=f"VIDAGE-PIECE-{piece_id}",
                            commentaire=f"Vidage de l'emplacement {emplacement_id}. {commentaire or ''}".strip()
                        )
                        mouvements_crees += 1
                except Exception as e:
                    # Continuer les autres emplacements mais journaliser l'erreur
                    self.logger.error(f"Echec vidage emplacement pour pièce {piece_id}: {e}")

            return mouvements_crees
        except Exception as e:
            self.logger.error(f"Erreur lors du vidage des emplacements pour la pièce {piece_id}: {e}")
            raise

    def transferer_piece_de_tous_emplacements(self, piece_id: int, emplacement_destination_id: int,
                                              utilisateur_id: int = None, commentaire: str = None) -> int:
        """Transfère toute la quantité présente de la pièce depuis tous ses emplacements
        vers un emplacement destination (ex: 'waste'). Crée des mouvements TRANSFERT_SORTIE/ENTREE.

        Retourne le nombre de transferts effectués (paires sortie+entrée comptées comme 1 transfert par source).
        """
        try:
            # Vérifier que l'emplacement destination existe
            dest = self.emplacement_repo.get_emplacement_by_id(emplacement_destination_id)
            if not dest:
                raise ValueError(f"Emplacement destination {emplacement_destination_id} introuvable")

            emplacements = self.get_emplacements_piece(piece_id)
            if not emplacements:
                return 0

            transferts_effectues = 0
            for emp in emplacements:
                try:
                    quantite = emp.get('quantite') or 0
                    source_id = emp.get('emplacement_id') or emp.get('id')
                    if source_id is None or source_id == emplacement_destination_id:
                        continue
                    if quantite and quantite > 0:
                        self.creer_mouvement_transfert(
                            piece_id=piece_id,
                            quantite=quantite,
                            emplacement_source_id=source_id,
                            emplacement_destination_id=emplacement_destination_id,
                            utilisateur_id=utilisateur_id,
                            reference_document=f"TRANSFERT-WASTE-PIECE-{piece_id}",
                            commentaire=f"Transfert total vers {emplacement_destination_id}. {commentaire or ''}".strip()
                        )
                        transferts_effectues += 1
                except Exception as e:
                    self.logger.error(f"Echec transfert depuis emplacement {emp} pour pièce {piece_id}: {e}")
            return transferts_effectues
        except Exception as e:
            self.logger.error(f"Erreur lors du transfert de tous les emplacements vers {emplacement_destination_id} pour la pièce {piece_id}: {e}")
            raise

    def creer_mouvement_reception(self, piece_id: int, quantite: int, type_mouvement_id: int,
                                 emplacement_destination_id: int = None, utilisateur_id: int = None,
                                 reference_document: str = None, commentaire: str = None,
                                 cout_unitaire: float = None, statut_mouvement: str = 'EN_ATTENTE') -> int:
        """Crée un mouvement de réception (impact_stock = 0, n'affecte pas les emplacements)"""
        try:
            # Vérifier que le type de mouvement est bien une réception
            type_mouvement = self.type_mouvement_repo.get_type_mouvement_by_id(type_mouvement_id)
            if not type_mouvement or type_mouvement['impact_stock'] != 0:
                raise ValueError("Le type de mouvement doit être une réception (impact_stock = 0)")

            # Récupérer le stock actuel (ne change pas pour une réception)
            stock_avant = self.mouvement_repo.get_stock_actuel_piece(piece_id)
            stock_apres = stock_avant  # Pas de changement pour une réception

            # Créer le mouvement
            mouvement_data = {
                'piece_id': piece_id,
                'type_mouvement_id': type_mouvement_id,
                'quantite': quantite,
                'emplacement_destination_id': emplacement_destination_id,
                'utilisateur_id': utilisateur_id,
                'reference_document': reference_document,
                'commentaire': commentaire,
                'cout_unitaire': cout_unitaire,
                'stock_avant': stock_avant,
                'stock_apres': stock_apres,
                'statut_mouvement': statut_mouvement
            }

            mouvement_id = self.mouvement_repo.add_mouvement(mouvement_data)

            # NE PAS mettre à jour le stock de la pièce (réception seulement)
            # NE PAS mettre à jour le stock par emplacement (réception seulement)

            self.logger.info(f"Mouvement de réception created: ID={mouvement_id}, Pièce={piece_id}, Quantité={quantite}, Statut={statut_mouvement}")
            return mouvement_id

        except Exception as e:
            self.logger.error(f"Error during la création du mouvement de réception: {e}")
            raise

    def confirmer_mouvement_reception(self, mouvement_id: int, utilisateur_id: int = None,
                                     commentaire_confirmation: str = None) -> bool:
        """Confirme un mouvement de réception et l'applique au stock"""
        try:
            with self.db.conn.cursor() as cur:
                # Utiliser la fonction SQL pour confirmer le mouvement
                cur.execute('''
                    SELECT confirmer_mouvement_en_attente(%s, %s, %s);
                ''', (mouvement_id, utilisateur_id, commentaire_confirmation))
                
                result = cur.fetchone()[0]
                self.db.conn.commit()
                
                if result:
                    self.logger.info(f"Mouvement {mouvement_id} confirmé avec success")
                
                return result
                
        except Exception as e:
            self.logger.error(f"Error during la confirmation du mouvement {mouvement_id}: {e}")
            self.db.conn.rollback()
            raise

    def annuler_mouvement_reception(self, mouvement_id: int, utilisateur_id: int = None,
                                   raison_annulation: str = None) -> bool:
        """Annule un mouvement de réception en attente"""
        try:
            with self.db.conn.cursor() as cur:
                # Utiliser la fonction SQL pour annuler le mouvement
                cur.execute('''
                    SELECT annuler_mouvement_en_attente(%s, %s, %s);
                ''', (mouvement_id, utilisateur_id, raison_annulation))
                
                result = cur.fetchone()[0]
                self.db.conn.commit()
                
                if result:
                    self.logger.info(f"Mouvement {mouvement_id} annulé avec success")
                
                return result
                
        except Exception as e:
            self.logger.error(f"Error during l'annulation du mouvement {mouvement_id}: {e}")
            self.db.conn.rollback()
            raise

    def get_mouvements_en_attente(self, limit: int = 100) -> List[Dict]:
        """Récupère tous les mouvements en attente de confirmation"""
        try:
            with self.db.conn.cursor() as cur:
                cur.execute('''
                    SELECT * FROM v_mouvements_en_attente
                    ORDER BY date_mouvement ASC
                    LIMIT %s;
                ''', (limit,))
                
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Error during la retrieval des mouvements en attente: {e}")
            return []

    def get_dashboard_reception(self) -> Dict:
        """Récupère les indicateurs du tableau de bord réception"""
        try:
            with self.db.conn.cursor() as cur:
                cur.execute('SELECT * FROM v_dashboard_reception;')
                
                dashboard = {}
                for row in cur.fetchall():
                    dashboard[row[0]] = {
                        'valeur': row[1],
                        'description': row[2]
                    }
                
                return dashboard
                
        except Exception as e:
            self.logger.error(f"Error during la retrieval du dashboard: {e}")
            return {}