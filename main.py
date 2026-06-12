import logging
import os

from dotenv import load_dotenv

load_dotenv()  # debe ser lo primero, antes de cualquier import que lea os.getenv

from telegram.ext import Application

import database as db
from bot import register_handlers
from scheduler import setup_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN no está configurado en .env")

    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not chat_id:
        raise ValueError("TELEGRAM_CHAT_ID no está configurado en .env")

    db.init_db()
    logger.info("Base de datos inicializada.")

    app = Application.builder().token(token).build()
    register_handlers(app)
    setup_scheduler(app)

    logger.info("Agente diario iniciado. Esperando mensajes...")
    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
