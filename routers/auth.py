from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import database as db
from auth import create_token, verify_password

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    remember: str = Form(default=""),
):
    user = db.get_user_by_email(email)
    if not user or not verify_password(password, user["hashed_password"]):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Email o contraseña incorrectos"},
            status_code=401,
        )

    remember_me = remember == "true"
    token = create_token(user["id"], remember=remember_me)
    max_age = 60 * 60 * 24 * 30 if remember_me else 60 * 60 * 8

    resp = RedirectResponse(url="/dashboard", status_code=303)
    resp.set_cookie(
        "access_token", token, httponly=True, samesite="lax", max_age=max_age
    )
    return resp


@router.post("/logout")
async def logout():
    resp = RedirectResponse(url="/login", status_code=303)
    resp.delete_cookie("access_token")
    return resp
