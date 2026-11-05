import re
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import Connection

from app.dao.repositories import PropertyDao
from app.services.errors import ServiceError


def slugify(value: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", value.lower())).strip("-")


def property_output(row: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "id",
        "property_id",
        "slug",
        "title",
        "description",
        "transaction_type",
        "property_type",
        "status",
        "city",
        "state",
        "locality",
        "address",
        "pincode",
        "price",
        "maintenance",
        "deposit",
        "bedrooms",
        "bathrooms",
        "balconies",
        "carpet_area",
        "builtup_area",
        "furnishing",
        "parking",
        "floor_number",
        "total_floors",
        "facing",
        "age_years",
        "latitude",
        "longitude",
        "possession_status",
        "rera_number",
        "rera_verified",
        "featured",
        "demo",
        "images",
        "amenities",
        "created_at",
    )
    result = {field: row.get(field) for field in fields}
    for field in ("price", "maintenance", "deposit"):
        if result.get(field) is not None:
            result[field] = float(result[field])
    return result


class PropertyService:
    def __init__(self, connection: Connection):
        self.dao = PropertyDao(connection)

    def get(self, identifier: str) -> dict[str, Any]:
        property_row = self.dao.hydrate_one(self.dao.by_identifier(identifier))
        if property_row is None:
            raise ServiceError(404, "Property not found")
        return property_row

    def get_published(self, identifier: str) -> dict[str, Any]:
        property_row = self.get(identifier)
        if property_row["status"] != "published":
            raise ServiceError(404, "Property not found")
        return property_row

    def search(
        self,
        *,
        q: str | None,
        city: str | None,
        locality: str | None,
        transaction_type: str | None,
        property_type: str | None,
        min_price: float | None,
        max_price: float | None,
        bedrooms: int | None,
        bathrooms: int | None,
        furnishing: str | None,
        possession_status: str | None,
        pincode: str | None,
        verified: bool | None,
        featured: bool | None,
        parking: bool | None,
        amenity: str | None,
        min_area: float | None,
        max_area: float | None,
        posted_within_days: int | None,
        sort: str,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        search_term = f"%{q.strip().lower()}%" if q and q.strip() else None
        posted_after = (
            datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=posted_within_days)
            if posted_within_days
            else None
        )
        parameters = {
            "city": city,
            "locality": locality,
            "transaction_type": transaction_type,
            "property_type": property_type,
            "furnishing": furnishing,
            "possession_status": possession_status,
            "pincode": pincode,
            "min_price": min_price,
            "max_price": max_price,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "verified": verified,
            "featured": featured,
            "parking": bool(parking),
            "min_area": min_area,
            "max_area": max_area,
            "posted_after": posted_after,
            "search_term": search_term,
            "amenity": f"%{amenity.lower()}%" if amenity else None,
        }
        total = self.dao.scalar("properties.search_count", parameters) or 0
        rows = self.dao.property_list(
            "properties.search",
            {
                **parameters,
                "sort": sort,
                "limit": page_size,
                "offset": (page - 1) * page_size,
            },
        )
        return {
            "items": [property_output(row) for row in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
        }

    @staticmethod
    def _values(data: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        defaults = {
            "address": None,
            "pincode": None,
            "latitude": None,
            "longitude": None,
            "maintenance": None,
            "deposit": None,
            "negotiable": False,
            "bedrooms": 0,
            "bathrooms": 0,
            "balconies": 0,
            "carpet_area": None,
            "builtup_area": None,
            "furnishing": "Unfurnished",
            "floor_number": None,
            "total_floors": None,
            "facing": None,
            "parking": 0,
            "age_years": None,
            "possession_status": "Ready to move",
            "rera_number": None,
        }
        return {**defaults, **data, "created_at": now, "updated_at": now}

    def create(self, data: dict[str, Any], user_id: str) -> dict[str, Any]:
        if data["transaction_type"] not in {"buy", "rent", "lease"}:
            raise ServiceError(422, "Invalid transaction type")
        if data.get("status", "draft") not in {"draft", "pending"}:
            raise ServiceError(422, "New listings must be draft or pending")
        property_id = str(uuid4())
        values = self._values(
            {
                **data,
                "id": property_id,
                "owner_id": user_id,
                "property_id": "AA-" + uuid4().hex[:8].upper(),
                "slug": slugify(f"{data['title']}-{data['city']}-{uuid4().hex[:6]}"),
                "status": data.get("status", "draft"),
                "rera_verified": False,
                "featured": False,
                "demo": False,
            }
        )
        values.pop("amenities", None)
        values.pop("images", None)
        self.dao.insert("properties.insert", values)
        self.dao.create_images(property_id, data.get("images", []))
        self.dao.create_amenities(property_id, data.get("amenities", []))
        return property_output(self.get(property_id))

    def update(self, identifier: str, data: dict[str, Any], user: Any) -> dict[str, Any]:
        property_row = self.get(identifier)
        if property_row["owner_id"] != user.id and "admin" not in user.roles:
            raise ServiceError(403, "You cannot edit this listing")
        if data["transaction_type"] not in {"buy", "rent", "lease"}:
            raise ServiceError(422, "Invalid transaction type")
        values = self._values(data)
        values["id"] = property_row["id"]
        values.pop("amenities", None)
        values.pop("images", None)
        self.dao.execute("properties.update", values)
        self.dao.execute("properties.images_delete", {"property_id": property_row["id"]})
        self.dao.execute("properties.amenities_delete", {"property_id": property_row["id"]})
        self.dao.create_images(property_row["id"], data.get("images", []))
        self.dao.create_amenities(property_row["id"], data.get("amenities", []))
        return property_output(self.get(property_row["id"]))

    def delete(self, identifier: str, user: Any) -> dict[str, bool]:
        property_row = self.get(identifier)
        if property_row["owner_id"] != user.id and "admin" not in user.roles:
            raise ServiceError(403, "You cannot delete this listing")
        self.dao.execute(
            "properties.status_update",
            {
                "id": property_row["id"],
                "status": "deleted",
                "moderation_note": property_row.get("moderation_note"),
                "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
            },
        )
        return {"ok": True}

    def my_properties(self, user_id: str) -> list[dict[str, Any]]:
        return [
            property_output(row)
            for row in self.dao.property_list("properties.by_owner", {"owner_id": user_id})
        ]

    def favourites(self, user_id: str) -> list[dict[str, Any]]:
        return [
            property_output(row)
            for row in self.dao.property_list("favourites.properties", {"user_id": user_id})
        ]

    def add_favourite(self, identifier: str, user_id: str) -> dict[str, bool]:
        property_row = self.get(identifier)
        params = {"user_id": user_id, "property_id": property_row["id"]}
        if self.dao.one("favourites.by_user_property", params) is None:
            self.dao.insert(
                "favourites.insert",
                {**params, "created_at": datetime.now(timezone.utc).replace(tzinfo=None)},
            )
        return {"saved": True}

    def remove_favourite(self, identifier: str, user_id: str) -> dict[str, bool]:
        property_row = self.get(identifier)
        self.dao.execute(
            "favourites.delete",
            {"user_id": user_id, "property_id": property_row["id"]},
        )
        return {"saved": False}

    def create_draft(self, data: dict[str, Any], user_id: str) -> dict[str, Any]:
        property_id = str(uuid4())
        amenities = data.pop("amenities", [])
        values = self._values(
            {
                **data,
                "id": property_id,
                "owner_id": user_id,
                "property_id": "DRAFT-" + uuid4().hex[:8].upper(),
                "slug": slugify(f"{data.get('title') or 'draft'}-{uuid4().hex[:8]}"),
                "status": "draft",
                "rera_verified": False,
                "featured": False,
                "demo": False,
            }
        )
        self.dao.insert("properties.insert", values)
        self.dao.create_amenities(property_id, amenities)
        property_row = self.dao.by_id(property_id)
        assert property_row is not None
        return {key: property_row[key] for key in ("id", "property_id", "slug", "status")}
