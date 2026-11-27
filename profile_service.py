"""ACC-01.3 (criterion 3) - View and edit a customer's profile, and change the password.

Works with models.py as it is. Uses the same checks and messages as account_service.py (sign-up),
so a change is held to the same rules as a new account.
Every function takes the logged-in user's id from the session, never from a form field.
Returns (success, message[, data]) like the other services.
"""
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash

from models import User
from account_service import EMAIL_RE, MIN_PASSWORD_LEN
from auth_service import app_session


def get_profile(session: Session, user_id: int):
    """Returns the editable profile fields (never the password hash), or None."""
    u = session.get(User, user_id)
    if u is None:
        return None
    return {"first_name": u.first_name, "last_name": u.last_name, "email": u.email,
            "phone": u.phone_number or "", "driver_license": u.driver_license_number or ""}


def update_profile(session: Session, user_id: int, first_name, last_name, email,
                   phone=None, driver_license=None):
    """Saves changes to the customer's own profile. Returns (success, message)."""
    first_name = (first_name or "").strip()
    last_name = (last_name or "").strip()
    email = (email or "").strip().lower()
    phone = (phone or "").strip() or None
    driver_license = (driver_license or "").strip() or None

    if not first_name or not last_name or not email:
        return False, "Please fill in all required fields."
    if not EMAIL_RE.match(email):
        return False, "Please enter a valid email address."
    if len(first_name) > 50 or len(last_name) > 50 or len(email) > 100:
        return False, "One or more fields are too long."
    if phone and len(phone) > 20:
        return False, "One or more fields are too long."
    if driver_license and len(driver_license) > 50:
        return False, "One or more fields are too long."

    user = session.get(User, user_id)
    if user is None:
        return False, "Account not found."

    # The email and license must not belong to SOMEONE ELSE (keeping your own is fine)
    if session.query(User).filter(User.email == email, User.user_id != user_id).first():
        return False, "Email already exists."
    if driver_license and session.query(User).filter(
            User.driver_license_number == driver_license, User.user_id != user_id).first():
        return False, "Driver's license is already registered."

    try:
        user.first_name, user.last_name, user.email = first_name, last_name, email
        user.phone_number, user.driver_license_number = phone, driver_license
        # role and password_hash are never touched here, so this can't be used to become an admin
        session.commit()
    except IntegrityError:
        session.rollback()
        return False, "Email already exists."
    except Exception:
        session.rollback()
        return False, "Could not save your changes. Please try again."

    # Keep the logged-in session in sync so the greeting shows the new name
    if app_session.is_logged_in and app_session.user.user_id == user_id:
        app_session.user.first_name = first_name
        app_session.user.email = email
    return True, "Your profile was saved."


def change_password(session: Session, user_id: int, current_password, new_password):
    """Changes the password after checking the current one. The new one is hashed. Returns (success, message)."""
    user = session.get(User, user_id)
    if user is None:
        return False, "Account not found."
    try:
        current_ok = check_password_hash(user.password_hash, current_password or "")
    except Exception:
        current_ok = False
    if not current_ok:
        return False, "Your current password is not correct."
    if len(new_password or "") < MIN_PASSWORD_LEN:
        return False, f"Password must be at least {MIN_PASSWORD_LEN} characters."
    if new_password == current_password:
        return False, "Your new password must be different from your current one."
    try:
        user.password_hash = generate_password_hash(new_password)
        session.commit()
    except Exception:
        session.rollback()
        return False, "Could not change your password. Please try again."
    return True, "Your password was changed."
