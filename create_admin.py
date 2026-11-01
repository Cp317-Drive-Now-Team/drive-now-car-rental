"""Run by the team to create an Administrator (public sign-up can't do this).
Usage:  python create_admin.py
"""
import getpass
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash
from models import User
from config import DATABASE_URL

session = sessionmaker(bind=create_engine(DATABASE_URL))()
email = input("Admin email: ").strip().lower()
pw = getpass.getpass("Password (min 8 chars): ")
if len(pw) < 8 or session.query(User).filter_by(email=email).first():
    raise SystemExit("Bad password or email already exists.")
session.add(User(first_name=input("First name: "), last_name=input("Last name: "),
                 email=email, password_hash=generate_password_hash(pw),
                 role="Administrator"))
session.commit()
print("Administrator created.")
