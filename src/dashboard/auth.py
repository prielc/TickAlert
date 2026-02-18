from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from itsdangerous import URLSafeTimedSerializer

from src.config import ADMIN_DASHBOARD_PASSWORD, SECRET_KEY

COOKIE_NAME = "dashboard_session"
MAX_AGE = 60 * 60 * 24  # 24 hours

_serializer = URLSafeTimedSerializer(SECRET_KEY)


def create_session_cookie(response: Response) -> Response:
    """Set a signed session cookie on the response."""
    token = _serializer.dumps({"authenticated": True})
    response.set_cookie(COOKIE_NAME, token, max_age=MAX_AGE, httponly=True, samesite="lax")
    return response


def verify_session(request: Request) -> bool:
    """Check if the request has a valid session cookie."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return False
    try:
        data = _serializer.loads(token, max_age=MAX_AGE)
        return data.get("authenticated") is True
    except Exception:
        return False


def check_password(password: str) -> bool:
    """Verify the provided password against the configured admin password."""
    if not ADMIN_DASHBOARD_PASSWORD:
        return False
    return password == ADMIN_DASHBOARD_PASSWORD


def require_auth(request: Request) -> RedirectResponse | None:
    """Return a redirect to login if not authenticated, else None."""
    if not verify_session(request):
        return RedirectResponse("/dashboard/login", status_code=302)
    return None
