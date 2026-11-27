import re
from sqlalchemy import func
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash
from models import User
from auth_service import app_session
from email_check import check_email

MIN_PASSWORD_LEN = 8


def phone_digits(phone):
    # Keeps only the numbers, so 519-555-0199 and (519) 555 0199 both work
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits


def is_own_account(user_id):
    # Customers can only see and change their own account
    return app_session.is_logged_in and app_session.user.user_id == user_id


def get_profile(session: Session, user_id: int):
    """Returns the account's details as a dictionary, or None."""
    if not is_own_account(user_id):
        return None
    user = session.get(User, user_id)
    if user is None:
        return None
    return {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone": user.phone_number or "",
        "licence": user.driver_license_number or "",
        "member_since": user.created_at,
    }


def check_profile_fields(first_name, last_name, email, phone):
    """Returns {field: error message}. Same rules as the Create Account form. Empty means okay."""
    problems = {}
    for name, value in (("first_name", first_name), ("last_name", last_name), ("phone", phone)):
        if not value:
            problems[name] = "This field is required."
    for name, value in (("first_name", first_name), ("last_name", last_name)):
        if name not in problems:
            if not re.match(r"^[A-Za-z][A-Za-z '\-]*$", value):
                problems[name] = "Use letters only."
            elif len(value) > 50:
                problems[name] = "Must be 50 characters or less."
    ok, message, _ = check_email(email)
    if not ok:
        problems["email"] = message
    if "phone" not in problems and len(phone_digits(phone)) != 10:
        problems["phone"] = "Enter a valid 10-digit phone number."
    return problems


def update_profile(session: Session, user_id: int, first_name, last_name, email, phone, licence):
    """
    Saves changes to the customer's details.
    Returns (success, message, problems) where problems is {field: error message} for the form.
    """
    # 1. Customers can only change their own account
    if not is_own_account(user_id):
        return False, "You can only change your own account.", {}
    user = session.get(User, user_id)
    if user is None:
        return False, "Account not found.", {}

    first_name = (first_name or "").strip()
    last_name = (last_name or "").strip()
    phone = (phone or "").strip()
    licence = (licence or "").strip()

    # 2. Check the values (the form checks these too, but the backend checks again)
    problems = check_profile_fields(first_name, last_name, email, phone)
    if problems:
        return False, "Please fix the highlighted fields.", problems
    email = check_email(email)[2]

    # 3. Only 1 account per email and per licence (not counting this account)
    if session.query(User).filter(func.lower(User.email) == email, User.user_id != user_id).first():
        problems["email"] = "An account with this email already exists."
    if licence and session.query(User).filter(User.driver_license_number == licence,
                                              User.user_id != user_id).first():
        problems["licence"] = "This licence number is already registered."
    if problems:
        return False, "Please fix the highlighted fields.", problems

    # 4. Save
    digits = phone_digits(phone)
    try:
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.phone_number = f"{digits[0:3]}-{digits[3:6]}-{digits[6:]}"
        user.driver_license_number = licence or None
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Profile update error: {e}")
        return False, "Could not save your changes. Please try again.", {}

    # 5. Keep the signed-in session up to date (the new email is used to sign in next time)
    app_session.user.first_name = first_name
    app_session.user.email = email
    print(f"Updated account #{user_id}")
    return True, "Your changes were saved.", {}


def change_password(session: Session, user_id: int, current_password, new_password, confirm_password):
    """Changes the password after checking the current one. Returns (success, message, problems)."""
    if not is_own_account(user_id):
        return False, "You can only change your own account.", {}
    user = session.get(User, user_id)
    if user is None:
        return False, "Account not found.", {}

    problems = {}
    if not current_password:
        problems["current"] = "This field is required."
    if not new_password:
        problems["new"] = "This field is required."
    elif len(new_password) < MIN_PASSWORD_LEN:
        problems["new"] = f"Password must be at least {MIN_PASSWORD_LEN} characters."
    if not confirm_password:
        problems["confirm"] = "This field is required."
    elif "new" not in problems and new_password != confirm_password:
        problems["confirm"] = "Passwords do not match."
    if problems:
        return False, "Please fix the highlighted fields.", problems

    try:
        correct = check_password_hash(user.password_hash, current_password)
    except Exception:
        correct = False
    if not correct:
        return False, "Please fix the highlighted fields.", {"current": "Current password is incorrect."}
    if check_password_hash(user.password_hash, new_password):
        return False, "Please fix the highlighted fields.", {"new": "New password must be different."}

    try:
        user.password_hash = generate_password_hash(new_password)  # only the hash is stored
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Password change error: {e}")
        return False, "Could not change your password. Please try again.", {}
    print(f"Changed password for account #{user_id}")
    return True, "Your password was changed.", {}
