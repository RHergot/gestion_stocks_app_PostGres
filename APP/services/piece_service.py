from APP.models.piece_repository import PieceRepository
from APP.models.piece_unit_repository import PieceUnitRepository
from APP.models.piece_category_repository import PieceCategoryRepository
from APP.models.emplacement_repository import EmplacementRepository
from APP.models.piece_statut_repository import PieceStatutRepository
from APP.services.piece_extension_service import PieceExtensionService
from APP.services.machine_service import MachineService
from APP.services.mouvement_service import MouvementService
try:
    from psycopg2 import errors as pg_errors
except Exception:  # pragma: no cover - fallback if psycopg2 not available in some contexts
    pg_errors = None

class PieceService:
    def __init__(self, db):
        self.db = db
        self.repo = PieceRepository(db)
        self.extension_service = PieceExtensionService(db)
        self.machine_service = MachineService(db)
        self.mouvement_service = MouvementService(db)
        # Parent lists for name lookups — loaded lazily on first access
        self._parent_unit_list = None
        self._parent_category_list = None
        self._parent_emplacement_list = None
        self._parent_statut_list = None

    @property
    def parent_unit_list(self):
        if self._parent_unit_list is None:
            self._parent_unit_list = PieceUnitRepository(self.db).get_all_units()
        return self._parent_unit_list

    @property
    def parent_category_list(self):
        if self._parent_category_list is None:
            self._parent_category_list = PieceCategoryRepository(self.db).get_all_categories()
        return self._parent_category_list

    @property
    def parent_emplacement_list(self):
        if self._parent_emplacement_list is None:
            self._parent_emplacement_list = EmplacementRepository(self.db).get_all_emplacements()
        return self._parent_emplacement_list

    @property
    def parent_statut_list(self):
        if self._parent_statut_list is None:
            self._parent_statut_list = PieceStatutRepository(self.db).get_all_statuts()
        return self._parent_statut_list

    def get_all_pieces(self):
        return self.repo.get_all_pieces()

    def get_piece_by_id(self, id_piece):
        return self.repo.get_piece_by_id(id_piece)

    def add_piece(self, piece):
        # Séparer les champs extension
        extension = {
            "unite_id": piece.get("unite_id"),
            "categorie_id": piece.get("categorie_id"),
            "emplacement_id": piece.get("emplacement_id"),
            "statut_id": piece.get("statut_id"),
            "machine_id": piece.get("machine_id")
        }
        # Synchroniser les champs texte attendus dans piece
        # Récupérer les noms des entités sélectionnées
        piece["unite"] = self._get_nom_from_id(extension["unite_id"], self.parent_unit_list, "id", "nom")
        piece["categorie"] = self._get_nom_from_id(extension["categorie_id"], self.parent_category_list, "id", "nom")
        piece["emplacement_stockage"] = self._get_nom_from_id(extension["emplacement_id"], self.parent_emplacement_list, "id", "nom")
        piece["statut"] = self._get_nom_from_id(extension["statut_id"], self.parent_statut_list, "id", "nom")
        # Machine (spécifique)
        machine_nom = None
        if extension["machine_id"]:
            machines = self.machine_service.list_machines()
            for m in machines:
                if m["id_machine"] == extension["machine_id"]:
                    machine_nom = m["nom"]
                    break
        piece["machine"] = machine_nom or ""
        id_piece = self.repo.add_piece(piece)
        self.extension_service.add_or_update_extension(id_piece, extension)
        return id_piece

    def update_piece(self, id_piece, piece):
        extension = {
            "unite_id": piece.get("unite_id"),
            "categorie_id": piece.get("categorie_id"),
            "emplacement_id": piece.get("emplacement_id"),
            "statut_id": piece.get("statut_id"),
            "machine_id": piece.get("machine_id")
        }
        piece["unite"] = self._get_nom_from_id(extension["unite_id"], self.parent_unit_list, "id", "nom")
        piece["categorie"] = self._get_nom_from_id(extension["categorie_id"], self.parent_category_list, "id", "nom")
        piece["emplacement_stockage"] = self._get_nom_from_id(extension["emplacement_id"], self.parent_emplacement_list, "id", "nom")
        piece["statut"] = self._get_nom_from_id(extension["statut_id"], self.parent_statut_list, "id", "nom")
        machine_nom = None
        if extension["machine_id"]:
            machines = self.machine_service.list_machines()
            for m in machines:
                if m["id_machine"] == extension["machine_id"]:
                    machine_nom = m["nom"]
                    break
        piece["machine"] = machine_nom or ""
        self.repo.update_piece(id_piece, piece)
        self.extension_service.add_or_update_extension(id_piece, extension)

    # Pré-contrôle: recense les références empêchant la suppression
    def get_delete_blockers(self, id_piece: int) -> dict:
        counts = {
            "mouvement_stock": 0,
            "reception_lot": 0,
            # "emplacement_stock": 0,  # en cascade, informatif seulement
            # "piece_extension": 0,     # supprimé avant, informatif seulement
        }
        with self.db.conn.cursor() as cur:
            # Mouvement de stock (bloquant)
            cur.execute("SELECT COUNT(*) FROM mouvement_stock WHERE piece_id = %s;", (id_piece,))
            counts["mouvement_stock"] = cur.fetchone()[0]

            # Lots de réception (bloquant)
            cur.execute("SELECT COUNT(*) FROM lot_reception WHERE piece_id = %s;", (id_piece,))
            counts["reception_lot"] = cur.fetchone()[0]

            # Informative only (non bloquant car ON DELETE CASCADE)
            # cur.execute("SELECT COUNT(*) FROM emplacement_stock WHERE piece_id = %s;", (id_piece,))
            # counts["emplacement_stock"] = cur.fetchone()[0]

            # Informative only (devrait être 0 car supprimé par service avant delete)
            # cur.execute("SELECT COUNT(*) FROM piece_extension WHERE id_piece = %s;", (id_piece,))
            # counts["piece_extension"] = cur.fetchone()[0]

        return counts

    def format_blockers_message(self, counts: dict) -> str:
        total = sum(counts.values())
        if total == 0:
            return ""
        parts = []
        if counts.get("mouvement_stock"):
            parts.append(f"- {counts['mouvement_stock']} record(s) in stock movements")
        if counts.get("reception_lot"):
            parts.append(f"- {counts['reception_lot']} record(s) in reception lots")
        details = "\n".join(parts) if parts else ""
        return (
            "Cannot delete this part because it is referenced by other records.\n"
            "Please remove these links first:\n" + details
        )

    def archive_piece(self, id_piece: int):
        """Set piece statut to 'Inactif' safely (archive), with rollback on failure."""
        try:
            self.repo.set_statut(id_piece, "Inactif")
        except Exception as e:
            try:
                self.db.conn.rollback()
            except Exception:
                pass
            raise

    def clear_piece_stocks(self, id_piece: int, utilisateur_id: int = None, commentaire: str = None) -> int:
        """Empty stock of this piece from all emplacements via inventory-out movements.

        Returns the number of movements created.
        """
        try:
            return self.mouvement_service.vider_piece_de_tous_emplacements(id_piece, utilisateur_id, commentaire)
        except Exception:
            # Safety rollback to clear aborted transaction state if any DB error occurred
            try:
                self.db.conn.rollback()
            except Exception:
                pass
            raise

    # Utilitaire pour retrouver le nom d'une entité à partir de son id et d'une liste
    def _get_nom_from_id(self, id_value, entity_list, id_key, nom_key):
        if not id_value or not entity_list:
            return ""
        for entity in entity_list:
            if entity.get(id_key) == id_value:
                return entity.get(nom_key, "")
        return ""

    def delete_piece(self, id_piece):
        try:
            # Pré-contrôle: si des références existent, on arrête et on remonte un message clair
            blockers = self.get_delete_blockers(id_piece)
            if sum(blockers.values()) > 0:
                raise RuntimeError(self.format_blockers_message(blockers))

            self.extension_service.delete_extension(id_piece)
            self.repo.delete_piece(id_piece)
        except Exception as e:
            # Always rollback to clear aborted transaction state
            try:
                self.db.conn.rollback()
            except Exception:
                pass
            # Map FK violations to a user-friendly error
            if pg_errors and isinstance(e, pg_errors.ForeignKeyViolation) or e.__class__.__name__ == 'ForeignKeyViolation':
                raise RuntimeError("Cannot delete this part because it is referenced by other records (e.g., interventions). Remove those links first.") from e
            raise

    # === Méthodes de filtrage (requêtes déplacées depuis piece_table_view.py) ===

    _PIECE_COLUMNS = [
        "id_piece", "reference", "nom", "fournisseur_pref_id", "prix_unitaire",
        "stock_alerte", "stock_actuel", "stock_reserve", "unite", "categorie",
        "emplacement_stockage", "statut"
    ]

    def _rows_to_pieces(self, rows):
        """Convertit des lignes de curseur en liste de dictionnaires."""
        return [dict(zip(self._PIECE_COLUMNS, row)) for row in rows]

    def get_pieces_stock_faible(self):
        """Pièces dont le stock est inférieur ou égal au seuil d'alerte."""
        with self.db.conn.cursor() as cur:
            cur.execute("""
                SELECT p.id_piece, p.reference, p.nom, p.fournisseur_pref_id, p.prix_unitaire,
                       p.stock_alerte, p.stock_actuel, p.stock_reserve,
                       p.unite, p.categorie, p.emplacement_stockage, p.statut
                FROM piece p
                WHERE p.stock_actuel <= p.stock_alerte
                ORDER BY p.stock_actuel ASC;
            """)
            return self._rows_to_pieces(cur.fetchall())

    def get_pieces_by_machine(self):
        """Pièces liées à une machine."""
        with self.db.conn.cursor() as cur:
            cur.execute("""
                SELECT p.id_piece, p.reference, p.nom, p.fournisseur_pref_id, p.prix_unitaire,
                       p.stock_alerte, p.stock_actuel, p.stock_reserve,
                       p.unite, p.categorie, p.emplacement_stockage, p.statut
                FROM piece p
                JOIN piece_extension pe ON p.id_piece = pe.id_piece
                WHERE pe.machine_id IS NOT NULL
                ORDER BY p.nom;
            """)
            return self._rows_to_pieces(cur.fetchall())

    def get_pieces_by_categorie(self):
        """Pièces triées par catégorie."""
        with self.db.conn.cursor() as cur:
            cur.execute("""
                SELECT p.id_piece, p.reference, p.nom, p.fournisseur_pref_id, p.prix_unitaire,
                       p.stock_alerte, p.stock_actuel, p.stock_reserve,
                       p.unite, p.categorie, p.emplacement_stockage, p.statut
                FROM piece p
                JOIN piece_extension pe ON p.id_piece = pe.id_piece
                WHERE pe.categorie_id IS NOT NULL
                ORDER BY p.categorie, p.nom;
            """)
            return self._rows_to_pieces(cur.fetchall())

    def get_pieces_emplacements_sous_utilises(self):
        """Pièces dans des emplacements sous-utilisés (<5 pièces)."""
        with self.db.conn.cursor() as cur:
            cur.execute("""
                SELECT p.id_piece, p.reference, p.nom, p.fournisseur_pref_id, p.prix_unitaire,
                       p.stock_alerte, p.stock_actuel, p.stock_reserve,
                       p.unite, p.categorie, p.emplacement_stockage, p.statut
                FROM piece p
                JOIN piece_extension pe ON p.id_piece = pe.id_piece
                WHERE pe.emplacement_id IN (
                    SELECT e.id
                    FROM emplacement e
                    LEFT JOIN piece_extension pe2 ON pe2.emplacement_id = e.id
                    LEFT JOIN piece p2 ON pe2.id_piece = p2.id_piece
                    GROUP BY e.id
                    HAVING COUNT(p2.id_piece) < 5
                )
                ORDER BY p.emplacement_stockage, p.nom;
            """)
            return self._rows_to_pieces(cur.fetchall())

    def get_pieces_by_statut(self):
        """Pièces triées par statut."""
        with self.db.conn.cursor() as cur:
            cur.execute("""
                SELECT p.id_piece, p.reference, p.nom, p.fournisseur_pref_id, p.prix_unitaire,
                       p.stock_alerte, p.stock_actuel, p.stock_reserve,
                       p.unite, p.categorie, p.emplacement_stockage, p.statut
                FROM piece p
                JOIN piece_extension pe ON p.id_piece = pe.id_piece
                WHERE pe.statut_id IS NOT NULL
                ORDER BY p.statut, p.nom;
            """)
            return self._rows_to_pieces(cur.fetchall())
