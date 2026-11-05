from collections.abc import Mapping
from typing import Any
from uuid import UUID
from uuid import uuid4

from sqlalchemy import Connection

from app.dao.template import NamedParameterJdbcTemplate


class BaseDao:
    def __init__(self, connection: Connection):
        self.jdbc = NamedParameterJdbcTemplate(connection)

    def list(self, statement: str, parameters: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        return self.jdbc.query(statement, parameters)

    def one(self, statement: str, parameters: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
        return self.jdbc.query_one(statement, parameters)

    def scalar(self, statement: str, parameters: Mapping[str, Any] | None = None) -> Any:
        return self.jdbc.scalar(statement, parameters)

    def execute(self, statement: str, parameters: Mapping[str, Any] | None = None) -> int:
        return self.jdbc.update(statement, parameters)

    def insert(self, statement: str, parameters: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
        return self.jdbc.insert(statement, parameters)


class UserDao(BaseDao):
    def by_email(self, email: str) -> dict[str, Any] | None:
        return self.one("users.by_email", {"email": email})

    def by_firebase_uid(self, firebase_uid: str) -> dict[str, Any] | None:
        return self.one("users.by_firebase_uid", {"firebase_uid": firebase_uid})

    def by_id(self, user_id: str) -> dict[str, Any] | None:
        return self.one("users.by_id", {"id": user_id})

    def roles(self, user_id: str) -> list[str]:
        return [row["role"] for row in self.list("users.roles", {"user_id": user_id})]

    def create(self, **values: Any) -> dict[str, Any]:
        self.insert("users.insert", values)
        return self.by_id(values["id"]) or values


class PropertyDao(BaseDao):
    def by_id(self, property_id: str) -> dict[str, Any] | None:
        return self.one("properties.by_id", {"id": property_id})

    def by_identifier(self, identifier: str) -> dict[str, Any] | None:
        row = self.one(
            "properties.by_alias",
            {"slug": identifier, "property_id": identifier},
        )
        if row is None:
            try:
                UUID(identifier)
            except ValueError:
                return None
            row = self.by_id(identifier)
        return row

    def hydrate(self, properties: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for property_row in properties:
            property_row["images"] = [
                row["url"]
                for row in self.list("properties.images", {"property_id": property_row["id"]})
            ]
            property_row["amenities"] = [
                row["name"]
                for row in self.list("properties.amenities", {"property_id": property_row["id"]})
            ]
        return properties

    def hydrate_one(self, property_row: dict[str, Any] | None) -> dict[str, Any] | None:
        if property_row is None:
            return None
        self.hydrate([property_row])
        return property_row

    def property_list(self, statement: str, parameters: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        return self.hydrate(self.list(statement, parameters))

    def create_images(self, property_id: str, images: list[str]) -> None:
        for position, url in enumerate(images):
            self.insert(
                "properties.image_insert",
                {
                    "id": str(uuid4()),
                    "property_id": property_id,
                    "url": url,
                    "alt_text": "Property image",
                    "position": position,
                    "is_cover": position == 0,
                },
            )

    def create_amenities(self, property_id: str, amenities: list[str]) -> None:
        for name in set(amenities):
            amenity = self.one("amenities.by_name", {"name": name})
            if amenity is None:
                self.insert("amenities.insert", {"name": name})
                amenity = self.one("amenities.by_name", {"name": name})
            if amenity is None:
                raise RuntimeError(f"Amenity '{name}' was not persisted")
            self.insert(
                "property_amenities.insert",
                {"property_id": property_id, "amenity_id": amenity["id"]},
            )


class EngagementDao(BaseDao):
    def notify(self, user_id: str | None, title: str, body: str, created_at: Any) -> None:
        if user_id:
            self.insert(
                "notifications.insert",
                {
                    "id": str(uuid4()),
                    "user_id": user_id,
                    "title": title,
                    "body": body,
                    "created_at": created_at,
                },
            )


class CatalogDao(BaseDao):
    pass


class AdminDao(BaseDao):
    pass
