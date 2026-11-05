import argparse

from app.dao.repositories import UserDao
from app.dao.template import NamedParameterJdbcTemplate
from app.db.datasource import data_source


def main() -> None:
    parser = argparse.ArgumentParser(description="Revoke an Aashiyana user's admin role")
    parser.add_argument("email")
    args = parser.parse_args()

    with data_source.engine.begin() as connection:
        user = UserDao(connection).by_email(args.email)
        if user is None:
            raise SystemExit("User not found")
        NamedParameterJdbcTemplate(connection).update(
            "user_roles.delete_admin",
            {"user_id": user["id"]},
        )
    print("Admin role revoked")


if __name__ == "__main__":
    main()
