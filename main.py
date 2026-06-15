import logging
import os
import threading
from contextlib import asynccontextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer

from dotenv import load_dotenv

load_dotenv()

import database as db
from bot_manager import BotManager

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
        pass


def _start_health_server(port: int):
    HTTPServer(("0.0.0.0", port), _HealthHandler).serve_forever()


@asynccontextmanager
async def lifespan(app):
    db.init_db()

    webhook_base = os.getenv("WEBHOOK_BASE_URL", "https://myapp.saltia.com.ar")
    manager = BotManager(webhook_base_url=webhook_base)
    await manager.load_all()
    app.state.bot_manager = manager

    yield

    await manager.shutdown_all()


from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

from routers import auth as auth_router
from routers import bots as bots_router
from routers import webhook as webhook_router

app.include_router(auth_router.router)
app.include_router(bots_router.router)
app.include_router(webhook_router.router)

templates = Jinja2Templates(directory="templates")


@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard")


def main():
    import uvicorn

    health_port = int(os.getenv("HEALTH_PORT", "8081"))
    threading.Thread(
        target=_start_health_server, args=(health_port,), daemon=True
    ).start()
    logger.info("Health check en puerto %s", health_port)

    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
