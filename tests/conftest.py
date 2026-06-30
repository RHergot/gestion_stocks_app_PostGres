"""Fixtures pytest pour le projet gestion_stocks_app.

Les imports psycopg2 et PySide6 sont mockés automatiquement car
ces librairies ne sont pas installées dans l'environnement de test CI.
"""
import sys
import os
from unittest.mock import MagicMock

# Mock psycopg2 and PySide6 before any app module is imported
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()
sys.modules['PySide6'] = MagicMock()
sys.modules['PySide6.QtCore'] = MagicMock()
sys.modules['PySide6.QtWidgets'] = MagicMock()
sys.modules['PySide6.QtGui'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


@pytest.fixture
def mock_db():
    """Retourne un objet Database mocké avec conn et cursor."""
    db = MagicMock()
    cursor = MagicMock()
    db.conn.cursor.return_value.__enter__.return_value = cursor
    db.execute.return_value = []
    return db


@pytest.fixture
def mock_cur(mock_db):
    """Retourne le curseur mocké directement."""
    return mock_db.conn.cursor.return_value.__enter__.return_value
