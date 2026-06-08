from unittest.mock import patch, MagicMock
from src.database import init_db, get_session

def test_init_db_success():
    with patch("src.database.Base.metadata.create_all") as mock_create_all, \
         patch("src.database.logger.info") as mock_log_info:
        init_db()
        mock_create_all.assert_called_once()
        mock_log_info.assert_called_with("✅ PostgreSQL tables created.")

def test_init_db_failure():
    with patch("src.database.Base.metadata.create_all", side_effect=Exception("Connection refused")) as mock_create_all, \
         patch("src.database.logger.error") as mock_log_error:
        init_db()
        mock_create_all.assert_called_once()
        mock_log_error.assert_called_with("DB init failed: Connection refused")

def test_get_session():
    with patch("src.database.SessionLocal") as mock_session_local:
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        session = get_session()
        assert session == mock_session
        mock_session_local.assert_called_once()
