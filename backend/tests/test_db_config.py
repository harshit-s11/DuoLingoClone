from sqlalchemy import text

from app.config import settings
from app.database import engine, ensure_data_directory


def test_data_directory_created():
    data_path = ensure_data_directory()
    assert data_path.exists()
    assert data_path.is_dir()


def test_sqlite_foreign_keys_pragma_enabled():
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA foreign_keys;")).scalar()
        # In SQLite, PRAGMA foreign_keys returns 1 when enabled
        assert result == 1, f"Expected PRAGMA foreign_keys to be 1, got {result}"


def test_db_path_matches_locked_decision():
    assert "duolingo_clone.db" in settings.database_url
    assert "data" in settings.database_url
