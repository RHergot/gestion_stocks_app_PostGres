"""Tests pour les repositories et l'i18n."""
import pytest
from unittest.mock import MagicMock


class TestCommandeRepositoryWhitelist:
    """Tests de la whitelist de colonnes dans CommandeRepository."""

    @pytest.fixture
    def repo(self, mock_db):
        from APP.models.commande_repository import CommandeRepository
        return CommandeRepository(mock_db)

    def test_allowed_columns_contains_expected(self, repo):
        """Les colonnes de base sont dans la whitelist."""
        assert "numero_commande" in repo.ALLOWED_COLUMNS
        assert "fournisseur_id" in repo.ALLOWED_COLUMNS
        assert "statut" in repo.ALLOWED_COLUMNS
        assert "total_ht" in repo.ALLOWED_COLUMNS
        assert "updated_at" in repo.ALLOWED_COLUMNS

    def test_allowed_columns_rejects_unknown(self, repo):
        """Une colonne inconnue n'est pas dans la whitelist."""
        assert "DROP TABLE" not in repo.ALLOWED_COLUMNS
        assert "1=1" not in repo.ALLOWED_COLUMNS

    def test_get_default_user_id_returns_none_when_no_admin(self, repo, mock_cur):
        """Pas d'admin → retourne None."""
        mock_cur.fetchone.return_value = None
        result = repo.get_default_user_id()
        assert result is None

    def test_get_default_user_id_finds_admin(self, repo, mock_cur):
        """Admin existe → retourne son ID."""
        mock_cur.fetchone.return_value = [42]
        result = repo.get_default_user_id()
        assert result == 42


class TestI18n:
    """Tests du module i18n."""

    def test_language_enum(self):
        from APP.utils.i18n import Language
        assert Language.from_env("fr") == Language.FRENCH
        assert Language.from_env("FR_fr") == Language.FRENCH
        assert Language.from_env("en") == Language.ENGLISH
        assert Language.from_env("de") == Language.ENGLISH  # fallback
        assert Language.from_env(None) == Language.ENGLISH

    def test_translate_status(self):
        from APP.utils.i18n import translate_status, Language
        assert translate_status("Créé", Language.FRENCH) == "Créé"
        assert translate_status("Créé", Language.ENGLISH) == "Created"
        assert translate_status("Annulé", Language.ENGLISH) == "Cancelled"

    def test_reverse_translate_status(self):
        from APP.utils.i18n import reverse_translate_status, Language
        assert reverse_translate_status("Created", Language.ENGLISH) == "Créé"
        assert reverse_translate_status("Cancelled", Language.ENGLISH) == "Annulé"
