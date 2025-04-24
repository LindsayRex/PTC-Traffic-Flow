import logging
import pytest
from unittest.mock import MagicMock
from sqlalchemy.exc import SQLAlchemyError
from app.init_db import init_db, get_database_url
from app.models import Base


def make_engine():
    """Helper: engine whose connect yields a no-op connection"""
    engine = MagicMock()
    conn_cm = MagicMock()
    conn = MagicMock()
    conn.execute = MagicMock()
    conn.commit = MagicMock()
    conn_cm.__enter__.return_value = conn
    engine.connect.return_value = conn_cm
    return engine


def test_schema_creation_success(monkeypatch, capsys):
    # Setup
    monkeypatch.setattr('app.init_db.get_database_url', lambda: 'db_url')
    engine = make_engine()
    monkeypatch.setattr('app.init_db.create_engine', lambda url: engine)
    Base.metadata.create_all = MagicMock()

    # Run
    init_db()

    # Assert create_all called and success message printed
    Base.metadata.create_all.assert_called_once_with(engine)
    out = capsys.readouterr().out
    assert "New tables created successfully" in out
    # Dispose should be called in finally
    engine.dispose.assert_called_once()


def test_schema_creation_error(monkeypatch, caplog, capsys):
    # Setup
    monkeypatch.setattr('app.init_db.get_database_url', lambda: 'db_url')
    engine = make_engine()
    monkeypatch.setattr('app.init_db.create_engine', lambda url: engine)
    # Simulate error in create_all
    def broken_create_all(engine_arg):
        raise SQLAlchemyError("schema fail")
    monkeypatch.setattr(Base.metadata, 'create_all', broken_create_all)

    caplog.set_level(logging.ERROR)

    # Run
    init_db()

    # Assert critical error printed and logged
    out = capsys.readouterr().out
    assert "CRITICAL ERROR" in out
    assert any("SQLAlchemy error during database operations" in rec.getMessage() or "Fatal error during database initialization" in rec.getMessage() for rec in caplog.records)
    engine.dispose.assert_called_once()


def test_engine_dispose_always(monkeypatch):
    # Setup to throw before any DDL
    monkeypatch.setattr('app.init_db.get_database_url', lambda: 'db_url')
    # Engine connect throws before extension
    engine = MagicMock()
    engine.connect.side_effect = Exception("boom")
    monkeypatch.setattr('app.init_db.create_engine', lambda url: engine)

    # Run
    init_db()

    # Dispose must still be called
    engine.dispose.assert_called_once()