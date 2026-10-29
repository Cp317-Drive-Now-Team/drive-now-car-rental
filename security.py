from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Session
from models import User

def register_user(session: Session, first_name: str, last_name: str, email: str, plain_password: str, role: str = 'Customer', driver_license: str = None, phone: str = None):
    """
    Hashes the plain text password securely and creates a new user record in the database.
    Fulfills ACC-01 (Manage Account) and security PII guidelines.
    """
    # 1. Generate secure cryptographic hash
    hashed_password = generate_password_hash(plain_password)

    # 2. Create User model instance
    new_user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password_hash=hashed_password,
        role=role,
        driver_license_number=driver_license,
        phone_number=phone
    )

    try:
        # 3. Add to database session and commit
        session.add(new_user)
        session.commit()
        print(f"Successfully registered user: {email} as {role}")
        return True, "User registered successfully."
    except Exception as e:
        session.rollback()
        print(f"Registration error: {e}")
        return False, str(e)


def authenticate_user(session: Session, email: str, plain_password: str):
    """
    Queries the database for the user by email and verifies the provided password against the stored hash.
    Returns the user object if successful, or None if authentication fails.
    """
    # 1. Fetch user from database
    user = session.query(User).filter(User.email == email).first()

    if not user:
        print("Authentication failed: User email not found.")
        return None

    # 2. Check the provided password against the stored cryptographic hash
    if check_password_hash(user.password_hash, plain_password):
        print(f"Authentication successful for: {user.email} (Role: {user.role})")
        return user
    else:
        print("Authentication failed: Incorrect password.")
        return None