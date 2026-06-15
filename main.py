import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

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


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass  # silenciar logs de acceso


def _start_health_server(port: int):
    HTTPServer(("0.0.0.0", port), _HealthHandler).serve_forever()


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN no está configurado en .env")

    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not chat_id:
        raise ValueError("TELEGRAM_CHAT_ID no está configurado en .env")

    db.init_db()
    logger.info("Base de datos inicializada.")

    health_port = int(os.getenv("HEALTH_PORT", "8081"))
    threading.Thread(target=_start_health_server, args=(health_port,), daemon=True).start()
    logger.info("Health check disponible en puerto %s /health", health_port)

    app = Application.builder().token(token).build()
    register_handlers(app)
    setup_scheduler(app)

    port = int(os.getenv("PORT", "8080"))
    webhook_url = f"https://myapp.saltia.com.ar/{token}"

    logger.info("Agente diario iniciado en modo webhook. Puerto: %s", port)
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=token,
        webhook_url=webhook_url,
        allowed_updates=["message"],
    )


if __name__ == "__main__":
    main()
