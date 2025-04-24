import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.init_db import init_db
from app.models import Base


def make_engine(connect_block=None):
    """Helper to create a dummy engine with a customizable connect context manager."""
    engine = MagicMock()
    # configure connect() context manager
    cm = MagicMock()
    if connect_block:
        # __enter__ returns a connection mock with specified behavior
        cm.__enter__.return_value = connect_block
    else:
        cm.__enter__.return_value = MagicMock()
    engine.connect.return_value = cm
    return engine


def test_init_db_success(monkeypatch, capsys):
    # Setup URL and engine
    monkeypatch.setattr('app.init_db.get_database_url', lambda: 'db_url')
    engine = make_engine()
    monkeypatch.setattr('app.init_db.create_engine', lambda url: engine)
    # Stub out schema creation
    monkeypatch.setattr(Base.metadata, 'create_all', lambda eng: None)

    # Run
    init_db()

    # Check extension call and commit
    conn = engine.connect().__enter__()
    conn.execute.assert_called_with(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
    conn.commit.assert_called_once()
    # Only PostGIS success printed
    out = capsys.readouterr().out
    assert "PostGIS extension initialized successfully" in out
    # Engine disposed
    engine.dispose.assert_called_once()


def test_init_db_extension_error(monkeypatch, caplog, capsys):
    # Simulate SQLAlchemyError during extension
    monkeypatch.setattr('app.init_db.get_database_url', lambda: 'db_url')
    connection = MagicMock()
    connection.execute.side_effect = SQLAlchemyError("ext fail")
    engine = make_engine(connect_block=connection)
    monkeypatch.setattr('app.init_db.create_engine', lambda url: engine)

    caplog.set_level('ERROR')
    init_db()

    # Should log extension error and critical in outer except
    assert any("SQLAlchemy error during PostGIS initialization" in rec.getMessage() for rec in caplog.records)
    # Should print CRITICAL for the outer exception
    out = capsys.readouterr().out
    assert "CRITICAL ERROR" in out
    # Dispose called
    engine.dispose.assert_called_once()


def test_init_db_generic_error(monkeypatch, caplog, capsys):
    # Simulate generic exception in extension stage
    monkeypatch.setattr('app.init_db.get_database_url', lambda: 'db_url')
    connection = MagicMock()
    connection.execute.side_effect = Exception("boom")
    engine = make_engine(connect_block=connection)
    monkeypatch.setattr('app.init_db.create_engine', lambda url: engine)

    caplog.set_level('ERROR')
    init_db()

    # Should capture fatal error
    assert any("Fatal error during database initialization" in rec.getMessage() for rec in caplog.records)
    out = capsys.readouterr().out
    assert "CRITICAL ERROR" in out
    engine.dispose.assert_called_once()
