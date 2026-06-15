"""CLI para operaciones administrativas."""
import argparse
import os
import sys

from dotenv import load_dotenv

load_dotenv()

import database as db
from auth import hash_password


def cmd_create_user(email: str, password: str) -> None:
    db.init_db()
    existing = db.get_user_by_email(email)
    if existing:
        print(f"Error: ya existe un usuario con email {email}")
        sys.exit(1)
    count = db.count_users()
    role = "admin" if count == 0 else "user"
    user_id = db.create_user(email, hash_password(password), role)
    print(f"Usuario creado: {email} (id={user_id}, role={role})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Daily Agent CLI")
    subs = parser.add_subparsers(dest="command")

    p_create = subs.add_parser("create_user", help="Crear un usuario del dashboard")
    p_create.add_argument("email")
    p_create.add_argument("password")

    args = parser.parse_args()

    if args.command == "create_user":
        cmd_create_user(args.email, args.password)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
