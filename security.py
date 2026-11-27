"""Compatibility layer.
The team's UI (app_ui.py) still calls register_user() and authenticate_user().
They now run through account_service.py (ACC-01.3) and auth_service.py (ACC-02.3).
"""
from sqlalchemy.orm import Session
from models import User
from account_service import register_customer
from auth_service import login


def register_user(session: Session, first_name: str, last_name: str, email: str,
                  plain_password: str, role: str = 'Customer',
                  driver_license: str = None, phone: str = None):
    """Returns (success, message). Public registration only creates Customers;
    the 'role' argument is ignored on purpose."""
    return register_customer(session, first_name, last_name, email, plain_password,
                             driver_license=driver_license, phone=phone)


def authenticate_user(session: Session, email: str, plain_password: str):
    """Returns the User object on success, or None (same failure for wrong email
    or wrong password). Also starts the app session."""
    ok, _msg, _home = login(session, email, plain_password)
    if not ok:
        return None
    return session.query(User).filter(User.email == (email or "").strip().lower()).first()