import os
import pytest

@pytest.fixture(autouse=True)
def env_setup(monkeypatch, tmp_path):
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-1234567890abcdef")
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
