from collections.abc import Iterator

from sqlalchemy import Connection, create_engine, event

from app.core.config import settings


class DataSource:
    def __init__(self):
        options = {"pool_pre_ping": True, "future": True}
        if not settings.database_url.startswith("sqlite"):
            options.update(
                pool_size=settings.db_pool_size,
                max_overflow=settings.db_max_overflow,
                pool_recycle=settings.db_pool_recycle_seconds,
            )
        self.engine = create_engine(settings.database_url, **options)
        if self.engine.dialect.name == "sqlite":
            event.listen(self.engine, "connect", self._enable_sqlite_foreign_keys)

    @staticmethod
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    def get_connection(self) -> Iterator[Connection]:
        with self.engine.begin() as connection:
            yield connection

    def dispose(self) -> None:
        self.engine.dispose()


data_source = DataSource()
