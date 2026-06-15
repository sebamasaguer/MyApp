from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()


@router.post("/webhook/{token}")
async def handle_webhook(token: str, request: Request):
    data = await request.json()
    await request.app.state.bot_manager.process_update(token, data)
    return JSONResponse({"ok": True})
