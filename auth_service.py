"""ACC-02.3 - Authentication, session, and role-based access."""
from dataclasses import dataclass
from typing import Optional
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash
from models import User

# Same message for wrong email AND wrong password (required).
INVALID_MSG = "Invalid email or password."

# Used so a missing email takes the same time as a wrong password.
_DUMMY_HASH = generate_password_hash("dummy-password-for-timing")

# Which page each role lands on, and which pages each role may open.
ROLE_HOME = {"Customer": "customer_home", "Administrator": "admin_dashboard"}
PAGE_ACCESS = {
    "customer_home":   {"Customer"},
    "browse_cars":     {"Customer"},
    "admin_dashboard": {"Administrator"},
}


@dataclass
class CurrentUser:
    user_id: int
    first_name: str
    email: str
    role: str


class AppSession:
    """Holds the logged-in user for the running app (desktop 'session')."""
    def __init__(self):
        self.user: Optional[CurrentUser] = None

    def login(self, user: User):
        self.user = CurrentUser(user.user_id, user.first_name, user.email, user.role)

    def logout(self):
        self.user = None

    @property
    def is_logged_in(self):
        return self.user is not None


app_session = AppSession()   # one shared session for the whole app


def _safe_check(pw_hash: str, password: str) -> bool:
    try:
        return check_password_hash(pw_hash, password)
    except Exception:        # unknown/placeholder hash format -> treat as wrong
        return False


def login(session: Session, email: str, password: str):
    """Returns (success, message, home_page). Starts the session on success."""
    email = (email or "").strip().lower()
    if not email or not password:
        return False, INVALID_MSG, None

    user = session.query(User).filter(User.email == email).first()
    if user is None:
        _safe_check(_DUMMY_HASH, password)
        return False, INVALID_MSG, None
    if not _safe_check(user.password_hash, password):
        return False, INVALID_MSG, None

    app_session.login(user)
    return True, "Login successful.", ROLE_HOME.get(user.role)


def logout():
    app_session.logout()


def can_access(page: str) -> bool:
    """Role-based access check - call before opening any page."""
    if not app_session.is_logged_in:
        return False
    return app_session.user.role in PAGE_ACCESS.get(page, set())


def require_access(page: str):
    if not can_access(page):
        raise PermissionError("You do not have access to this page.")
