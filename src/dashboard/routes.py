import pathlib

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.db.session import async_session
from src.db.repositories import block_user, unblock_user
from src.dashboard.auth import require_auth, check_password, create_session_cookie, COOKIE_NAME
from src.dashboard import stats

TEMPLATES_DIR = pathlib.Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(prefix="/dashboard")


# --- Auth ---

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
async def login_submit(request: Request, password: str = Form(...)):
    if check_password(password):
        response = RedirectResponse("/dashboard", status_code=302)
        return create_session_cookie(response)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid password"})


@router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse("/dashboard/login", status_code=302)
    response.delete_cookie(COOKIE_NAME)
    return response


# --- Dashboard pages ---

@router.get("", response_class=HTMLResponse)
async def index(request: Request):
    redirect = require_auth(request)
    if redirect:
        return redirect
    async with async_session() as session:
        overview = await stats.get_overview_stats(session)
        top_events = await stats.get_top_events(session)
    return templates.TemplateResponse("index.html", {
        "request": request, "stats": overview, "top_events": top_events, "page": "index",
    })


@router.get("/users", response_class=HTMLResponse)
async def users_page(request: Request):
    redirect = require_auth(request)
    if redirect:
        return redirect
    async with async_session() as session:
        users = await stats.get_all_users(session)
        growth = await stats.get_user_growth(session)
    return templates.TemplateResponse("pages.html", {
        "request": request, "section": "users", "users": users, "growth": growth, "page": "users",
    })


@router.get("/events", response_class=HTMLResponse)
async def events_page(request: Request):
    redirect = require_auth(request)
    if redirect:
        return redirect
    async with async_session() as session:
        events = await stats.get_all_events(session)
    return templates.TemplateResponse("pages.html", {
        "request": request, "section": "events", "events": events, "page": "events",
    })


@router.get("/tickets", response_class=HTMLResponse)
async def tickets_page(request: Request):
    redirect = require_auth(request)
    if redirect:
        return redirect
    async with async_session() as session:
        tickets = await stats.get_all_tickets(session)
        top_sellers = await stats.get_top_sellers(session)
    return templates.TemplateResponse("pages.html", {
        "request": request, "section": "tickets", "tickets": tickets,
        "top_sellers": top_sellers, "page": "tickets",
    })


@router.get("/blocked", response_class=HTMLResponse)
async def blocked_page(request: Request):
    redirect = require_auth(request)
    if redirect:
        return redirect
    async with async_session() as session:
        blocked = await stats.get_blocked_users(session)
    return templates.TemplateResponse("pages.html", {
        "request": request, "section": "blocked", "blocked": blocked, "page": "blocked",
    })


# --- Block/Unblock actions ---

@router.post("/block", response_class=HTMLResponse)
async def block_action(request: Request, telegram_id: int = Form(...), reason: str = Form("")):
    redirect = require_auth(request)
    if redirect:
        return redirect
    async with async_session() as session:
        await block_user(session, telegram_id, reason=reason or None)
    return RedirectResponse("/dashboard/blocked", status_code=302)


@router.post("/unblock", response_class=HTMLResponse)
async def unblock_action(request: Request, telegram_id: int = Form(...)):
    redirect = require_auth(request)
    if redirect:
        return redirect
    async with async_session() as session:
        await unblock_user(session, telegram_id)
    return RedirectResponse("/dashboard/blocked", status_code=302)
