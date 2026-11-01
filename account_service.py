"""ACC-01.3 - Account creation (server-side logic).
Public registration ONLY creates Customers. Admins are created by the team (create_admin.py).
"""
import re
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash
from models import User

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LEN = 8


def register_customer(session: Session, first_name, last_name, email, password,
                      driver_license=None, phone=None):
    """Returns (success: bool, message: str)."""
    first_name = (first_name or "").strip()
    last_name = (last_name or "").strip()
    email = (email or "").strip().lower()
    password = password or ""
    driver_license = (driver_license or "").strip() or None
    phone = (phone or "").strip() or None

    # 1. All required fields filled in?
    if not first_name or not last_name or not email or not password:
        return False, "Please fill in all required fields."

    # 2. Do the values look right?
    if not EMAIL_RE.match(email):
        return False, "Please enter a valid email address."
    if len(password) < MIN_PASSWORD_LEN:
        return False, f"Password must be at least {MIN_PASSWORD_LEN} characters."
    if len(first_name) > 50 or len(last_name) > 50 or len(email) > 100:
        return False, "One or more fields are too long."

    # 3. Email already exists?
    if session.query(User).filter(User.email == email).first():
        return False, "Email already exists."
    if driver_license and session.query(User).filter(
            User.driver_license_number == driver_license).first():
        return False, "Driver's license is already registered."

    # 4. Hash password (real one is never stored)
    hashed = generate_password_hash(password)

    # 5. Save with role = Customer (role is hard-coded, never taken from input)
    user = User(first_name=first_name, last_name=last_name, email=email,
                password_hash=hashed, role="Customer",
                driver_license_number=driver_license, phone_number=phone)
    try:
        session.add(user)
        session.commit()
        return True, "Account created."
    except IntegrityError:          # two people registering at the same moment
        session.rollback()
        return False, "Email already exists."
    except Exception:
        session.rollback()
        return False, "Could not create account. Please try again."
