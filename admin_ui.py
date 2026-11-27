import tkinter as tk
from tkinter import messagebox, ttk
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from car_admin import add_car, update_car, remove_car, list_all_cars, list_locations, CAR_STATUSES
from auth_service import update_rental_status_secure
from rental_admin import list_rentals, mark_picked_up, mark_returned
import rental_status
from report_service import rental_report

# Colours (greyscale to match the wireframes)
WHITE = "#FFFFFF"
GREY = "#E6E6E6"
BORDER = "#D0D0D0"
DARK = "#3F3F3F"
TEXT = "#1F1F1F"
MUTED = "#595959"  # darker grey so small text is easier to read (UI-01)
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
    """Admin page with three tabs: Manage Cars (ADMIN-01), Manage Rentals (ADMIN-02) and Reports (ADMIN-03)"""

    def __init__(self, app, user):
        self.app = app
        self.user = user
        self.selected_car_id = None
        self.location_ids = {}  # location name -> location_id

        self.window = tk.Toplevel(app.root)
        self.window.title("DriveNow - Administrator")
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

        # Tabs - Manage Cars, Manage Rentals and Reports
        self.tabs = ttk.Notebook(self.window)
        self.tabs.pack(fill=tk.BOTH, expand=True, padx=20, pady=(12, 15))
        self.tabs.enable_traversal()  # Ctrl+Tab switches tabs with the keyboard (UI-01)

        cars_tab = tk.Frame(self.tabs, bg=WHITE, padx=15, pady=12)
        self.tabs.add(cars_tab, text="  Manage Cars  ")
        tk.Label(cars_tab, text="Manage Cars", font=("Arial", 20, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
        tk.Label(cars_tab, text=f"Signed in as {user['first_name']} (Administrator). Select a car to edit or remove it, "
                                f"or fill in the form to add a new one.",
                 font=("Arial", 9), bg=WHITE, fg=MUTED).pack(anchor="w", pady=(0, 12))
        columns = tk.Frame(cars_tab, bg=WHITE)
        columns.pack(fill=tk.BOTH, expand=True)
        self.build_table(columns)
        self.build_form(columns)
        self.load_locations()
        self.load_cars()

        rentals_tab = tk.Frame(self.tabs, bg=WHITE, padx=15, pady=12)
        self.tabs.add(rentals_tab, text="  Manage Rentals  ")
        self.build_rentals_tab(rentals_tab)
        self.load_rentals()

        reports_tab = tk.Frame(self.tabs, bg=WHITE, padx=15, pady=12)
        self.tabs.add(reports_tab, text="  Reports  ")
        self.build_reports_tab(reports_tab)
        self.load_report()
        # Refresh the report every time the tab is opened, so new bookings show up
        self.tabs.bind("<<NotebookTabChanged>>",
                       lambda event: self.load_report() if self.tabs.index("current") == 2 else None)

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

    # ---------------- MANAGE RENTALS (ADMIN-02.2) ----------------
    def build_rentals_tab(self, tab):
        tk.Label(tab, text="Manage Rentals", font=("Arial", 20, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
        tk.Label(tab, text="Select a rental, then mark it as picked up when the customer gets the car, "
                           "or returned when the car comes back.",
                 font=("Arial", 9), bg=WHITE, fg=MUTED).pack(anchor="w", pady=(0, 10))

        # Status filter
        top = tk.Frame(tab, bg=WHITE)
        top.pack(fill=tk.X, pady=(0, 8))
        tk.Label(top, text="Show", font=("Arial", 11), bg=WHITE, fg=TEXT).pack(side=tk.LEFT)
        self.rental_filter = ttk.Combobox(top, values=["All"] + list(rental_status.RENTAL_STATUSES),
                                          state="readonly", width=15)
        self.rental_filter.set("All")
        self.rental_filter.pack(side=tk.LEFT, padx=(6, 0))
        self.rental_filter.bind("<<ComboboxSelected>>", lambda event: self.load_rentals())
        self.rental_count = tk.Label(top, text="", font=("Arial", 10), bg=WHITE, fg=MUTED)
        self.rental_count.pack(side=tk.LEFT, padx=(12, 0))

        # Rentals table
        holder = tk.Frame(tab, bg=WHITE)
        holder.pack(fill=tk.BOTH, expand=True)
        headings = [("id", "Booking", 70), ("customer", "Customer", 150), ("car", "Car", 150),
                    ("start", "Pick-up", 105), ("end", "Return", 105), ("total", "Total", 85),
                    ("payment", "Payment", 85), ("status", "Status", 95)]
        self.rentals_table = ttk.Treeview(holder, columns=[h[0] for h in headings], show="headings",
                                          selectmode="browse")
        for key, title, width in headings:
            self.rentals_table.heading(key, text=title)
            self.rentals_table.column(key, width=width, anchor="w" if key in ("customer", "car") else "center")
        scrollbar = ttk.Scrollbar(holder, orient=tk.VERTICAL, command=self.rentals_table.yview)
        self.rentals_table.configure(yscrollcommand=scrollbar.set)
        self.rentals_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.rentals_table.bind("<<TreeviewSelect>>", lambda event: self.update_rental_buttons())

        # Picked up and Returned buttons
        buttons = tk.Frame(tab, bg=WHITE)
        buttons.pack(anchor="w", pady=(10, 0))
        self.picked_up_btn = tk.Button(buttons, text="Mark Picked Up", font=("Arial", 11, "bold"), bg=DARK,
                                       fg="white", state=tk.DISABLED,
                                       command=lambda: self.rental_action('Mark Picked Up'))
        self.picked_up_btn.pack(side=tk.LEFT, padx=(0, 8), ipady=2)
        self.returned_btn = tk.Button(buttons, text="Mark Returned", font=("Arial", 11), bg=WHITE, fg=TEXT,
                                      state=tk.DISABLED, command=lambda: self.rental_action('Mark Returned'))
        self.returned_btn.pack(side=tk.LEFT, ipady=2)
        tk.Button(buttons, text="Refresh", font=("Arial", 11), bg=WHITE, fg=TEXT,
                  command=self.load_rentals).pack(side=tk.LEFT, padx=(8, 0), ipady=2)

    def load_rentals(self):
        status_filter = self.rental_filter.get()
        session = self.app.Session()
        try:
            rentals = list_rentals(session, None if status_filter == "All" else status_filter)
        except Exception as e:
            messagebox.showerror("Error", f"Could not load rentals:\n{e}", parent=self.window)
            return
        finally:
            session.close()

        self.rentals_table.delete(*self.rentals_table.get_children())
        for r in rentals:
            self.rentals_table.insert("", tk.END, iid=str(r["id"]), values=(
                f"#{r['id']}", r["customer"], r["car"], r["start"].strftime("%b %d, %Y"),
                r["end"].strftime("%b %d, %Y"), f"${r['total']:.2f}", r["payment"], r["status"]))
        self.rental_count.config(text=f"{len(rentals)} rental(s)")
        self.update_rental_buttons()

    def update_rental_buttons(self):
        # Only turn on the button that makes sense for the selected rental's status (rental_status.py)
        selected = self.rentals_table.selection()
        status = self.rentals_table.item(selected[0])["values"][7] if selected else None
        self.picked_up_btn.config(state=tk.NORMAL if rental_status.can_do('Mark Picked Up', status) else tk.DISABLED)
        self.returned_btn.config(state=tk.NORMAL if rental_status.can_do('Mark Returned', status) else tk.DISABLED)

    def rental_action(self, action):
        selected = self.rentals_table.selection()
        if not selected:
            return
        self.handle_rental_status_update(int(selected[0]), action)

    def handle_rental_status_update(self, reservation_id, new_status):
        """
        ADMIN-02.3
        Called when an admin updates a booking status in the management panel.
        new_status is the action from rental_status.py ('Mark Picked Up' or 'Mark Returned').
        Mark Returned saves the new status through update_rental_status_secure (in rental_admin.py).
        """
        # Open a database session
        session = self.app.Session()
        try:
            # Call the secure backend function
            if new_status == 'Mark Picked Up':
                success, message = mark_picked_up(session, reservation_id)
            else:
                success, message = mark_returned(session, reservation_id)

            if success:
                messagebox.showinfo("Success", message, parent=self.window)
                self.load_rentals()  # Refresh your UI view here
            elif message.startswith("Access Denied"):
                # Successfully blocks customers attempting to bypass UI controls
                messagebox.showerror("Access Denied", message, parent=self.window)
            else:
                # e.g. the booking hasn't been paid yet
                messagebox.showerror("Could Not Update", message, parent=self.window)
                
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self.window)
        finally:
            session.close()

    # ---------------- REPORTS (ADMIN-03) ----------------
    def build_reports_tab(self, tab):
        tk.Label(tab, text="Rental Reports", font=("Arial", 20, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
        tk.Label(tab, text="See which cars are booked the most. Leave the dates empty to include every booking, "
                           "or enter a date range to only count bookings with a pick-up date in that range.",
                 font=("Arial", 9), bg=WHITE, fg=MUTED).pack(anchor="w", pady=(0, 10))

        # Date range filter
        top = tk.Frame(tab, bg=WHITE)
        top.pack(fill=tk.X)
        tk.Label(top, text="From (mm/dd/yyyy)", font=("Arial", 11), bg=WHITE, fg=TEXT).pack(side=tk.LEFT)
        self.report_from = tk.Entry(top, font=("Arial", 11), relief="solid", bd=1, width=12)
        self.report_from.pack(side=tk.LEFT, padx=(6, 14), ipady=2)
        tk.Label(top, text="To (mm/dd/yyyy)", font=("Arial", 11), bg=WHITE, fg=TEXT).pack(side=tk.LEFT)
        self.report_to = tk.Entry(top, font=("Arial", 11), relief="solid", bd=1, width=12)
        self.report_to.pack(side=tk.LEFT, padx=(6, 14), ipady=2)
        tk.Button(top, text="Run Report", font=("Arial", 11, "bold"), bg=DARK, fg="white",
                  command=self.load_report).pack(side=tk.LEFT, ipady=1)
        tk.Button(top, text="Clear Dates", font=("Arial", 11), bg=WHITE, fg=TEXT,
                  command=self.clear_report_dates).pack(side=tk.LEFT, padx=(8, 0), ipady=1)
        for entry in (self.report_from, self.report_to):
            entry.bind("<Return>", lambda event: self.load_report())
        self.report_error = tk.Label(tab, text="", font=("Arial", 10), bg=WHITE, fg=RED)
        self.report_error.pack(anchor="w", pady=(4, 0))

        # Summary boxes
        boxes = tk.Frame(tab, bg=WHITE)
        boxes.pack(fill=tk.X, pady=(4, 10))
        self.summary_labels = {}
        for col, (key, title) in enumerate([("bookings", "Bookings"), ("revenue", "Revenue"),
                                            ("cancelled", "Cancellations"), ("most_booked", "Most booked car")]):
            boxes.columnconfigure(col, weight=1, uniform="box")
            box = tk.Frame(boxes, bg=GREY, padx=14, pady=10)
            box.grid(row=0, column=col, sticky="nsew", padx=(0, 10) if col < 3 else 0)
            tk.Label(box, text=title, font=("Arial", 10), bg=GREY, fg=MUTED).pack(anchor="w")
            self.summary_labels[key] = tk.Label(box, text="-", font=("Arial", 16, "bold"), bg=GREY, fg=TEXT,
                                                wraplength=220, justify="left")
            self.summary_labels[key].pack(anchor="w")

        # Table on the left, bar chart on the right
        bottom = tk.Frame(tab, bg=WHITE)
        bottom.pack(fill=tk.BOTH, expand=True)
        headings = [("car", "Car", 190), ("type", "Type", 80), ("bookings", "Bookings", 80),
                    ("days", "Days Rented", 90), ("cancelled", "Cancelled", 80), ("revenue", "Revenue", 95)]
        self.report_table = ttk.Treeview(bottom, columns=[h[0] for h in headings], show="headings", height=12)
        for key, title, width in headings:
            self.report_table.heading(key, text=title)
            self.report_table.column(key, width=width, anchor="w" if key == "car" else "center")
        self.report_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        chart_box = tk.Frame(bottom, bg=WHITE, padx=15)
        chart_box.pack(side=tk.RIGHT, fill=tk.Y)
        tk.Label(chart_box, text="Bookings per car", font=("Arial", 11, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
        self.chart = tk.Canvas(chart_box, width=360, height=300, bg=WHITE, highlightthickness=0)
        self.chart.pack()

    def clear_report_dates(self):
        self.report_from.delete(0, tk.END)
        self.report_to.delete(0, tk.END)
        self.load_report()

    def load_report(self):
        self.report_error.config(text="")
        dates = []
        for entry in (self.report_from, self.report_to):
            text = entry.get().strip()
            value = None
            if text:
                for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d"):
                    try:
                        value = datetime.strptime(text, fmt).date()
                        break
                    except ValueError:
                        pass
                if value is None:
                    self.report_error.config(text="Enter dates as mm/dd/yyyy.")
                    return
            dates.append(value)
        if dates[0] and dates[1] and dates[1] < dates[0]:
            self.report_error.config(text="The 'To' date must be on or after the 'From' date.")
            return

        session = self.app.Session()
        try:
            rows, totals = rental_report(session, dates[0], dates[1])
        except Exception as e:
            messagebox.showerror("Error", f"Could not load the report:\n{e}", parent=self.window)
            return
        finally:
            session.close()

        # Summary boxes
        self.summary_labels["bookings"].config(text=str(totals["bookings"]))
        self.summary_labels["revenue"].config(text=f"${totals['revenue']:,.2f}")
        self.summary_labels["cancelled"].config(text=str(totals["cancelled"]))
        self.summary_labels["most_booked"].config(text=totals["most_booked"])

        # Table
        self.report_table.delete(*self.report_table.get_children())
        for r in rows:
            self.report_table.insert("", tk.END, iid=str(r["car_id"]), values=(
                f"#{r['car_id']} {r['car']}", r["type"], r["bookings"], r["days"], r["cancelled"],
                f"${r['revenue']:,.2f}"))

        self.draw_chart(rows)

    def draw_chart(self, rows):
        """Simple bar chart: one bar per car, longest bar = most bookings"""
        self.chart.delete("all")
        if not rows:
            return
        most = max(r["bookings"] for r in rows) or 1
        bar_height = min(28, int(280 / len(rows)) - 6)
        label_width = 150
        max_bar = 360 - label_width - 40
        for i, r in enumerate(rows):
            y = 10 + i * (bar_height + 6)
            name = f"#{r['car_id']} {r['car'].split(' ', 1)[1]}"  # e.g. #1 Toyota Corolla
            self.chart.create_text(label_width - 8, y + bar_height / 2, text=name, anchor="e",
                                   font=("Arial", 9), fill=TEXT)
            length = int(max_bar * r["bookings"] / most)
            if length > 0:
                self.chart.create_rectangle(label_width, y, label_width + length, y + bar_height,
                                            fill=DARK, outline=DARK)
            self.chart.create_text(label_width + length + 6, y + bar_height / 2, text=str(r["bookings"]),
                                   anchor="w", font=("Arial", 9, "bold"), fill=TEXT)
