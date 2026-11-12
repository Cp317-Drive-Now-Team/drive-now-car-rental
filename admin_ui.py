import tkinter as tk
from tkinter import messagebox, ttk
from datetime import date
from decimal import Decimal, InvalidOperation
from car_admin import add_car, update_car, remove_car, list_all_cars, list_locations, CAR_STATUSES
from auth_service import update_rental_status_secure

# Colours (greyscale to match the wireframes)
WHITE = "#FFFFFF"
GREY = "#E6E6E6"
BORDER = "#D0D0D0"
DARK = "#3F3F3F"
TEXT = "#1F1F1F"
MUTED = "#6B6B6B"
RED = "#B00020"


def check_car_fields(make, model, year, car_type, daily_rate, status, location):
    """Checks the Add/Update Car form. Returns {field: error message}. Empty means everything is okay."""
    problems = {}
    values = {"make": make, "model": model, "year": year, "car_type": car_type,
              "daily_rate": daily_rate, "status": status, "location": location}
    for name, value in values.items():
        if not value:
            problems[name] = "This field is required."

    if "year" not in problems:
        if not year.isdigit() or not 1990 <= int(year) <= date.today().year + 1:
            problems["year"] = "Enter a year between 1990 and next year."
    if "daily_rate" not in problems:
        try:
            if Decimal(daily_rate.lstrip("$")) <= 0:
                problems["daily_rate"] = "Enter a daily price greater than 0."
        except InvalidOperation:
            problems["daily_rate"] = "Enter a daily price greater than 0."
    return problems


class AdminWindow:
    """Admin car management (ADMIN-01) - add, update and remove cars"""

    def __init__(self, app, user):
        self.app = app
        self.user = user
        self.selected_car_id = None
        self.location_ids = {}  # location name -> location_id

        self.window = tk.Toplevel(app.root)
        self.window.title("DriveNow - Manage Cars")
        self.window.geometry("1180x820")
        self.window.minsize(1100, 800)
        self.window.configure(bg=WHITE)
        self.window.protocol("WM_DELETE_WINDOW", lambda: app.logout(self.window))

        # Navigation Bar
        nav = tk.Frame(self.window, bg=WHITE, padx=30, pady=12)
        nav.pack(fill=tk.X)
        tk.Label(nav, text="Drive Now\nCar Rentals", font=("Arial", 11, "bold"), bg=WHITE, fg=TEXT,
                 justify="left").pack(side=tk.LEFT)
        tk.Button(nav, text="Logout", font=("Arial", 11), bg=WHITE, fg=TEXT,
                  command=lambda: app.logout(self.window)).pack(side=tk.RIGHT)
        tk.Frame(self.window, bg=BORDER, height=1).pack(fill=tk.X)

        main_frame = tk.Frame(self.window, bg=WHITE, padx=30, pady=18)
        main_frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(main_frame, text="Manage Cars", font=("Arial", 20, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
        tk.Label(main_frame, text=f"Signed in as {user['first_name']} (Administrator). Select a car to edit or remove it, "
                                  f"or fill in the form to add a new one.",
                 font=("Arial", 9), bg=WHITE, fg=MUTED).pack(anchor="w", pady=(0, 12))

        columns = tk.Frame(main_frame, bg=WHITE)
        columns.pack(fill=tk.BOTH, expand=True)
        self.build_table(columns)
        self.build_form(columns)
        self.load_locations()
        self.load_cars()

    def build_table(self, parent):
        # Table of every car, including ones customers can't see
        holder = tk.Frame(parent, bg=WHITE)
        holder.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 18))
        headings = [("id", "ID", 36), ("year", "Year", 50), ("make", "Make", 80), ("model", "Model", 90),
                    ("type", "Type", 70), ("rate", "Price / Day", 80), ("status", "Status", 90),
                    ("listed", "Listed", 70), ("location", "Location", 170)]
        self.table = ttk.Treeview(holder, columns=[h[0] for h in headings], show="headings", selectmode="browse")
        for key, title, width in headings:
            self.table.heading(key, text=title)
            self.table.column(key, width=width, anchor="center" if key in ("id", "year", "rate") else "w")
        scrollbar = ttk.Scrollbar(holder, orient=tk.VERTICAL, command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.table.bind("<<TreeviewSelect>>", lambda event: self.fill_form())

    def build_form(self, parent):
        # Add / Edit Car form
        panel = tk.Frame(parent, bg=GREY, padx=16, pady=14, width=330)
        panel.pack(side=tk.RIGHT, fill=tk.Y)
        panel.pack_propagate(False)
        self.form_title = tk.Label(panel, text="Add a New Car", font=("Arial", 13, "bold"), bg=GREY, fg=TEXT)
        self.form_title.pack(anchor="w", pady=(0, 6))

        self.inputs = {}
        self.errors = {}
        for name, label in [("make", "Make"), ("model", "Model"), ("year", "Year"), ("car_type", "Vehicle Type"),
                            ("daily_rate", "Daily Price ($)"), ("status", "Status"), ("location", "Location")]:
            tk.Label(panel, text=label, font=("Arial", 9), bg=GREY, fg=TEXT).pack(anchor="w")
            if name == "car_type":
                widget = ttk.Combobox(panel, values=["Economy", "Sedan", "SUV", "Van"])  # can also type a new type
            elif name == "status":
                widget = ttk.Combobox(panel, values=list(CAR_STATUSES), state="readonly")
                widget.set("Available")
            elif name == "location":
                widget = ttk.Combobox(panel, state="readonly")
            else:
                widget = tk.Entry(panel, font=("Arial", 11), relief="solid", bd=1)
            widget.pack(fill=tk.X)
            error = tk.Label(panel, text="", font=("Arial", 8), bg=GREY, fg=RED)
            error.pack(anchor="w")
            self.inputs[name] = widget
            self.errors[name] = error

        # Buttons
        buttons = tk.Frame(panel, bg=GREY)
        buttons.pack(fill=tk.X, pady=(4, 0))
        buttons.columnconfigure(0, weight=1, uniform="btn")
        buttons.columnconfigure(1, weight=1, uniform="btn")
        tk.Button(buttons, text="Add Car", font=("Arial", 11, "bold"), bg=DARK, fg="white",
                  command=self.handle_add).grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=(0, 6))
        tk.Button(buttons, text="Update", font=("Arial", 11), bg=WHITE, fg=TEXT,
                  command=self.handle_update).grid(row=0, column=1, sticky="ew", pady=(0, 6))
        tk.Button(buttons, text="Remove", font=("Arial", 11), bg=WHITE, fg=TEXT,
                  command=self.handle_remove).grid(row=1, column=0, sticky="ew", padx=(0, 4))
        tk.Button(buttons, text="Clear Form", font=("Arial", 11), bg=WHITE, fg=TEXT,
                  command=self.clear_form).grid(row=1, column=1, sticky="ew")

        self.status_label = tk.Label(panel, text="", font=("Arial", 9), bg=GREY, fg=TEXT, wraplength=290, justify="left")
        self.status_label.pack(anchor="w", pady=(8, 0))

    def load_locations(self):
        session = self.app.Session()
        try:
            for loc in list_locations(session):
                self.location_ids[loc.location_name] = loc.location_id
        finally:
            session.close()
        self.inputs["location"]["values"] = list(self.location_ids)
        if self.location_ids:
            self.inputs["location"].current(0)

    def load_cars(self):
        session = self.app.Session()
        try:
            rows = []
            for car in list_all_cars(session, self.user["user_id"]):
                location = car.location.location_name if car.location else ""
                listed = "Yes" if car.is_active else "Removed"
                rows.append((car.car_id, car.year, car.make, car.model, car.car_type, f"${car.daily_rate:.2f}",
                             car.status, listed, location))
        except Exception as e:
            messagebox.showerror("Error", f"Could not load cars:\n{e}", parent=self.window)
            return
        finally:
            session.close()

        self.table.delete(*self.table.get_children())
        for row in rows:
            self.table.insert("", tk.END, iid=str(row[0]), values=row)

    def fill_form(self):
        # When a car is clicked in the table, put its details in the form so it can be edited
        selected = self.table.selection()
        if not selected:
            return
        car_id, year, make, model, car_type, rate, status, listed, location = self.table.item(selected[0])["values"]
        self.selected_car_id = int(car_id)
        values = {"make": make, "model": model, "year": year, "car_type": car_type,
                  "daily_rate": str(rate).lstrip("$"), "status": status, "location": location}
        for name, value in values.items():
            widget = self.inputs[name]
            if isinstance(widget, ttk.Combobox):
                widget.set(value)
            else:
                widget.delete(0, tk.END)
                widget.insert(0, value)
        for label in self.errors.values():
            label.config(text="")
        self.form_title.config(text=f"Edit Car #{self.selected_car_id}")
        self.status_label.config(text="")

    def get_form_values(self):
        # Reads the form and shows any errors. Returns None if something is wrong.
        form = {name: widget.get().strip() for name, widget in self.inputs.items()}
        problems = check_car_fields(**form)
        for name, label in self.errors.items():
            label.config(text=problems.get(name, ""))
        if problems:
            return None
        return {
            "make": form["make"],
            "model": form["model"],
            "year": int(form["year"]),
            "car_type": form["car_type"],
            "daily_rate": Decimal(form["daily_rate"].lstrip("$")),
            "status": form["status"],
            "location_id": self.location_ids[form["location"]],
        }

    def save(self, action, message):
        session = self.app.Session()
        try:
            action(session)
        except Exception as e:
            session.rollback()
            messagebox.showerror("Could Not Save", str(e), parent=self.window)
            return False
        finally:
            session.close()
        self.load_cars()
        self.status_label.config(text=message)
        return True

    def handle_add(self):
        values = self.get_form_values()
        if values is None:
            return
        if self.save(lambda s: add_car(s, self.user["user_id"], values),
                     f"Added {values['year']} {values['make']} {values['model']}."):
            self.clear_form(keep_message=True)

    def handle_update(self):
        if self.selected_car_id is None:
            self.status_label.config(text="Select a car in the table first.")
            return
        values = self.get_form_values()
        if values is None:
            return
        car_id = self.selected_car_id
        if self.save(lambda s: update_car(s, self.user["user_id"], car_id, values), f"Updated car #{car_id}."):
            self.table.selection_set(str(car_id))

    def handle_remove(self):
        if self.selected_car_id is None:
            self.status_label.config(text="Select a car in the table first.")
            return
        car_id = self.selected_car_id
        if not messagebox.askyesno("Remove Car", f"Remove car #{car_id}? Customers won't see it anymore, "
                                                 f"but its record and past bookings are kept.", parent=self.window):
            return
        if self.save(lambda s: remove_car(s, self.user["user_id"], car_id),
                     f"Car #{car_id} was removed and is now hidden from customers."):
            self.clear_form(keep_message=True)

    def clear_form(self, keep_message=False):
        self.selected_car_id = None
        if self.table.selection():
            self.table.selection_remove(self.table.selection())
        for name, widget in self.inputs.items():
            if isinstance(widget, ttk.Combobox):
                widget.set("")
            else:
                widget.delete(0, tk.END)
        self.inputs["status"].set("Available")
        if self.location_ids:
            self.inputs["location"].current(0)
        for label in self.errors.values():
            label.config(text="")
        self.form_title.config(text="Add a New Car")
        if not keep_message:
            self.status_label.config(text="")

    def handle_rental_status_update(self, reservation_id, new_status):
        """
        ADMIN-02.3
        Called when an admin updates a booking status in the management panel.

        """
        # Open a database session
        session = self.app.Session()
        try:
            # Call the secure backend function
            success, message = update_rental_status_secure(session, reservation_id, new_status)
            
            if success:
                messagebox.showinfo("Success", message, parent=self.window)
                # self.load_rentals()  # Refresh your UI view here
            else:
                # Successfully blocks customers attempting to bypass UI controls
                messagebox.showerror("Access Denied", message, parent=self.window)
                
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self.window)
        finally:
            session.close()
