import argparse
from datetime import datetime, timezone

from app.dao.repositories import UserDao
from app.dao.template import NamedParameterJdbcTemplate
from app.db.datasource import data_source


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Grant admin role to an existing Aashiyana user"
    )
    parser.add_argument("email")
    args = parser.parse_args()

    with data_source.engine.begin() as connection:
        user = UserDao(connection).by_email(args.email)
        if user is None:
            raise SystemExit(
                "User not found. Sign in once first so Firebase provisions the account."
            )
        jdbc = NamedParameterJdbcTemplate(connection)
        existing_roles = UserDao(connection).roles(user["id"])
        if "admin" not in existing_roles:
            jdbc.insert(
                "user_roles.insert",
                {"user_id": user["id"], "role": "admin"},
            )
        jdbc.insert(
            "admin.audit_insert",
            {
                "actor_id": user["id"],
                "action": "admin.role.granted",
                "entity_type": "user",
                "entity_id": str(user["id"]),
                "metadata_json": {"email": args.email},
                "created_at": datetime.now(timezone.utc).replace(tzinfo=None),
            },
        )
    print(f"Admin role granted to {args.email}")


if __name__ == "__main__":
    main()
