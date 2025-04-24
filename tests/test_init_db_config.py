import os
import io
import logging
import pytest
from app import init_db


def test_get_database_url_env_var(monkeypatch, caplog):
    """When DATABASE_URL is in env, it returns that URL and logs info"""
    monkeypatch.setenv('DATABASE_URL', 'env://db')
    caplog.set_level(logging.INFO)

    url = init_db.get_database_url()

    assert url == 'env://db'
    assert 'Loaded DATABASE_URL from environment variable.' in caplog.text


def test_get_database_url_from_toml(monkeypatch, caplog):
    """When env var missing, it loads from .streamlit/secrets.toml"""
    # Ensure env var is not set
    monkeypatch.delenv('DATABASE_URL', raising=False)
    # Dummy open to provide a file-like
    def dummy_open(path, mode='rb'):
        return io.BytesIO(b'')
    monkeypatch.setattr('builtins.open', dummy_open)
    # Dummy tomli.load to return desired dict
    monkeypatch.setattr(init_db.tomli, 'load', lambda f: {'DATABASE_URL': 'toml://db'})
    caplog.set_level(logging.INFO)

    url = init_db.get_database_url()

    assert url == 'toml://db'
    assert 'Loaded DATABASE_URL from .streamlit/secrets.toml.' in caplog.text


def test_get_database_url_file_not_found(monkeypatch, caplog):
    """When toml file missing, it logs error and raises RuntimeError"""
    monkeypatch.delenv('DATABASE_URL', raising=False)
    # open raises FileNotFoundError
    monkeypatch.setattr('builtins.open', lambda *args, **kwargs: (_ for _ in ()).throw(FileNotFoundError()))
    caplog.set_level(logging.ERROR)

    with pytest.raises(RuntimeError) as exc:
        init_db.get_database_url()
    assert 'secrets.toml not found' in caplog.text
    assert 'DATABASE_URL not found' in str(exc.value)


def test_get_database_url_malformed_toml(monkeypatch, caplog):
    """When toml parsing fails, it logs error and raises RuntimeError"""
    monkeypatch.delenv('DATABASE_URL', raising=False)
    # open returns dummy
    monkeypatch.setattr('builtins.open', lambda path, mode='rb': io.BytesIO(b''))
    # tomli.load raises
    monkeypatch.setattr(init_db.tomli, 'load', lambda f: (_ for _ in ()).throw(ValueError('bad toml')))
    caplog.set_level(logging.ERROR)

    with pytest.raises(RuntimeError) as exc:
        init_db.get_database_url()
    assert 'Error reading secrets.toml' in caplog.text
    assert 'DATABASE_URL not found' in str(exc.value)
