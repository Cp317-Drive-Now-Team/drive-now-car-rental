import tkinter as tk
from tkinter import messagebox
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, Car
from security import register_user, authenticate_user

# Database Connection Configuration (Pulls directly from your local MySQL instance)
DATABASE_URL = "mysql+pymysql://root:1234567890!@localhost:3306/drivenow_db" 


engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

class DriveNowApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DriveNow Car Rental - Login")
        self.root.geometry("500x230")
        self.root.resizable(False, False) # Keep fixed dimensions tidy

        # Main Frame Container
        main_frame = tk.Frame(root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title Label
        title_label = tk.Label(main_frame, text="Welcome to DriveNow", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 15))

        # Username / Email Field
        tk.Label(main_frame, text="Email / Username:", font=("Arial", 10)).grid(row=1, column=0, sticky="w", pady=5)
        self.email_entry = tk.Entry(main_frame, width=30)
        self.email_entry.grid(row=1, column=1, pady=5)

        # Password Field
        tk.Label(main_frame, text="Password:", font=("Arial", 10)).grid(row=2, column=0, sticky="w", pady=5)
        self.password_entry = tk.Entry(main_frame, width=30, show="*")
        self.password_entry.grid(row=2, column=1, pady=5)

        # Buttons Frame (Login & Sign Up)
        button_frame = tk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(15, 0))

        login_btn = tk.Button(button_frame, text="Login", width=10, bg="#007ACC", fg="white", command=self.handle_login)
        login_btn.pack(side=tk.LEFT, padx=5)

        signup_btn = tk.Button(button_frame, text="Sign Up (Renter)", width=15, bg="#28A745", fg="white", command=self.handle_signup)
        signup_btn.pack(side=tk.LEFT, padx=5)

    def handle_login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not email or not password:
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        session = SessionLocal()
        try:
            # Authenticate against MySQL database using security.py
            user = authenticate_user(session, email, password)
            
            if user:
                messagebox.showinfo("Success", f"Login successful!\nWelcome back, {user.first_name} ({user.role})")
                
                # If they are a customer, we can launch the vehicle browsing window!
                if user.role == 'Customer':
                    self.open_car_browser_window(session, user)
            else:
                messagebox.showwarning("Login Failed", "Invalid email or incorrect password.")
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not connect to database:\n{e}")
        finally:
            session.close()

    def handle_signup(self):
        # Opens the renter registration sub-window
        signup_window = tk.Toplevel(self.root)
        signup_window.title("Renter Sign Up")
        signup_window.geometry("400x350")
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
        
        tk.Label(signup_window, text="Password:").pack(anchor="w", padx=40)
        su_pass = tk.Entry(signup_window, width=32, show="*")
        su_pass.pack(padx=40, pady=2)

        tk.Label(signup_window, text="Driver's License Number:").pack(anchor="w", padx=40)
        dl_entry = tk.Entry(signup_window, width=32)
        dl_entry.pack(padx=40, pady=2)

        def submit_renter():
            first_name = fn_entry.get().strip()
            last_name = ln_entry.get().strip()
            email = su_email.get().strip()
            password = su_pass.get().strip()
            dl_num = dl_entry.get().strip()

            if not first_name or not last_name or not email or not password:
                messagebox.showerror("Error", "Please fill in all required fields.", parent=signup_window)
                return

            session = SessionLocal()
            try:
                # Register user using security.py (hashes password and commits to MySQL)
                success, msg = register_user(
                    session=session,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    plain_password=password,
                    role='Customer',
                    driver_license=dl_num if dl_num else None
                )
                
                if success:
                    messagebox.showinfo("Success", "Account created successfully! You can now log in.", parent=signup_window)
                    signup_window.destroy()
                else:
                    messagebox.showerror("Registration Failed", f"Could not register user:\n{msg}", parent=signup_window)
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}", parent=signup_window)
            finally:
                session.close()

        tk.Button(signup_window, text="Register as Renter", bg="#28A745", fg="white", font=("Arial", 10, "bold"), command=submit_renter).pack(pady=15)

    def open_car_browser_window(self, session, user):
        """Simple subsequent window demonstrating database integration (Browse Cars feature CAR-01)"""
        car_window = tk.Toplevel(self.root)
        car_window.title("DriveNow - Available Vehicles")
        car_window.geometry("600x350")

        tk.Label(car_window, text=f"Welcome, {user.first_name}! Browse Available Fleet:", font=("Arial", 12, "bold")).pack(pady=10)

        # Frame for listbox and scrollbar
        frame = tk.Frame(car_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        car_listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, width=80, font=("Courier", 10))
        
        # Query database for available cars (including your Subaru Outbacks!)
        available_cars = session.query(Car).filter(Car.status == 'Available').all()
        
        for car in available_cars:
            car_listbox.insert(tk.END, f"[{car.car_id}] {car.year} {car.make} {car.model} ({car.car_type}) - ${car.daily_rate}/day")

        car_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=car_listbox.yview)

        tk.Button(car_window, text="Close", command=car_window.destroy).pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = DriveNowApp(root)
    root.mainloop()