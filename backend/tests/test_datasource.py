from types import SimpleNamespace

from sqlalchemy.engine import URL

import app.db.datasource as datasource_module
from app.db.datasource import DataSource


def test_postgres_url_uses_psycopg_without_prepared_statements(monkeypatch):
    captured = {}

    def fake_create_engine(url, **options):
        captured["url"] = url
        captured["options"] = options
        return SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))

    monkeypatch.setattr(
        datasource_module.settings,
        "database_url",
        "postgresql://postgres:secret@localhost:5432/aashiyana",
    )
    monkeypatch.setattr(datasource_module, "create_engine", fake_create_engine)

    DataSource()

    assert isinstance(captured["url"], URL)
    assert captured["url"].drivername == "postgresql+psycopg"
    assert captured["options"]["connect_args"] == {"prepare_threshold": None}
