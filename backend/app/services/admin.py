import json
import re
from datetime import datetime, timezone

from sqlalchemy import Connection

from app.dao.repositories import AdminDao, UserDao
from app.services.catalog import CatalogService
from app.services.errors import ServiceError
from app.services.engagement import EngagementService
from app.services.properties import PropertyService, property_output


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _json_value(value):
    return json.loads(value) if isinstance(value, str) else value


class AdminService:
    allowed_roles = {"buyer", "tenant", "seller", "owner", "agent", "builder", "admin"}

    def __init__(self, connection: Connection):
        self.dao = AdminDao(connection)
        self.users = UserDao(connection)
        self.property_service = PropertyService(connection)
        self.catalog = CatalogService(connection)
        self.engagement = EngagementService(connection)

    def _audit(
        self,
        actor_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        metadata: dict | None = None,
    ) -> None:
        self.dao.insert(
            "admin.audit_insert",
            {
                "actor_id": actor_id,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "metadata_json": metadata or {},
                "created_at": _now(),
            },
        )

    def overview(self) -> dict:
        return {
            "users": self.dao.scalar("admin.users_count"),
            "listings": self.dao.scalar("admin.listings_count"),
            "pending": self.dao.scalar("admin.pending_count"),
            "published": self.dao.scalar("admin.published_count"),
            "reports": self.dao.scalar("reports.open_count"),
            "inquiries": self.dao.scalar("inquiries.count"),
        }

    def properties(self, status: str | None) -> list[dict]:
        rows = self.properties_dao_list(status)
        return [property_output(row) for row in rows]

    def properties_dao_list(self, status: str | None) -> list[dict]:
        return self.properties.dao.property_list("admin.properties_list", {"status": status})

    def moderate(self, property_identifier: str, decision: str, reason: str | None, actor_id: str) -> dict:
        if decision not in {"approve", "reject"}:
            raise ServiceError(422, "Decision must be approve or reject")
        property_row = self.property_service.get(property_identifier)
        status = "published" if decision == "approve" else "rejected"
        self.dao.execute(
            "properties.status_update",
            {
                "id": property_row["id"],
                "status": status,
                "moderation_note": reason,
                "updated_at": _now(),
            },
        )
        self.dao.insert(
            "admin.approval_insert",
            {
                "property_id": property_row["id"],
                "admin_id": actor_id,
                "decision": decision,
                "reason": reason,
                "created_at": _now(),
            },
        )
        self._audit(
            actor_id,
            f"listing.{decision}",
            "property",
            str(property_row["id"]),
            {"reason": reason},
        )
        self.engagement.dao.notify(
            property_row.get("owner_id"),
            "Listing reviewed",
            f"Your listing {property_row['title']} was {status}",
            _now(),
        )
        return {"id": property_row["id"], "status": status}

    def set_roles(self, user_id: str, roles: list[str], actor_id: str) -> dict:
        if not roles or not set(roles) <= self.allowed_roles:
            raise ServiceError(422, "Invalid roles")
        if self.users.by_id(user_id) is None:
            raise ServiceError(404, "User not found")
        self.dao.execute("user_roles.delete_all", {"user_id": user_id})
        for role in set(roles):
            self.dao.insert("user_roles.insert", {"user_id": user_id, "role": role})
        self._audit(
            actor_id,
            "user.roles.updated",
            "user",
            user_id,
            {"roles": roles},
        )
        return {"user_id": user_id, "roles": roles}

    def reports(self) -> list[dict]:
        return self.dao.list("admin.reports_list")

    def update_report(self, report_id: str, status: str, actor_id: str) -> dict:
        if status not in {"open", "reviewing", "resolved", "dismissed"}:
            raise ServiceError(422, "Invalid report status")
        report = self.dao.one("reports.by_id", {"id": report_id})
        if report is None:
            raise ServiceError(404, "Report not found")
        self.dao.execute("reports.update_status", {"id": report_id, "status": status})
        self._audit(
            actor_id,
            "report.status.updated",
            "report",
            report_id,
            {"status": status},
        )
        return {"id": report_id, "status": status}

    def users_list(self) -> list[dict]:
        rows = self.dao.list("admin.users_list")
        roles_by_user: dict[str, list[str]] = {}
        for row in self.dao.list("users.roles_for_all"):
            roles_by_user.setdefault(str(row["user_id"]), []).append(row["role"])
        for row in rows:
            row["roles"] = roles_by_user.get(str(row["id"]), [])
        return rows

    def audit_logs(self) -> list[dict]:
        rows = self.dao.list("admin.audit_logs")
        for row in rows:
            row["metadata"] = _json_value(row["metadata"])
        return rows

    def delete_property(self, identifier: str, actor_id: str) -> dict:
        property_row = self.property_service.get(identifier)
        self.dao.execute(
            "properties.status_update",
            {
                "id": property_row["id"],
                "status": "deleted",
                "moderation_note": property_row.get("moderation_note"),
                "updated_at": _now(),
            },
        )
        self._audit(actor_id, "listing.deleted", "property", str(property_row["id"]))
        return {"ok": True}

    def feature_property(self, identifier: str, featured: bool, actor_id: str) -> dict:
        property_row = self.property_service.get(identifier)
        self.dao.execute(
            "properties.feature_update",
            {
                "id": property_row["id"],
                "featured": featured,
                "updated_at": _now(),
            },
        )
        self._audit(
            actor_id,
            "listing.feature.updated",
            "property",
            str(property_row["id"]),
            {"featured": featured},
        )
        return {"id": property_row["id"], "featured": featured}

    def projects(self, city: str | None = None) -> list[dict]:
        return self.catalog.projects(city)

    def create_project(self, data: dict, actor_id: str) -> dict:
        return self.catalog.create_project(data, actor_id)

    def create_developer(self, data: dict, actor_id: str) -> dict:
        return self.catalog.create_developer(data, actor_id)

    def create_blog_post(self, data: dict, actor_id: str) -> dict:
        return self.catalog.create_blog_post(data, actor_id)

    def create_category(self, data: dict, actor_id: str) -> dict:
        return self.catalog.create_category(data, actor_id)

    def create_location(self, data: dict, actor_id: str) -> dict:
        return self.catalog.create_location(data, actor_id)

    def create_agent(self, data: dict, actor_id: str) -> dict:
        return self.catalog.create_agent(data, actor_id)

    def settings(self) -> list[dict]:
        rows = self.dao.list("admin.settings_list")
        for row in rows:
            row["value"] = _json_value(row["value"])
        return rows

    def update_setting(self, key: str, value: dict, actor_id: str) -> dict:
        if not re.fullmatch(r"[a-z0-9_.-]{2,100}", key):
            raise ServiceError(422, "Invalid setting key")
        parameters = {"key": key, "value": value, "updated_at": _now()}
        if self.dao.one("admin.setting_by_key", {"key": key}) is None:
            self.dao.insert("admin.setting_insert", parameters)
        else:
            self.dao.execute("admin.setting_update", parameters)
        self._audit(
            actor_id,
            "platform_setting.updated",
            "setting",
            key,
            {"keys": list(value.keys())},
        )
        return {"key": key, "value": value}

    def contact_messages(self) -> list[dict]:
        return self.dao.list("admin.contact_messages")

    def newsletter(self, email: str, consent: bool) -> dict:
        return self.engagement.subscribe(email, consent)
