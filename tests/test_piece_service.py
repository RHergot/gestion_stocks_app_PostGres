"""Tests pour PieceService — validation et logique métier."""
import pytest
from unittest.mock import MagicMock, patch


class TestPieceServiceValidation:
    """Tests de validation des entrées dans PieceService.add_piece()."""

    @pytest.fixture
    def service(self, mock_db):
        from APP.services.piece_service import PieceService
        # Mock all repos to avoid DB calls
        with patch('APP.services.piece_service.PieceUnitRepository'), \
             patch('APP.services.piece_service.PieceCategoryRepository'), \
             patch('APP.services.piece_service.EmplacementRepository'), \
             patch('APP.services.piece_service.PieceStatutRepository'):
            svc = PieceService(mock_db)
        return svc

    def test_add_piece_missing_required_fields(self, service):
        """Champs obligatoires manquants → ValueError."""
        with pytest.raises(ValueError, match="Champ obligatoire manquant"):
            service.add_piece({})

        with pytest.raises(ValueError, match="Champ obligatoire manquant : reference"):
            service.add_piece({"nom": "Test", "unite": "pcs"})

        with pytest.raises(ValueError, match="Champ obligatoire manquant : nom"):
            service.add_piece({"reference": "REF001", "unite": "pcs"})

    def test_add_piece_invalid_numeric_fields(self, service):
        """Champs numériques invalides → ValueError."""
        with pytest.raises(ValueError, match="Valeur invalide pour prix_unitaire"):
            service.add_piece({
                "reference": "REF001", "nom": "Test", "unite": "pcs",
                "prix_unitaire": "pas_un_nombre"
            })

    def test_add_piece_valid_minimal(self, service, mock_db):
        """Pièce valide minimale — ne doit pas lever d'exception de validation."""
        mock_db.conn.cursor.return_value.__enter__.return_value.fetchone.return_value = {"id_piece": 1}
        mock_db.conn.cursor.return_value.__enter__.return_value.fetchall.return_value = []

        # Should not raise validation error (may raise DB error, that's OK)
        try:
            service.add_piece({
                "reference": "REF001", "nom": "Test Piece", "unite": "pcs",
                "prix_unitaire": 10.5, "stock_alerte": 5
            })
        except ValueError as e:
            pytest.fail(f"Validation failed unexpectedly: {e}")
        except Exception:
            pass  # DB errors are expected with mocks


class TestPieceServiceDeleteBlockers:
    """Tests de get_delete_blockers()."""

    @pytest.fixture
    def service(self, mock_db):
        from APP.services.piece_service import PieceService
        with patch('APP.services.piece_service.PieceUnitRepository'), \
             patch('APP.services.piece_service.PieceCategoryRepository'), \
             patch('APP.services.piece_service.EmplacementRepository'), \
             patch('APP.services.piece_service.PieceStatutRepository'):
            svc = PieceService(mock_db)
        return svc

    def test_get_delete_blockers_no_refs(self, service, mock_cur):
        """Aucune référence → tous les compteurs à 0."""
        mock_cur.fetchone.side_effect = [[0], [0]]
        blockers = service.get_delete_blockers(1)
        assert blockers["mouvement_stock"] == 0
        assert blockers["reception_lot"] == 0
        assert sum(blockers.values()) == 0

    def test_get_delete_blockers_has_refs(self, service, mock_cur):
        """Références existantes → compteurs non nuls."""
        mock_cur.fetchone.side_effect = [[5], [3]]
        blockers = service.get_delete_blockers(1)
        assert blockers["mouvement_stock"] == 5
        assert blockers["reception_lot"] == 3

    def test_format_blockers_message(self, service):
        """Message de blocage formaté correctement."""
        msg = service.format_blockers_message({"mouvement_stock": 2, "reception_lot": 1})
        assert "2 record(s) in stock movements" in msg
        assert "1 record(s) in reception lots" in msg

    def test_format_blockers_message_empty(self, service):
        """Pas de blocage → message vide."""
        assert service.format_blockers_message({"mouvement_stock": 0, "reception_lot": 0}) == ""
