from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Connection

from app.dao.repositories import UserDao


@dataclass(frozen=True)
class UserContext:
    id: str
    email: str | None
    phone: str | None
    full_name: str
    avatar_url: str | None
    roles: tuple[str, ...]


class IdentityService:
    def __init__(self, connection: Connection):
        self.dao = UserDao(connection)

    def _context(self, row: dict) -> UserContext:
        return UserContext(
            id=str(row["id"]),
            email=row.get("email"),
            phone=row.get("phone"),
            full_name=row["full_name"],
            avatar_url=row.get("avatar_url"),
            roles=tuple(self.dao.roles(str(row["id"]))),
        )

    def by_dev_email(self, email: str) -> UserContext:
        user = self.dao.by_email(email)
        if user is None:
            user_id = str(uuid4())
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            user = self.dao.create(
                id=user_id,
                firebase_uid=None,
                email=email,
                phone=None,
                full_name="Local development user",
                avatar_url=None,
                is_active=True,
                is_verified=False,
                created_at=now,
            )
            self.dao.insert("user_roles.insert", {"user_id": user_id, "role": "seller"})
        return self._context(user)

    def by_firebase_claims(self, claims: dict) -> UserContext:
        firebase_uid = claims.get("uid")
        if not firebase_uid:
            raise ValueError("Firebase token does not contain a user ID")
        user = self.dao.by_firebase_uid(firebase_uid)
        if user is None:
            user_id = str(uuid4())
            user = self.dao.create(
                id=user_id,
                firebase_uid=firebase_uid,
                email=claims.get("email"),
                phone=claims.get("phone_number"),
                full_name=claims.get("name") or "Aashiyana user",
                avatar_url=claims.get("picture"),
                is_active=True,
                is_verified=False,
                created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            self.dao.insert("user_roles.insert", {"user_id": user_id, "role": "buyer"})
        return self._context(user)

    def optional_by_firebase_claims(self, claims: dict) -> UserContext | None:
        firebase_uid = claims.get("uid")
        if not firebase_uid:
            return None
        user = self.dao.by_firebase_uid(firebase_uid)
        return self._context(user) if user is not None else None
