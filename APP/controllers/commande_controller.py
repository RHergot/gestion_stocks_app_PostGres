"""Contrôleur pour la gestion des commandes (workflow métier).

Extrait de commande_view.py — logique métier pure, sans UI.
Le contrôleur ne fait PAS de QMessageBox ; il retourne des résultats
ou lève des exceptions que la vue gère.
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class CommandeController:
    """Gère le workflow des commandes : statuts, livraison, copie."""

    def __init__(self, db, commande_repo, ligne_commande_repo):
        self.db = db
        self.commande_repo = commande_repo
        self.ligne_commande_repo = ligne_commande_repo

    def changer_statut(self, commande_id, nouveau_statut):
        """Change le statut d'une commande. Lève une exception en cas d'échec."""
        update_data = {'statut': nouveau_statut}
        if nouveau_statut == 'Livree':
            update_data['date_livraison_reelle'] = datetime.now().strftime('%Y-%m-%d')

        success = self.commande_repo.update_commande(commande_id, update_data)
        if not success:
            raise RuntimeError("Unable to change the order status.")
        logger.info("Commande %s → statut %s", commande_id, nouveau_statut)
        return True

    def creer_mouvements_livraison(self, commande):
        """Crée les mouvements de stock pour la livraison d'une commande."""
        from APP.services.mouvement_service import MouvementService

        mouvement_service = MouvementService(self.db)
        lignes = self.ligne_commande_repo.get_lignes_by_commande_id(commande['id_commande'])
        types_mouvement = mouvement_service.get_all_types_mouvement()
        type_entree_achat = next(
            (t for t in types_mouvement if t['nom'] == 'ENTREE_ACHAT'), None
        )
        if not type_entree_achat:
            raise ValueError("Type de mouvement ENTREE_ACHAT non trouvé")

        mouvements_crees = 0
        for ligne in lignes:
            mouvement_service.creer_mouvement_entree(
                piece_id=ligne['piece_id'],
                quantite=ligne['quantite_commandee'],
                type_mouvement_id=type_entree_achat['id'],
                reference_document=f"CMD-{commande['numero_commande']}",
                commentaire=f"Livraison commande {commande['numero_commande']}",
                cout_unitaire=ligne.get('prix_unitaire_ht')
            )
            mouvements_crees += 1

        logger.info("%s mouvements créés pour commande %s", mouvements_crees, commande['numero_commande'])
        return mouvements_crees

    def creer_copie_commande(self, commande_originale):
        """Crée une copie d'une commande avec ses lignes.

        Returns:
            tuple: (nouveau_commande_id, nouveau_numero)
        """
        createur_id = self.commande_repo.get_default_user_id()
        if not createur_id:
            raise ValueError("Aucun utilisateur Admin trouvé. Créez un compte admin d'abord.")

        nouveau_numero = self.generer_nouveau_numero()
        nouvelle_commande_data = {
            'numero_commande': nouveau_numero,
            'fournisseur_id': commande_originale['fournisseur_id'],
            'createur_id': createur_id,
            'date_commande': datetime.now().strftime('%Y-%m-%d'),
            'date_livraison_prevue': commande_originale.get('date_livraison_prevue'),
            'statut': 'Brouillon',
            'total_ht': commande_originale.get('total_ht', 0),
            'frais_port': commande_originale.get('frais_port', 0),
            'reference_fournisseur': commande_originale.get('reference_fournisseur'),
            'mode_paiement': commande_originale.get('mode_paiement'),
            'notes_commande': f"Copy of order {commande_originale['numero_commande']}"
        }

        nouvelle_commande_id = self.commande_repo.add_commande(nouvelle_commande_data)
        lignes_originales = self.ligne_commande_repo.get_lignes_by_commande_id(
            commande_originale['id_commande']
        )

        for ligne in lignes_originales:
            self.ligne_commande_repo.add_ligne_commande({
                'commande_id': nouvelle_commande_id,
                'piece_id': ligne['piece_id'],
                'quantite_commandee': ligne['quantite_commandee'],
                'prix_unitaire_ht': ligne['prix_unitaire_ht'],
                'description_libre': ligne.get('description_libre')
            })

        logger.info("Commande copiée : %s → %s (ID %s)",
                     commande_originale['numero_commande'], nouveau_numero, nouvelle_commande_id)
        return nouvelle_commande_id, nouveau_numero

    def generer_nouveau_numero(self):
        """Génère un nouveau numéro de commande unique (via SQL MAX)."""
        try:
            with self.db.conn.cursor() as cur:
                cur.execute(
                    "SELECT MAX(CAST(NULLIF(regexp_replace(numero_commande, '[^0-9]', '', 'g'), '') AS INTEGER)) "
                    "FROM commande"
                )
                result = cur.fetchone()
                max_num = result[0] if result and result[0] else 0
            return str(max_num + 1)
        except Exception:
            return f"CMD-{int(datetime.now().timestamp())}"
