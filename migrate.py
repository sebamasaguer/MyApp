"""
Migra los datos del bot de instancia única al esquema multi-bot.
Leer TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY, TELEGRAM_CHAT_ID del .env.
Crear usuario admin y bot inicial, luego reasignar tasks y day_log existentes.

Uso: python migrate.py
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

import database as db
from auth import hash_password
from crypto import encrypt


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    timezone = os.getenv("TIMEZONE", "America/Argentina/Salta")

    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not admin_email or not admin_password:
        print("Error: definí ADMIN_EMAIL y ADMIN_PASSWORD en .env antes de migrar.")
        sys.exit(1)

    db.init_db()

    if db.count_users() == 0:
        user_id = db.create_user(admin_email, hash_password(admin_password), "admin")
        print(f"Usuario admin creado: {admin_email} (id={user_id})")
    else:
        existing = db.get_user_by_email(admin_email)
        if not existing:
            print(f"Error: ya hay usuarios en la base pero {admin_email} no existe.")
            sys.exit(1)
        user_id = existing["id"]
        print(f"Usando usuario existente: {admin_email} (id={user_id})")

    if not token or not api_key or not chat_id:
        print("No se encontraron credenciales del bot en .env. Saltando migración del bot.")
        return

    bot_id = db.create_bot(
        user_id=user_id,
        name="Bot principal",
        token_enc=encrypt(token),
        api_key_enc=encrypt(api_key),
        chat_id=chat_id,
        timezone=timezone,
        morning_time="08:00",
        followup_time="08:30",
        night_time="23:00",
    )
    print(f"Bot creado con id={bot_id}")

    db.migrate_existing_data(bot_id)
    print("Datos existentes (tasks, day_log) migrados al bot.")
    print("Migracion completada.")


if __name__ == "__main__":
    main()
