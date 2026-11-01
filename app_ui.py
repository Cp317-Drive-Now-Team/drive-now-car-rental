import re
import tkinter as tk
from tkinter import messagebox
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from models import User
import auth_service
from account_service import register_customer
from browse_ui import BrowseWindow
from admin_ui import AdminWindow

# Database connection comes from config.py (copy config.example.py to config.py and set your own password)
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

# Colours used on every screen (greyscale to match the wireframes)
WHITE = "#FFFFFF"
DARK = "#3F3F3F"
TEXT = "#1F1F1F"
MUTED = "#6B6B6B"
RED = "#B00020"


class DriveNowApp:
    def __init__(self, root):
        self.root = root
        self.Session = SessionLocal  # the other screens use this to talk to the database
        self.current_window = None

        self.root.title("DriveNow Car Rentals - Sign In")
        self.root.geometry("460x440")
        self.root.resizable(False, False)
        self.root.configure(bg=WHITE)

        # Header
        header = tk.Frame(root, bg=WHITE, padx=30, pady=15)
        header.pack(fill=tk.X)
        tk.Label(header, text="Drive Now", font=("Arial", 14, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
        tk.Label(header, text="Car Rentals", font=("Arial", 9), bg=WHITE, fg=MUTED).pack(anchor="w")
        tk.Frame(root, bg="#D0D0D0", height=1).pack(fill=tk.X)

        # Main Frame Container
        main_frame = tk.Frame(root, bg=WHITE, padx=40, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="Sign In", font=("Arial", 20, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
        tk.Label(main_frame, text="Welcome back! Sign in to find your next rental.", font=("Arial", 9),
                 bg=WHITE, fg=MUTED).pack(anchor="w", pady=(0, 15))

        # Email Field
        tk.Label(main_frame, text="Email", font=("Arial", 11), bg=WHITE, fg=TEXT).pack(anchor="w")
        self.email_entry = tk.Entry(main_frame, font=("Arial", 11), relief="solid", bd=1)
        self.email_entry.pack(fill=tk.X, ipady=4, pady=(2, 10))

        # Password Field
        tk.Label(main_frame, text="Password", font=("Arial", 11), bg=WHITE, fg=TEXT).pack(anchor="w")
        self.password_entry = tk.Entry(main_frame, font=("Arial", 11), relief="solid", bd=1, show="*")
        self.password_entry.pack(fill=tk.X, ipady=4, pady=(2, 4))

        # Error message shows here instead of a popup
        self.login_error = tk.Label(main_frame, text="", font=("Arial", 9), bg=WHITE, fg=RED)
        self.login_error.pack(anchor="w", pady=(0, 8))

        # Buttons (Sign In & Create Account)
        tk.Button(main_frame, text="Sign In", font=("Arial", 11, "bold"), bg=DARK, fg="white",
                  command=self.handle_login).pack(fill=tk.X, ipady=3)
        tk.Label(main_frame, text="Don't have an account?", font=("Arial", 9), bg=WHITE,
                 fg=MUTED).pack(pady=(12, 3))
        tk.Button(main_frame, text="Create Account", font=("Arial", 11), bg=WHITE, fg=TEXT,
                  command=self.handle_signup).pack(fill=tk.X, ipady=3)

        # Pressing Enter also signs in
        self.email_entry.bind("<Return>", lambda event: self.handle_login())
        self.password_entry.bind("<Return>", lambda event: self.handle_login())
        self.email_entry.focus_set()

    # ---------------- LOGIN (ACC-02.3) ----------------
    def handle_login(self):
        """Sign In (ACC-02)"""
        email = self.email_entry.get().strip().lower()
        password = self.password_entry.get()
        self.login_error.config(text="")

        if not email or not password:
            self.login_error.config(text="Please enter your email and password.")
            return

        session = SessionLocal()
        try:
            # Albina's auth_service checks the password and starts the session (ACC-02.3)
            success, message, home_page = auth_service.login(session, email, password)
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not connect to database:\n{e}")
            return
        finally:
            session.close()

        if not success:
            # Same message for a wrong email or a wrong password, so nobody can guess which emails have accounts
            self.login_error.config(text=message)
            self.password_entry.delete(0, tk.END)
            return

        current = auth_service.app_session.user
        user_info = {"user_id": current.user_id, "first_name": current.first_name, "role": current.role}

        # Hide the sign in window and open the right screen for the role
        self.password_entry.delete(0, tk.END)
        self.root.withdraw()
        if home_page == "admin_dashboard" and auth_service.can_access("admin_dashboard"):
            self.current_window = AdminWindow(self, user_info)
        elif auth_service.can_access("browse_cars"):
            self.current_window = BrowseWindow(self, user_info)

    def logout(self, window):
        """Logout (ACC-02) - closes the current screen and goes back to sign in"""
        if not messagebox.askyesno("Logout", "Are you sure you want to log out?", parent=window):
            return
        auth_service.logout()  # ends the session in auth_service
        window.destroy()
        self.current_window = None
        self.email_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self.login_error.config(text="")
        self.root.deiconify()
        self.email_entry.focus_set()

    def handle_signup(self):
        """Create Account form (ACC-01). Name, email, phone and password are required."""
        signup_window = tk.Toplevel(self.root)
        signup_window.title("DriveNow - Create Account")
        signup_window.geometry("520x540")
        signup_window.resizable(False, False)
        signup_window.configure(bg=WHITE)
        signup_window.grab_set()

        form = tk.Frame(signup_window, bg=WHITE, padx=35, pady=20)
        form.pack(fill=tk.BOTH, expand=True)
        tk.Label(form, text="Create Your Account", font=("Arial", 18, "bold"), bg=WHITE, fg=TEXT).grid(
            row=0, column=0, columnspan=2, sticky="w")
        tk.Label(form, text="Fields marked with * are required.", font=("Arial", 9), bg=WHITE, fg=MUTED).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(0, 10))
        form.columnconfigure(0, weight=1, uniform="col")
        form.columnconfigure(1, weight=1, uniform="col")

        # (field name, label, row, column, hide text?)
        fields = [
            ("first_name", "First Name *", 2, 0, False),
            ("last_name", "Last Name *", 2, 1, False),
            ("email", "Email *", 5, 0, False),
            ("phone", "Phone Number *", 5, 1, False),
            ("password", "Password * (8+ characters)", 8, 0, True),
            ("confirm", "Confirm Password *", 8, 1, True),
            ("licence", "Driver's Licence Number", 11, 0, False),
        ]
        self.signup_entries = {}
        self.signup_errors = {}
        for name, label, row, col, hidden in fields:
            pad = (0, 10) if col == 0 else (10, 0)
            tk.Label(form, text=label, font=("Arial", 11), bg=WHITE, fg=TEXT).grid(row=row, column=col, sticky="w", padx=pad)
            entry = tk.Entry(form, font=("Arial", 11), relief="solid", bd=1, show="*" if hidden else "")
            entry.grid(row=row + 1, column=col, sticky="ew", ipady=3, padx=pad)
            error = tk.Label(form, text="", font=("Arial", 9), bg=WHITE, fg=RED)
            error.grid(row=row + 2, column=col, sticky="w", padx=pad, pady=(0, 4))
            self.signup_entries[name] = entry
            self.signup_errors[name] = error

        entries = self.signup_entries
        errors = self.signup_errors

        def submit_account():
            first_name = entries["first_name"].get().strip()
            last_name = entries["last_name"].get().strip()
            email = entries["email"].get().strip().lower()
            phone = entries["phone"].get().strip()
            password = entries["password"].get()
            confirm = entries["confirm"].get()
            licence = entries["licence"].get().strip()

            for label in errors.values():
                label.config(text="")
            problems = check_signup_fields(first_name, last_name, email, phone, password, confirm)

            session = SessionLocal()
            try:
                # Only 1 account per email
                if "email" not in problems and email_taken(session, email):
                    problems["email"] = "An account with this email already exists."
                if licence and session.query(User).filter(User.driver_license_number == licence).first():
                    problems["licence"] = "This licence number is already registered."

                if problems:
                    for name, message in problems.items():
                        errors[name].config(text=message)
                    return

                # Albina's account_service checks the data again, hashes the password and saves
                # the account as a Customer (ACC-01.3)
                digits = phone_digits(phone)
                success, msg = register_customer(
                    session,
                    first_name,
                    last_name,
                    email,
                    password,
                    driver_license=licence if licence else None,
                    phone=f"{digits[0:3]}-{digits[3:6]}-{digits[6:]}"
                )

                if success:
                    messagebox.showinfo("Success", "Account created successfully! You can now sign in.", parent=signup_window)
                    signup_window.destroy()
                elif msg == "Email already exists.":
                    errors["email"].config(text="An account with this email already exists.")
                elif msg == "Driver's license is already registered.":
                    errors["licence"].config(text="This licence number is already registered.")
                else:
                    messagebox.showerror("Registration Failed", msg, parent=signup_window)
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}", parent=signup_window)
            finally:
                session.close()

        self.submit_account = submit_account
        tk.Button(form, text="Create Account", font=("Arial", 11, "bold"), bg=DARK, fg="white",
                  command=submit_account).grid(row=14, column=0, columnspan=2, sticky="ew", ipady=3, pady=(10, 0))
        signup_window.bind("<Return>", lambda event: submit_account())
        entries["first_name"].focus_set()
        self.signup_window = signup_window


def phone_digits(phone):
    # Keeps only the numbers, so 519-555-0199 and (519) 555 0199 both work
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits


def check_signup_fields(first_name, last_name, email, phone, password, confirm):
    """Returns a dictionary of {field: error message}. Empty means everything is okay."""
    problems = {}
    values = {"first_name": first_name, "last_name": last_name, "email": email, "phone": phone,
              "password": password, "confirm": confirm}
    for name, value in values.items():
        if not value:
            problems[name] = "This field is required."

    for name in ("first_name", "last_name"):
        if name not in problems and not re.match(r"^[A-Za-z][A-Za-z '\-]*$", values[name]):
            problems[name] = "Use letters only."
    if "email" not in problems and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        problems["email"] = "Enter a valid email address."
    if "phone" not in problems and len(phone_digits(phone)) != 10:
        problems["phone"] = "Enter a valid 10-digit phone number."
    if "password" not in problems and len(password) < 8:
        problems["password"] = "Password must be at least 8 characters."
    if "password" not in problems and "confirm" not in problems and password != confirm:
        problems["confirm"] = "Passwords do not match."
    return problems


def email_taken(session, email):
    return session.query(User).filter(func.lower(User.email) == email.lower()).first() is not None



if __name__ == "__main__":
    root = tk.Tk()
    app = DriveNowApp(root)
    root.mainloop()
