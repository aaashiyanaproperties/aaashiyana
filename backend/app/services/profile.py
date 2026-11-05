from sqlalchemy import Connection

from app.dao.repositories import UserDao
from app.services.catalog import CatalogService


class ProfileService:
    def __init__(self, connection: Connection):
        self.dao = UserDao(connection)
        self.catalog = CatalogService(connection)

    def get(self, user) -> dict:
        profile = self.dao.one("profiles.by_user", {"user_id": user.id})
        return {
            "id": user.id,
            "email": user.email,
            "phone": user.phone,
            "contact_phone": profile.get("contact_phone") if profile else None,
            "avatar_url": user.avatar_url,
            "full_name": user.full_name,
            "roles": list(user.roles),
        }

    def update(self, user, data: dict) -> dict:
        return self.catalog.update_profile(user, data)
