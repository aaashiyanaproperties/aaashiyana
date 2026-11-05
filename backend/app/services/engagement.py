import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Connection

from app.dao.repositories import EngagementDao, UserDao
from app.services.errors import ServiceError
from app.services.properties import PropertyService


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class EngagementService:
    def __init__(self, connection: Connection):
        self.dao = EngagementDao(connection)
        self.users = UserDao(connection)
        self.properties = PropertyService(connection)

    def create_inquiry(self, identifier: str, data: dict, user) -> dict:
        property_row = self.properties.get_published(identifier)
        if not data["consent"]:
            raise ServiceError(422, "Consent is required to submit this enquiry")
        now = _now()
        inquiry_id = str(uuid4())
        self.dao.insert(
            "inquiries.insert",
            {
                "id": inquiry_id,
                "property_id": property_row["id"],
                "sender_id": user.id if user else None,
                "recipient_id": property_row.get("owner_id"),
                "name": data["name"],
                "email": str(data["email"]),
                "phone": data["phone"],
                "message": data["message"],
                "consent_at": now,
                "created_at": now,
            },
        )
        self.dao.notify(
            property_row.get("owner_id"),
            "New property enquiry",
            f"{data['name']} enquired about {property_row['title']}",
            now,
        )
        owner = (
            self.users.by_id(property_row["owner_id"])
            if property_row.get("owner_id")
            else None
        )
        return {
            "id": inquiry_id,
            "status": "new",
            "message": "Your enquiry has been received",
            "owner_email": owner.get("email") if owner else None,
            "property_title": property_row["title"],
            "name": data["name"],
            "phone": data["phone"],
        }

    def create_visit(self, identifier: str, data: dict, user) -> dict:
        property_row = self.properties.get(identifier)
        if not data["consent"]:
            raise ServiceError(422, "Consent is required to request a visit")
        scheduled_at = data["scheduled_at"]
        if scheduled_at.replace(tzinfo=None) < _now():
            raise ServiceError(422, "Visit must be in the future")
        visit_id = str(uuid4())
        now = _now()
        self.dao.insert(
            "visits.insert",
            {
                "id": visit_id,
                "property_id": property_row["id"],
                "user_id": user.id if user else None,
                "name": data["name"],
                "phone": data["phone"],
                "scheduled_at": scheduled_at.replace(tzinfo=None),
                "consent_at": now,
                "created_at": now,
            },
        )
        self.dao.notify(
            property_row.get("owner_id"),
            "Property visit requested",
            f"Visit requested for {property_row['title']}",
            now,
        )
        owner = (
            self.users.by_id(property_row["owner_id"])
            if property_row.get("owner_id")
            else None
        )
        return {
            "id": visit_id,
            "status": "requested",
            "owner_email": owner.get("email") if owner else None,
            "property_title": property_row["title"],
            "name": data["name"],
            "scheduled_at": scheduled_at,
        }

    def report(self, identifier: str, data: dict, user) -> dict:
        property_row = self.properties.get(identifier)
        report_id = str(uuid4())
        self.dao.insert(
            "reports.insert",
            {
                "id": report_id,
                "property_id": property_row["id"],
                "reporter_id": user.id if user else None,
                "reason": data["reason"],
                "details": data.get("details"),
                "created_at": _now(),
            },
        )
        return {"id": report_id, "status": "open"}

    def my_inquiries(self, user_id: str) -> list[dict]:
        rows = self.dao.list("inquiries.by_user", {"user_id": user_id})
        return [
            {
                "id": row["id"],
                "property_id": row["property_id"],
                "property_title": row["property_title"],
                "name": row["name"],
                "email": row["email"],
                "phone": row["phone"],
                "message": row["message"],
                "status": row["status"],
                "created_at": row["created_at"],
                "is_received": row["recipient_id"] == user_id,
            }
            for row in rows
        ]

    def update_inquiry(self, inquiry_id: str, status: str, user) -> dict:
        row = self.dao.one("inquiries.by_id", {"id": inquiry_id})
        if row is None:
            raise ServiceError(404, "Inquiry not found")
        if row["recipient_id"] != user.id and "admin" not in user.roles:
            raise ServiceError(403, "Not allowed")
        if status not in {
            "new",
            "contacted",
            "follow_up",
            "visit_scheduled",
            "converted",
            "closed",
        }:
            raise ServiceError(422, "Invalid inquiry status")
        self.dao.execute(
            "inquiries.update_status", {"id": inquiry_id, "status": status}
        )
        return {"id": inquiry_id, "status": status}

    def my_visits(self, user_id: str) -> list[dict]:
        return [
            {
                "id": row["id"],
                "property_id": row["property_id"],
                "property_title": row["property_title"],
                "name": row["name"],
                "phone": row["phone"],
                "scheduled_at": row["scheduled_at"],
                "status": row["status"],
                "is_received": row["owner_id"] == user_id,
            }
            for row in self.dao.list("visits.by_user", {"user_id": user_id})
        ]

    def save_search(self, user_id: str, name: str, filters: dict) -> dict:
        search_id = str(uuid4())
        self.dao.insert(
            "saved_searches.insert",
            {
                "id": search_id,
                "user_id": user_id,
                "name": name,
                "filters": filters,
                "created_at": _now(),
            },
        )
        return {"id": search_id, "name": name, "filters": filters}

    def list_searches(self, user_id: str) -> list[dict]:
        rows = self.dao.list("saved_searches.by_user", {"user_id": user_id})
        for row in rows:
            if isinstance(row["filters"], str):
                row["filters"] = json.loads(row["filters"])
        return rows

    def notifications(self, user_id: str) -> list[dict]:
        return [
            {
                "id": row["id"],
                "title": row["title"],
                "body": row["body"],
                "read": row["read_at"] is not None,
                "created_at": row["created_at"],
            }
            for row in self.dao.list("notifications.by_user", {"user_id": user_id})
        ]

    def mark_notification_read(self, notification_id: str, user_id: str) -> dict:
        changed = self.dao.execute(
            "notifications.mark_read",
            {
                "id": notification_id,
                "user_id": user_id,
                "read_at": _now(),
            },
        )
        if not changed:
            raise ServiceError(404, "Notification not found")
        return {"id": notification_id, "read": True}

    def update_visit(self, visit_id: str, status: str, user) -> dict:
        visit = self.dao.one("visits.by_id", {"id": visit_id})
        if visit is None:
            raise ServiceError(404, "Visit request not found")
        property_row = self.dao.one(
            "properties.owner_property", {"id": visit["property_id"]}
        )
        if (
            property_row is None
            or (
                property_row["owner_id"] != user.id
                and visit["user_id"] != user.id
                and "admin" not in user.roles
            )
        ):
            raise ServiceError(403, "Not allowed")
        if status not in {
            "requested",
            "confirmed",
            "rescheduled",
            "completed",
            "cancelled",
        }:
            raise ServiceError(422, "Invalid visit status")
        self.dao.execute("visits.update_status", {"id": visit_id, "status": status})
        return {"id": visit_id, "status": status}

    def contact_message(self, data: dict) -> dict:
        if not data["consent"]:
            raise ServiceError(422, "Consent is required to send this message")
        message_id = str(uuid4())
        now = _now()
        self.dao.insert(
            "contact_messages.insert",
            {
                "id": message_id,
                "name": data["name"],
                "email": str(data["email"]),
                "topic": data["topic"],
                "message": data["message"],
                "consent_at": now,
                "created_at": now,
            },
        )
        return {
            "id": message_id,
            "status": "new",
            "message": "Your message has been received.",
            "email": str(data["email"]),
            "name": data["name"],
            "topic": data["topic"],
            "body": data["message"],
        }

    def subscribe(self, email: str, consent: bool) -> dict:
        if not consent:
            raise ServiceError(422, "Consent is required to subscribe")
        email = email.lower()
        params = {"email": email}
        if self.dao.one("newsletter.by_email", params):
            self.dao.execute("newsletter.activate", {**params, "consent_at": _now()})
        else:
            self.dao.insert(
                "newsletter.insert", {**params, "consent_at": _now()}
            )
        return {
            "subscribed": True,
            "message": "Your subscription preference has been saved.",
        }
