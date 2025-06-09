from APP.services.mouvement_service import MouvementService
from APP.services.piece_service import PieceService
from APP.services.emplacement_service import EmplacementService
from APP.services.user_service import UserService
from datetime import datetime, date
from typing import List, Dict, Optional
import logging

class MouvementController:
    """Contrôleur pour la gestion des mouvements de stock"""
    
    def __init__(self, db):
        self.db = db
        self.mouvement_service = MouvementService(db)
        self.piece_service = PieceService(db)
        self.emplacement_service = EmplacementService(db)
        self.user_service = UserService(db)
        self.logger = logging.getLogger(__name__)

    # === Actions principales ===

    def lister_mouvements(self, filtres: Dict = None) -> List[Dict]:
        """Liste les mouvements avec filtres optionnels"""
        try:
            if not filtres:
                return self.mouvement_service.get_all_mouvements()
            
            # Appliquer les filtres
            if 'piece_id' in filtres:
                return self.mouvement_service.get_historique_piece(filtres['piece_id'])
            
            if 'date_debut' in filtres and 'date_fin' in filtres:
                return self.mouvement_service.get_mouvements_periode(
                    filtres['date_debut'], filtres['date_fin']
                )
            
            return self.mouvement_service.get_all_mouvements()
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la liste des mouvements: {e}")
            raise

    def obtenir_mouvement(self, mouvement_id: int) -> Optional[Dict]:
        """Obtient un mouvement par son ID"""
        try:
            return self.mouvement_service.get_mouvement_by_id(mouvement_id)
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération du mouvement {mouvement_id}: {e}")
            raise

    def effectuer_entree_stock(self, piece_id: int, quantite: int, type_mouvement: str,
                              emplacement_id: int = None, utilisateur_id: int = None,
                              reference: str = None, commentaire: str = None,
                              cout_unitaire: float = None) -> Dict:
        """Effectue une entrée de stock"""
        try:
            # Valider les données
            self._valider_piece_existe(piece_id)
            self._valider_quantite_positive(quantite)
            
            if emplacement_id:
                self._valider_emplacement_existe(emplacement_id)
            
            # Récupérer le type de mouvement
            type_mouvement_id = self._obtenir_type_mouvement_id(type_mouvement, impact_attendu=1)
            
            # Effectuer l'entrée
            mouvement_id = self.mouvement_service.creer_mouvement_entree(
                piece_id=piece_id,
                quantite=quantite,
                type_mouvement_id=type_mouvement_id,
                emplacement_destination_id=emplacement_id,
                utilisateur_id=utilisateur_id,
                reference_document=reference,
                commentaire=commentaire,
                cout_unitaire=cout_unitaire
            )
            
            return {
                'success': True,
                'mouvement_id': mouvement_id,
                'message': f'Entrée de {quantite} unités effectuée avec succès'
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'entrée de stock: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Erreur lors de l\'entrée de stock'
            }

    def effectuer_sortie_stock(self, piece_id: int, quantite: int, type_mouvement: str,
                              emplacement_id: int = None, utilisateur_id: int = None,
                              reference: str = None, commentaire: str = None) -> Dict:
        """Effectue une sortie de stock"""
        try:
            # Valider les données
            self._valider_piece_existe(piece_id)
            self._valider_quantite_positive(quantite)
            self._valider_stock_suffisant(piece_id, quantite)
            
            if emplacement_id:
                self._valider_emplacement_existe(emplacement_id)
            
            # Récupérer le type de mouvement
            type_mouvement_id = self._obtenir_type_mouvement_id(type_mouvement, impact_attendu=-1)
            
            # Effectuer la sortie
            mouvement_id = self.mouvement_service.creer_mouvement_sortie(
                piece_id=piece_id,
                quantite=quantite,
                type_mouvement_id=type_mouvement_id,
                emplacement_source_id=emplacement_id,
                utilisateur_id=utilisateur_id,
                reference_document=reference,
                commentaire=commentaire
            )
            
            return {
                'success': True,
                'mouvement_id': mouvement_id,
                'message': f'Sortie de {quantite} unités effectuée avec succès'
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la sortie de stock: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Erreur lors de la sortie de stock'
            }

    def effectuer_transfert(self, piece_id: int, quantite: int,
                           emplacement_source_id: int, emplacement_destination_id: int,
                           utilisateur_id: int = None, reference: str = None,
                           commentaire: str = None) -> Dict:
        """Effectue un transfert entre emplacements"""
        try:
            # Valider les données
            self._valider_piece_existe(piece_id)
            self._valider_quantite_positive(quantite)
            self._valider_stock_suffisant(piece_id, quantite)
            self._valider_emplacement_existe(emplacement_source_id)
            self._valider_emplacement_existe(emplacement_destination_id)
            
            if emplacement_source_id == emplacement_destination_id:
                raise ValueError("L'emplacement source et destination doivent être différents")
            
            # Effectuer le transfert
            mouvement_ids = self.mouvement_service.creer_mouvement_transfert(
                piece_id=piece_id,
                quantite=quantite,
                emplacement_source_id=emplacement_source_id,
                emplacement_destination_id=emplacement_destination_id,
                utilisateur_id=utilisateur_id,
                reference_document=reference,
                commentaire=commentaire
            )
            
            return {
                'success': True,
                'mouvement_ids': mouvement_ids,
                'message': f'Transfert de {quantite} unités effectué avec succès'
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors du transfert: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Erreur lors du transfert'
            }

    def effectuer_ajustement_inventaire(self, piece_id: int, nouveau_stock: int,
                                       utilisateur_id: int = None, commentaire: str = None) -> Dict:
        """Effectue un ajustement d'inventaire"""
        try:
            # Valider les données
            self._valider_piece_existe(piece_id)
            
            if nouveau_stock < 0:
                raise ValueError("Le nouveau stock ne peut pas être négatif")
            
            # Effectuer l'ajustement
            mouvement_id = self.mouvement_service.ajustement_inventaire(
                piece_id=piece_id,
                nouveau_stock=nouveau_stock,
                utilisateur_id=utilisateur_id,
                commentaire=commentaire
            )
            
            if mouvement_id is None:
                return {
                    'success': True,
                    'message': 'Aucun ajustement nécessaire (stock identique)'
                }
            
            return {
                'success': True,
                'mouvement_id': mouvement_id,
                'message': f'Ajustement d\'inventaire effectué avec succès'
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'ajustement d'inventaire: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Erreur lors de l\'ajustement d\'inventaire'
            }

    def annuler_mouvement(self, mouvement_id: int, utilisateur_id: int = None,
                         commentaire: str = None) -> Dict:
        """Annule un mouvement"""
        try:
            # Vérifier que le mouvement existe
            mouvement = self.mouvement_service.get_mouvement_by_id(mouvement_id)
            if not mouvement:
                raise ValueError("Mouvement non trouvé")
            
            # Effectuer l'annulation
            mouvement_annulation_id = self.mouvement_service.annuler_mouvement(
                mouvement_id=mouvement_id,
                utilisateur_id=utilisateur_id,
                commentaire=commentaire
            )
            
            return {
                'success': True,
                'mouvement_annulation_id': mouvement_annulation_id,
                'message': 'Mouvement annulé avec succès'
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'annulation du mouvement: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Erreur lors de l\'annulation du mouvement'
            }

    # === Rapports et statistiques ===

    def obtenir_historique_piece(self, piece_id: int, limite: int = 100) -> Dict:
        """Obtient l'historique complet d'une pièce"""
        try:
            self._valider_piece_existe(piece_id)
            
            historique = self.mouvement_service.get_historique_piece(piece_id, limite)
            statistiques = self.mouvement_service.get_statistiques_piece(piece_id)
            
            return {
                'success': True,
                'piece_id': piece_id,
                'historique': historique,
                'statistiques': statistiques
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération de l'historique: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def generer_rapport_activite(self, date_debut: date, date_fin: date) -> Dict:
        """Génère un rapport d'activité pour une période"""
        try:
            if date_debut > date_fin:
                raise ValueError("La date de début doit être antérieure à la date de fin")
            
            rapport = self.mouvement_service.get_rapport_activite(date_debut, date_fin)
            
            return {
                'success': True,
                'rapport': rapport
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la génération du rapport: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def obtenir_pieces_stock_faible(self) -> Dict:
        """Obtient la liste des pièces avec un stock faible"""
        try:
            pieces = self.mouvement_service.get_pieces_stock_faible()
            
            return {
                'success': True,
                'pieces': pieces,
                'count': len(pieces)
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des stocks faibles: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    # === Données de référence ===

    def obtenir_types_mouvement(self, filtre_type: str = None) -> List[Dict]:
        """Obtient les types de mouvement disponibles"""
        try:
            if filtre_type == 'entree':
                return self.mouvement_service.get_types_entree()
            elif filtre_type == 'sortie':
                return self.mouvement_service.get_types_sortie()
            elif filtre_type == 'neutre' or filtre_type == 'reception':
                return self.mouvement_service.get_types_neutre()
            else:
                return self.mouvement_service.get_all_types_mouvement()
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des types de mouvement: {e}")
            raise

    def obtenir_pieces_disponibles(self) -> List[Dict]:
        """Obtient la liste des pièces disponibles"""
        try:
            return self.piece_service.get_all_pieces()
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des pièces: {e}")
            raise

    def obtenir_emplacements_disponibles(self) -> List[Dict]:
        """Obtient la liste des emplacements disponibles"""
        try:
            return self.emplacement_service.get_all_emplacements()
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des emplacements: {e}")
            raise

    def get_pieces_en_reception(self) -> List[Dict]:
        """Récupère les pièces actuellement en zone de réception"""
        try:
            from APP.services.reception_workflow_service import ReceptionWorkflowService
            reception_service = ReceptionWorkflowService(self.db)
            return reception_service.get_stock_en_reception()
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des pièces en réception: {e}")
            raise

    def get_reception_stock_summary(self) -> Dict:
        """Récupère un résumé du stock en réception"""
        try:
            from APP.services.reception_workflow_service import ReceptionWorkflowService
            reception_service = ReceptionWorkflowService(self.db)
            
            # Récupérer les pièces en réception
            pieces_en_reception = reception_service.get_stock_en_reception()
            lots_en_attente = reception_service.get_lots_en_attente()
            
            # Calculer les totaux
            total_pieces = len(pieces_en_reception)
            total_quantite = sum(piece.get('quantite_en_reception', 0) for piece in pieces_en_reception)
            total_lots = len(lots_en_attente)
            
            return {
                'success': True,
                'total_pieces': total_pieces,
                'total_quantite': total_quantite,
                'total_lots': total_lots,
                'pieces_detail': pieces_en_reception,
                'lots_detail': lots_en_attente
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération du résumé de réception: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_pieces': 0,
                'total_quantite': 0,
                'total_lots': 0,
                'pieces_detail': [],
                'lots_detail': []
            }

    # === Méthodes de validation privées ===

    def _valider_piece_existe(self, piece_id: int) -> None:
        """Valide qu'une pièce existe"""
        piece = self.piece_service.get_piece_by_id(piece_id)
        if not piece:
            raise ValueError(f"Pièce avec ID {piece_id} non trouvée")

    def _valider_emplacement_existe(self, emplacement_id: int) -> None:
        """Valide qu'un emplacement existe"""
        emplacement = self.emplacement_service.get_emplacement_by_id(emplacement_id)
        if not emplacement:
            raise ValueError(f"Emplacement avec ID {emplacement_id} non trouvé")

    def _valider_quantite_positive(self, quantite: int) -> None:
        """Valide qu'une quantité est positive"""
        if quantite <= 0:
            raise ValueError("La quantité doit être positive")

    def _valider_stock_suffisant(self, piece_id: int, quantite_demandee: int) -> None:
        """Valide qu'il y a suffisamment de stock"""
        stock_actuel = self.mouvement_service.mouvement_repo.get_stock_actuel_piece(piece_id)
        if stock_actuel < quantite_demandee:
            raise ValueError(f"Stock insuffisant. Stock actuel: {stock_actuel}, Quantité demandée: {quantite_demandee}")

    def _obtenir_type_mouvement_id(self, nom_type_mouvement: str, impact_attendu: int = None) -> int:
        """Obtient l'ID d'un type de mouvement par son nom"""
        try:
            types_mouvement = self.mouvement_service.get_all_types_mouvement()
            
            # Chercher le type de mouvement par nom
            type_trouve = None
            for type_mouvement in types_mouvement:
                if type_mouvement['nom'] == nom_type_mouvement:
                    type_trouve = type_mouvement
                    break
            
            if not type_trouve:
                raise ValueError(f"Type de mouvement '{nom_type_mouvement}' non trouvé")
            
            # Vérifier l'impact si spécifié
            if impact_attendu is not None and type_trouve['impact_stock'] != impact_attendu:
                raise ValueError(f"Type de mouvement '{nom_type_mouvement}' a un impact de {type_trouve['impact_stock']}, attendu: {impact_attendu}")
            
            return type_trouve['id']
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération du type de mouvement '{nom_type_mouvement}': {e}")
            raise

    # === Workflow de réception ===

    def effectuer_reception_achat(self, piece_id: int, quantite: int,
                                 emplacement_reception_id: int = None, utilisateur_id: int = None,
                                 reference: str = None, commentaire: str = None,
                                 cout_unitaire: float = None) -> Dict:
        """Effectue une réception d'achat (zone de réception, sans impact sur stock emplacement)"""
        try:
            # Valider les données
            self._valider_piece_existe(piece_id)
            self._valider_quantite_positive(quantite)
            
            if emplacement_reception_id:
                self._valider_emplacement_existe(emplacement_reception_id)
            
            # Récupérer le type de mouvement RECEPTION_ACHAT
            type_mouvement_id = self._obtenir_type_mouvement_id('RECEPTION_ACHAT', impact_attendu=0)
            
            # Effectuer la réception
            mouvement_id = self.mouvement_service.creer_mouvement_reception(
                piece_id=piece_id,
                quantite=quantite,
                type_mouvement_id=type_mouvement_id,
                emplacement_destination_id=emplacement_reception_id,
                utilisateur_id=utilisateur_id,
                reference_document=reference,
                commentaire=commentaire,
                cout_unitaire=cout_unitaire
            )
            
            return {
                'success': True,
                'mouvement_id': mouvement_id,
                'message': f'Réception de {quantite} unités effectuée avec succès (zone de réception)',
                'type_operation': 'RECEPTION_ACHAT'
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la réception d'achat: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Erreur lors de la réception d\'achat'
            }

    def effectuer_mise_en_stock(self, piece_id: int, quantite: int,
                               emplacement_stockage_id: int, utilisateur_id: int = None,
                               reference: str = None, commentaire: str = None) -> Dict:
        """Effectue la mise en stock depuis la réception vers l'emplacement final"""
        try:
            # Valider les données
            self._valider_piece_existe(piece_id)
            self._valider_quantite_positive(quantite)
            self._valider_emplacement_existe(emplacement_stockage_id)
            
            # Récupérer le type de mouvement MISE_EN_STOCK
            type_mouvement_id = self._obtenir_type_mouvement_id('MISE_EN_STOCK', impact_attendu=1)
            
            # Effectuer la mise en stock
            mouvement_id = self.mouvement_service.creer_mouvement_entree(
                piece_id=piece_id,
                quantite=quantite,
                type_mouvement_id=type_mouvement_id,
                emplacement_destination_id=emplacement_stockage_id,
                utilisateur_id=utilisateur_id,
                reference_document=reference,
                commentaire=commentaire
            )
            
            return {
                'success': True,
                'mouvement_id': mouvement_id,
                'message': f'Mise en stock de {quantite} unités effectuée avec succès',
                'type_operation': 'MISE_EN_STOCK'
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la mise en stock: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Erreur lors de la mise en stock'
            }

    def effectuer_sortie_reception(self, piece_id: int, quantite: int,
                                  emplacement_reception_id: int = None, utilisateur_id: int = None,
                                  reference: str = None, commentaire: str = None) -> Dict:
        """Effectue une sortie de la zone de réception (retour fournisseur, etc.)"""
        try:
            # Valider les données
            self._valider_piece_existe(piece_id)
            self._valider_quantite_positive(quantite)
            
            if emplacement_reception_id:
                self._valider_emplacement_existe(emplacement_reception_id)
            
            # Récupérer le type de mouvement SORTIE_RECEPTION
            type_mouvement_id = self._obtenir_type_mouvement_id('SORTIE_RECEPTION', impact_attendu=-1)
            
            # Effectuer la sortie de réception
            mouvement_id = self.mouvement_service.creer_mouvement_sortie(
                piece_id=piece_id,
                quantite=quantite,
                type_mouvement_id=type_mouvement_id,
                emplacement_source_id=emplacement_reception_id,
                utilisateur_id=utilisateur_id,
                reference_document=reference,
                commentaire=commentaire
            )
            
            return {
                'success': True,
                'mouvement_id': mouvement_id,
                'message': f'Sortie de réception de {quantite} unités effectuée avec succès',
                'type_operation': 'SORTIE_RECEPTION'
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la sortie de réception: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Erreur lors de la sortie de réception'
            }

    def effectuer_retour_reception(self, piece_id: int, quantite: int,
                                  emplacement_reception_id: int = None, utilisateur_id: int = None,
                                  reference: str = None, commentaire: str = None) -> Dict:
        """Effectue un retour vers la zone de réception"""
        try:
            # Valider les données
            self._valider_piece_existe(piece_id)
            self._valider_quantite_positive(quantite)
            
            if emplacement_reception_id:
                self._valider_emplacement_existe(emplacement_reception_id)
            
            # Récupérer le type de mouvement RETOUR_RECEPTION
            type_mouvement_id = self._obtenir_type_mouvement_id('RETOUR_RECEPTION', impact_attendu=0)
            
            # Effectuer le retour vers réception
            mouvement_id = self.mouvement_service.creer_mouvement_reception(
                piece_id=piece_id,
                quantite=quantite,
                type_mouvement_id=type_mouvement_id,
                emplacement_destination_id=emplacement_reception_id,
                utilisateur_id=utilisateur_id,
                reference_document=reference,
                commentaire=commentaire
            )
            
            return {
                'success': True,
                'mouvement_id': mouvement_id,
                'message': f'Retour en réception de {quantite} unités effectué avec succès',
                'type_operation': 'RETOUR_RECEPTION'
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors du retour en réception: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Erreur lors du retour en réception'
            }

    def obtenir_types_mouvement_reception(self) -> List[Dict]:
        """Obtient les types de mouvement spécifiques au workflow de réception"""
        try:
            types_mouvement = self.mouvement_service.get_all_types_mouvement()
            types_reception = [
                t for t in types_mouvement 
                if t['nom'] in ['RECEPTION_ACHAT', 'MISE_EN_STOCK', 'SORTIE_RECEPTION', 'RETOUR_RECEPTION']
            ]
            return types_reception
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des types de mouvement de réception: {e}")
            raise

    def valider_workflow_reception(self, piece_id: int, quantite_recue: int, 
                                  quantite_mise_en_stock: int) -> Dict:
        """Valide la cohérence du workflow de réception"""
        try:
            # Récupérer les mouvements de réception pour cette pièce
            historique = self.mouvement_service.get_historique_piece(piece_id)
            
            # Calculer les quantités en réception
            receptions = [m for m in historique if m['type_mouvement_nom'] == 'RECEPTION_ACHAT']
            mises_en_stock = [m for m in historique if m['type_mouvement_nom'] == 'MISE_EN_STOCK']
            sorties_reception = [m for m in historique if m['type_mouvement_nom'] == 'SORTIE_RECEPTION']
            retours_reception = [m for m in historique if m['type_mouvement_nom'] == 'RETOUR_RECEPTION']
            
            total_recu = sum(m['quantite'] for m in receptions) + sum(m['quantite'] for m in retours_reception)
            total_sorti_reception = sum(m['quantite'] for m in sorties_reception)
            total_mis_en_stock = sum(m['quantite'] for m in mises_en_stock)
            
            quantite_en_reception = total_recu - total_sorti_reception - total_mis_en_stock
            
            return {
                'success': True,
                'piece_id': piece_id,
                'total_recu': total_recu,
                'total_mis_en_stock': total_mis_en_stock,
                'total_sorti_reception': total_sorti_reception,
                'quantite_en_reception': quantite_en_reception,
                'coherent': quantite_en_reception >= 0
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la validation du workflow: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    # === Rapports et statistiques ===