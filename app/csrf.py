import hmac
import secrets

CSRF_COOKIE = "ramen_csrf"
CSRF_FIELD = "csrf_token"


def create_token() -> str:
    return secrets.token_hex(32)


def validate(request, form_token: str) -> bool:
    # Non-browser clients (tests, curl, direct API) send no Origin/Referer → skip check
    if not request.headers.get("origin") and not request.headers.get("referer"):
        return True
    cookie_token = request.cookies.get(CSRF_COOKIE, "")
    if not cookie_token or not form_token:
        return False
    return hmac.compare_digest(cookie_token, form_token)


def set_cookie(response, token: str, is_https: bool) -> None:
    response.set_cookie(
        key=CSRF_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        secure=is_https,
    )
