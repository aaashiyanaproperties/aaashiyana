from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import DATE, JSON, Uuid, Connection, DateTime, bindparam, text

from app.dao.sql import SqlProperties, sql_properties


class NamedParameterJdbcTemplate:
    def __init__(self, connection: Connection, statements: SqlProperties = sql_properties):
        self.connection = connection
        self.statements = statements

    def _parameters(self, parameters: Mapping[str, Any] | None) -> dict[str, Any]:
        return dict(parameters or {})

    def _statement(self, key: str):
        statement = text(self.statements.get(key))
        json_parameters = {
            "filters",
            "locations_served",
            "metadata_json",
            "preferences",
            "value",
        }
        uuid_parameters = {
            "id",
            "user_id",
            "owner_id",
            "sender_id",
            "recipient_id",
            "reporter_id",
            "actor_id",
            "admin_id",
            "developer_id",
            "property_id",
        }
        datetime_parameters = {
            "created_at",
            "updated_at",
            "read_at",
            "scheduled_at",
            "consent_at",
            "posted_after",
        }
        names = set(statement._bindparams)
        typed_parameters = []
        for name in names:
            if name in json_parameters:
                typed_parameters.append(bindparam(name, type_=JSON))
            elif name in uuid_parameters and not (
                name == "property_id"
                and key in {"properties.by_alias", "properties.insert"}
            ):
                typed_parameters.append(bindparam(name, type_=Uuid(as_uuid=False)))
            elif name in datetime_parameters:
                typed_parameters.append(bindparam(name, type_=DateTime()))
            elif name == "possession_date":
                typed_parameters.append(bindparam(name, type_=DATE))
        return statement.bindparams(*typed_parameters) if typed_parameters else statement

    @staticmethod
    def _row(row) -> dict[str, Any]:
        return {
            key: str(value) if isinstance(value, UUID) else value
            for key, value in row.items()
        }

    def query(self, key: str, parameters: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        result = self.connection.execute(
            self._statement(key), self._parameters(parameters)
        )
        return [self._row(row) for row in result.mappings().all()]

    def query_one(self, key: str, parameters: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
        result = self.connection.execute(
            self._statement(key), self._parameters(parameters)
        )
        row = result.mappings().first()
        return self._row(row) if row is not None else None

    def scalar(self, key: str, parameters: Mapping[str, Any] | None = None) -> Any:
        return self.connection.execute(
            self._statement(key), self._parameters(parameters)
        ).scalar_one_or_none()

    def update(self, key: str, parameters: Mapping[str, Any] | None = None) -> int:
        result = self.connection.execute(
            self._statement(key), self._parameters(parameters)
        )
        return result.rowcount

    def insert(self, key: str, parameters: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
        result = self.connection.execute(
            self._statement(key), self._parameters(parameters)
        )
        if not result.returns_rows:
            return None
        row = result.mappings().first()
        return self._row(row) if row is not None else None
