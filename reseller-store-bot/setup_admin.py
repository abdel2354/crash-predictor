"""Create the first admin account in the database."""

import sys

import database as db


def main() -> None:
    db.init_db()

    if len(sys.argv) < 3:
        print("Usage: python setup_admin.py <login> <password>")
        print("Example: python setup_admin.py admin8340 kgUhsmcY982")
        sys.exit(1)

    login = sys.argv[1]
    password = sys.argv[2]

    existing = db.get_account_by_login(login)
    if existing:
        print(f"Account '{login}' already exists.")
        sys.exit(1)

    account = db.create_account(login, password, is_admin=1)
    if account:
        print(f"Admin account '{login}' created successfully!")
    else:
        print("Failed to create account.")
        sys.exit(1)


if __name__ == "__main__":
    main()
