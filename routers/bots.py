from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import database as db
from auth import decode_token
from bot_manager import BotConfig
from crypto import decrypt, encrypt

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def _get_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    user_id = decode_token(token)
    if not user_id:
        return None
    return db.get_user_by_id(user_id)


def _can_access_bot(user, bot) -> bool:
    if not user or not bot:
        return False
    return bot["user_id"] == user["id"] or user["role"] == "admin"


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = _get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    bots = db.get_bots_by_user(user["id"])
    manager = request.app.state.bot_manager
    bots_with_status = [
        {**dict(b), **manager.get_status(b["id"])} for b in bots
    ]
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "user": dict(user), "bots": bots_with_status}
    )


@router.get("/bots/new", response_class=HTMLResponse)
async def new_bot_page(request: Request):
    user = _get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        "bot_form.html", {"request": request, "user": dict(user), "bot": None}
    )


@router.post("/bots/new")
async def create_bot(
    request: Request,
    name: str = Form(...),
    telegram_token: str = Form(...),
    anthropic_api_key: str = Form(...),
    telegram_chat_id: str = Form(...),
    timezone: str = Form("America/Argentina/Salta"),
    morning_time: str = Form("08:00"),
    followup_time: str = Form("08:30"),
    night_time: str = Form("23:00"),
):
    user = _get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    bot_id = db.create_bot(
        user_id=user["id"],
        name=name,
        token_enc=encrypt(telegram_token),
        api_key_enc=encrypt(anthropic_api_key),
        chat_id=telegram_chat_id,
        timezone=timezone,
        morning_time=morning_time,
        followup_time=followup_time,
        night_time=night_time,
    )

    config = BotConfig(
        id=bot_id, name=name,
        telegram_token=telegram_token,
        anthropic_api_key=anthropic_api_key,
        telegram_chat_id=telegram_chat_id,
        timezone=timezone,
        morning_time=morning_time,
        followup_time=followup_time,
        night_time=night_time,
    )
    await request.app.state.bot_manager.start_bot(config)
    return RedirectResponse(url=f"/bots/{bot_id}", status_code=303)


@router.get("/bots/{bot_id}", response_class=HTMLResponse)
async def bot_detail(bot_id: int, request: Request):
    user = _get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    bot = db.get_bot(bot_id)
    if not _can_access_bot(user, bot):
        return RedirectResponse(url="/dashboard", status_code=303)

    manager = request.app.state.bot_manager
    status = manager.get_status(bot_id)
    tasks = db.get_tasks(bot_id)
    logs = db.get_recent_logs(bot_id)

    return templates.TemplateResponse("bot_detail.html", {
        "request": request,
        "user": dict(user),
        "bot": {**dict(bot), **status},
        "tasks": [dict(t) for t in tasks],
        "logs": [dict(l) for l in logs],
    })


@router.get("/bots/{bot_id}/edit", response_class=HTMLResponse)
async def edit_bot_page(bot_id: int, request: Request):
    user = _get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    bot = db.get_bot(bot_id)
    if not _can_access_bot(user, bot):
        return RedirectResponse(url="/dashboard", status_code=303)

    return templates.TemplateResponse("bot_form.html", {
        "request": request,
        "user": dict(user),
        "bot": dict(bot),
    })


@router.post("/bots/{bot_id}/update")
async def update_bot(
    bot_id: int,
    request: Request,
    name: str = Form(...),
    telegram_token: str = Form(""),
    anthropic_api_key: str = Form(""),
    telegram_chat_id: str = Form(...),
    timezone: str = Form(...),
    morning_time: str = Form(...),
    followup_time: str = Form(...),
    night_time: str = Form(...),
):
    user = _get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    bot = db.get_bot(bot_id)
    if not _can_access_bot(user, bot):
        return RedirectResponse(url="/dashboard", status_code=303)

    manager = request.app.state.bot_manager
    was_running = manager.get_status(bot_id)["running"]
    if was_running:
        await manager.stop_bot(bot_id)

    updates = dict(
        name=name, telegram_chat_id=telegram_chat_id,
        timezone=timezone, morning_time=morning_time,
        followup_time=followup_time, night_time=night_time,
    )
    if telegram_token.strip():
        updates["telegram_token"] = encrypt(telegram_token.strip())
    if anthropic_api_key.strip():
        updates["anthropic_api_key"] = encrypt(anthropic_api_key.strip())

    db.update_bot(bot_id, **updates)

    if was_running:
        updated = db.get_bot(bot_id)
        config = BotConfig(
            id=bot_id,
            name=updated["name"],
            telegram_token=decrypt(updated["telegram_token"]),
            anthropic_api_key=decrypt(updated["anthropic_api_key"]),
            telegram_chat_id=updated["telegram_chat_id"],
            timezone=updated["timezone"],
            morning_time=updated["morning_time"],
            followup_time=updated["followup_time"],
            night_time=updated["night_time"],
        )
        await manager.start_bot(config)

    return RedirectResponse(url=f"/bots/{bot_id}", status_code=303)


@router.post("/bots/{bot_id}/start")
async def start_bot(bot_id: int, request: Request):
    user = _get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    bot = db.get_bot(bot_id)
    if not _can_access_bot(user, bot):
        return RedirectResponse(url="/dashboard", status_code=303)

    config = BotConfig(
        id=bot_id,
        name=bot["name"],
        telegram_token=decrypt(bot["telegram_token"]),
        anthropic_api_key=decrypt(bot["anthropic_api_key"]),
        telegram_chat_id=bot["telegram_chat_id"],
        timezone=bot["timezone"],
        morning_time=bot["morning_time"],
        followup_time=bot["followup_time"],
        night_time=bot["night_time"],
    )
    await request.app.state.bot_manager.start_bot(config)
    return RedirectResponse(url=f"/bots/{bot_id}", status_code=303)


@router.post("/bots/{bot_id}/stop")
async def stop_bot(bot_id: int, request: Request):
    user = _get_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    bot = db.get_bot(bot_id)
    if not _can_access_bot(user, bot):
        return RedirectResponse(url="/dashboard", status_code=303)

    await request.app.state.bot_manager.stop_bot(bot_id)
    return RedirectResponse(url=f"/bots/{bot_id}", status_code=303)


@router.post("/bots/{bot_id}/trigger/{check_type}")
async def trigger_checkin(bot_id: int, check_type: str, request: Request):
    user = _get_user(request)
    if not user:
        return {"error": "unauthorized"}, 401

    bot = db.get_bot(bot_id)
    if not _can_access_bot(user, bot):
        return {"error": "not found"}, 404

    manager = request.app.state.bot_manager
    app_instance = manager._apps.get(bot_id)
    if not app_instance:
        return {"error": "bot not running"}

    from bot import morning_checkin, night_checkin
    if check_type == "morning":
        await morning_checkin(app_instance)
    elif check_type == "night":
        await night_checkin(app_instance)

    return {"ok": True}
