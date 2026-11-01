import tkinter as tk
from tkinter import messagebox
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL
from account_service import register_customer
from auth_service import login, app_session
from car_listing import get_active_cars

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


class DriveNowApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DriveNow Car Rental - Login")
        self.root.geometry("500x230")
        self.root.resizable(False, False)

        main_frame = tk.Frame(root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="Welcome to DriveNow", font=("Arial", 14, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 15))

        tk.Label(main_frame, text="Email / Username:", font=("Arial", 10)).grid(row=1, column=0, sticky="w", pady=5)
        self.email_entry = tk.Entry(main_frame, width=30)
        self.email_entry.grid(row=1, column=1, pady=5)

        tk.Label(main_frame, text="Password:", font=("Arial", 10)).grid(row=2, column=0, sticky="w", pady=5)
        self.password_entry = tk.Entry(main_frame, width=30, show="*")
        self.password_entry.grid(row=2, column=1, pady=5)

        button_frame = tk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(15, 0))

        tk.Button(button_frame, text="Login", width=10, bg="#007ACC", fg="white",
                  command=self.handle_login).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Sign Up (Renter)", width=15, bg="#28A745", fg="white",
                  command=self.handle_signup).pack(side=tk.LEFT, padx=5)

    # ---------------- LOGIN (ACC-02.3) ----------------
    def handle_login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        if not email or not password:
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        session = SessionLocal()
        try:
            ok, msg, home = login(session, email, password)

            if ok:
                user = app_session.user
                messagebox.showinfo("Success", f"Login successful!\nWelcome back, {user.first_name} ({user.role})")

                if home == "customer_home":
                    self.open_car_browser_window(session, user)
                # elif home == "admin_dashboard":
                #     Aryan opens the admin page here
            else:
                messagebox.showwarning("Login Failed", msg)  # "Invalid email or password."
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not connect to database:\n{e}")
        finally:
            session.close()

    # ---------------- SIGN UP (ACC-01.3) ----------------
    def handle_signup(self):
        signup_window = tk.Toplevel(self.root)
        signup_window.title("Renter Sign Up")
        signup_window.geometry("400x400")
        signup_window.resizable(False, False)

        tk.Label(signup_window, text="Create Renter Account", font=("Arial", 12, "bold")).pack(pady=10)

        tk.Label(signup_window, text="First Name:").pack(anchor="w", padx=40)
        fn_entry = tk.Entry(signup_window, width=32)
        fn_entry.pack(padx=40, pady=2)

        tk.Label(signup_window, text="Last Name:").pack(anchor="w", padx=40)
        ln_entry = tk.Entry(signup_window, width=32)
        ln_entry.pack(padx=40, pady=2)

        tk.Label(signup_window, text="Email:").pack(anchor="w", padx=40)
        su_email = tk.Entry(signup_window, width=32)
        su_email.pack(padx=40, pady=2)

        tk.Label(signup_window, text="Password (min 8 characters):").pack(anchor="w", padx=40)
        su_pass = tk.Entry(signup_window, width=32, show="*")
        su_pass.pack(padx=40, pady=2)

        tk.Label(signup_window, text="Driver's License Number:").pack(anchor="w", padx=40)
        dl_entry = tk.Entry(signup_window, width=32)
        dl_entry.pack(padx=40, pady=2)

        def submit_renter():
            session = SessionLocal()
            try:
                success, msg = register_customer(
                    session=session,
                    first_name=fn_entry.get().strip(),
                    last_name=ln_entry.get().strip(),
                    email=su_email.get().strip(),
                    password=su_pass.get(),
                    driver_license=dl_entry.get().strip() or None,
                )

                if success:
                    messagebox.showinfo("Success", "Account created! You can now log in.", parent=signup_window)
                    signup_window.destroy()
                else:
                    messagebox.showerror("Registration Failed", msg, parent=signup_window)
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}", parent=signup_window)
            finally:
                session.close()

        tk.Button(signup_window, text="Register as Renter", bg="#28A745", fg="white",
                  font=("Arial", 10, "bold"), command=submit_renter).pack(pady=15)

    # ---------------- CAR LIST (CAR-01.3) ----------------
    def open_car_browser_window(self, session, user):
        car_window = tk.Toplevel(self.root)
        car_window.title("DriveNow - Available Vehicles")
        car_window.geometry("600x350")

        tk.Label(car_window, text=f"Welcome, {user.first_name}! Browse Available Fleet:",
                 font=("Arial", 12, "bold")).pack(pady=10)

        frame = tk.Frame(car_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        car_listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, width=80, font=("Courier", 10))

        for car in get_active_cars(session):
            car_listbox.insert(
                tk.END,
                f"[{car.car_id}] {car.year} {car.make} {car.model} ({car.car_type}) - ${car.daily_rate}/day")

        car_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=car_listbox.yview)

        tk.Button(car_window, text="Close", command=car_window.destroy).pack(pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = DriveNowApp(root)
    root.mainloop()