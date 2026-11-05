import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Connection

from app.dao.repositories import CatalogDao, UserDao
from app.services.errors import ServiceError
from app.services.properties import slugify


def _json_value(value):
    return json.loads(value) if isinstance(value, str) else value


class CatalogService:
    def __init__(self, connection: Connection):
        self.dao = CatalogDao(connection)
        self.users = UserDao(connection)

    def _audit(self, actor_id: str, action: str, entity_type: str, entity_id: str) -> None:
        self.dao.insert(
            "admin.audit_insert",
            {
                "actor_id": actor_id,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "metadata_json": {},
                "created_at": datetime.now(timezone.utc).replace(tzinfo=None),
            },
        )

    def locations(self, query: str | None) -> list[dict]:
        return self.dao.list(
            "locations.search",
            {"query": f"%{query.lower()}%" if query else None},
        )

    def projects(self, city: str | None) -> list[dict]:
        rows = self.dao.list("projects.list", {"city": city})
        for row in rows:
            for field in ("price_min", "price_max"):
                if row[field] is not None:
                    row[field] = float(row[field])
        return rows

    def agents(self) -> list[dict]:
        rows = self.dao.list("agents.list")
        for row in rows:
            row["name"] = row.pop("full_name") or "Demo property professional"
            row["locations_served"] = _json_value(row["locations_served"])
        return rows

    def developers(self) -> list[dict]:
        return self.dao.list("developers.list")

    def blog(self) -> list[dict]:
        return self.dao.list("blog.published")

    def categories(self) -> list[dict]:
        return self.dao.list("categories.active")

    def update_profile(self, user, data: dict) -> dict:
        avatar_url = data.get("avatar_url")
        if avatar_url is None:
            account = self.users.by_id(user.id)
            avatar_url = account["avatar_url"] if account else None
        self.dao.execute(
            "users.update_profile",
            {"id": user.id, "full_name": data["full_name"], "avatar_url": avatar_url},
        )
        profile = self.dao.one("profiles.by_user", {"user_id": user.id})
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        profile_values = {
            "user_id": user.id,
            "bio": data.get("bio") or "",
            "company": data.get("company"),
            "contact_phone": data.get("contact_phone"),
            "experience_years": data.get("experience_years"),
            "address": data.get("address"),
            "preferences": {},
            "updated_at": now,
        }
        if profile is None:
            self.dao.insert("profiles.insert", profile_values)
        else:
            self.dao.execute("profiles.update", profile_values)
        return {
            "id": user.id,
            "full_name": data["full_name"],
            "email": user.email,
            "phone": user.phone,
            "contact_phone": data.get("contact_phone"),
            "avatar_url": avatar_url,
            "bio": data.get("bio") or "",
            "company": data.get("company"),
            "experience_years": data.get("experience_years"),
            "address": data.get("address"),
        }

    def create_project(self, data: dict, actor_id: str) -> dict:
        if self.dao.one("projects.by_slug", {"slug": data["slug"]}):
            raise ServiceError(409, "Project slug already exists")
        project_id = str(uuid4())
        values = {
            **data,
            "id": project_id,
            "rera_verified": False,
        }
        self.dao.insert("projects.insert", values)
        self._audit(actor_id, "project.created", "project", project_id)
        return {"id": project_id, "slug": data["slug"]}

    def create_developer(self, data: dict, actor_id: str) -> dict:
        developer_id = str(uuid4())
        self.dao.insert(
            "developers.insert",
            {**data, "id": developer_id, "verified": False},
        )
        self._audit(actor_id, "developer.created", "developer", developer_id)
        return {"id": developer_id, "name": data["name"]}

    def create_blog_post(self, data: dict, actor_id: str) -> dict:
        if self.dao.one("blog.by_slug", {"slug": data["slug"]}):
            raise ServiceError(409, "Blog slug already exists")
        post_id = str(uuid4())
        self.dao.insert(
            "blog.insert",
            {
                **data,
                "id": post_id,
                "created_at": datetime.now(timezone.utc).replace(tzinfo=None),
            },
        )
        self._audit(actor_id, "blog.created", "blog_post", post_id)
        return {"id": post_id, "slug": data["slug"]}

    def create_category(self, data: dict, actor_id: str) -> dict:
        slug = slugify(data["name"])
        if self.dao.one(
            "categories.by_name_or_slug", {"name": data["name"], "slug": slug}
        ):
            raise ServiceError(409, "Category already exists")
        row = self.dao.insert(
            "categories.insert",
            {"name": data["name"], "slug": slug, "is_active": data["is_active"]},
        )
        self._audit(actor_id, "category.created", "property_category", str(row["id"]))
        return {"id": row["id"], "name": data["name"], "slug": slug}

    def create_location(self, data: dict, actor_id: str) -> dict:
        row = self.dao.insert("locations.insert", data)
        self._audit(actor_id, "location.created", "location", str(row["id"]))
        return {"id": row["id"], "city": data["city"], "locality": data["locality"]}

    def create_agent(self, data: dict, actor_id: str) -> dict:
        if data.get("user_id") and self.users.by_id(data["user_id"]) is None:
            raise ServiceError(404, "Agent user not found")
        agent_id = str(uuid4())
        self.dao.insert(
            "agents.insert",
            {
                **data,
                "id": agent_id,
                "locations_served": data.get("locations_served", []),
                "verified": False,
            },
        )
        self._audit(actor_id, "agent.created", "agent", agent_id)
        return {"id": agent_id}
