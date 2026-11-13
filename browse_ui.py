import tkinter as tk
from tkinter import messagebox, ttk
from datetime import date, datetime
from car_search import get_filter_options, get_locations, search_cars, SORT_OPTIONS
from booking_service import create_booking
import booking_rules
import payment_rules
import booking_ui

# Colours (greyscale to match the wireframes)
WHITE = "#FFFFFF"
GREY = "#E6E6E6"
BANNER = "#D9D9D9"
BORDER = "#D0D0D0"
DARK = "#3F3F3F"
TEXT = "#1F1F1F"
MUTED = "#6B6B6B"
RED = "#B00020"

VEHICLE_TYPES = ["Economy", "Sedan", "SUV", "Van"]  # same types as Wireframe 1
MAX_PRICE = 200  # the right end of the price slider means $200+
CARDS_PER_ROW = 4


def draw_car(canvas, x, y, size, colour=TEXT, bg=WHITE):
    """Draws the simple car shape used in the wireframes"""
    canvas.create_rectangle(x, y + size * 0.35, x + size, y + size * 0.65, fill=colour, outline=colour)  # body
    canvas.create_polygon(x + size * 0.2, y + size * 0.36, x + size * 0.32, y + size * 0.1, x + size * 0.68,
                          y + size * 0.1, x + size * 0.82, y + size * 0.36, fill=colour, outline=colour)  # roof
    canvas.create_rectangle(x + size * 0.34, y + size * 0.16, x + size * 0.48, y + size * 0.33, fill=bg, outline=bg)
    canvas.create_rectangle(x + size * 0.52, y + size * 0.16, x + size * 0.66, y + size * 0.33, fill=bg, outline=bg)
    for wheel in (0.24, 0.76):
        canvas.create_oval(x + size * (wheel - 0.12), y + size * 0.52, x + size * (wheel + 0.12), y + size * 0.76,
                           fill=bg, outline=bg)
        canvas.create_oval(x + size * (wheel - 0.08), y + size * 0.56, x + size * (wheel + 0.08), y + size * 0.72,
                           fill=colour, outline=colour)


def car_picture(parent, size, bg=WHITE):
    canvas = tk.Canvas(parent, width=size + 4, height=int(size * 0.8), bg=bg, highlightthickness=0)
    draw_car(canvas, 2, 0, size, bg=bg)
    return canvas


def read_date(text):
    # Accepts mm/dd/yyyy like the wireframe, or yyyy-mm-dd
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def check_search(pickup_text, return_text, min_price, max_price, today=None):
    """
    Checks the search inputs (CAR-02.2 rules).
    Returns (list of error messages, pick-up date, return date).
    """
    today = today or date.today()
    errors = []
    pickup = None
    return_date = None

    if bool(pickup_text) != bool(return_text):
        errors.append("Enter both a pick-up date and a return date.")
    elif pickup_text and return_text:
        pickup = read_date(pickup_text)
        return_date = read_date(return_text)
        if pickup is None or return_date is None:
            errors.append("Enter dates as mm/dd/yyyy.")
            pickup = return_date = None
        else:
            if pickup < today:
                errors.append("Pick-up date cannot be in the past.")
            if return_date <= pickup:
                errors.append("Return date must be after pick-up date.")

    if min_price > max_price:
        errors.append("Minimum price cannot be higher than maximum price.")
    return errors, pickup, return_date


class BrowseWindow:
    """Browse & Search Cars (CAR-01, CAR-02) based on Wireframe 1, and Car Details (CAR-03) based on Wireframe 2"""

    def __init__(self, app, user):
        self.app = app
        self.user = user
        self.dates = (None, None)  # dates from the last search, so the details page can fill them in
        self.page = None  # the page shown instead of the browse page (details, booking, payment, receipt, My Bookings)

        self.window = tk.Toplevel(app.root)
        self.window.title("DriveNow - Browse Cars")
        self.window.geometry("1120x760")
        self.window.minsize(1060, 700)
        self.window.configure(bg=WHITE)
        self.window.protocol("WM_DELETE_WINDOW", lambda: app.logout(self.window))

        self.build_nav_bar()
        self.browse_frame = tk.Frame(self.window, bg=WHITE, padx=30, pady=15)
        self.browse_frame.pack(fill=tk.BOTH, expand=True)
        self.build_search_banner()
        bottom = tk.Frame(self.browse_frame, bg=WHITE)
        bottom.pack(fill=tk.BOTH, expand=True, pady=(14, 0))
        self.build_filters(bottom)
        self.build_results(bottom)

        self.load_filter_options()
        self.search()

    def build_nav_bar(self):
        # Navigation Bar (same on every page in the wireframes)
        nav = tk.Frame(self.window, bg=WHITE, padx=30, pady=10)
        nav.pack(fill=tk.X)
        logo = tk.Frame(nav, bg=WHITE)
        logo.pack(side=tk.LEFT)
        car_picture(logo, 42).pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(logo, text="Drive Now\nCar Rentals", font=("Arial", 11, "bold"), bg=WHITE, fg=TEXT,
                 justify="left").pack(side=tk.LEFT)

        tk.Button(nav, text="Logout", font=("Arial", 11), bg=WHITE, fg=TEXT,
                  command=lambda: self.app.logout(self.window)).pack(side=tk.RIGHT, padx=(15, 0))
        # My Account is Sprint 3 (ACC-03), so it shows a message for now. My Bookings has a basic version (RENT-02).
        for page in ["My Account", "My Bookings", "Browse Cars", "Home"]:
            link = tk.Label(nav, text=page, font=("Arial", 12, "bold" if page == "Browse Cars" else "normal"),
                            bg=WHITE, fg=TEXT, cursor="hand2")
            link.pack(side=tk.RIGHT, padx=12)
            if page in ("Home", "Browse Cars"):
                link.bind("<Button-1>", lambda event: self.back_to_search())
            elif page == "My Bookings":
                link.bind("<Button-1>", lambda event: booking_ui.show_my_bookings(self))
            else:
                link.bind("<Button-1>", lambda event, p=page: messagebox.showinfo(
                    p, "This page will be added in a later sprint.", parent=self.window))
        tk.Frame(self.window, bg=BORDER, height=1).pack(fill=tk.X)

    def build_search_banner(self):
        # "Find Your Perfect Ride" banner with the search bar
        banner = tk.Frame(self.browse_frame, bg=BANNER, padx=20, pady=15)
        banner.pack(fill=tk.X)
        top = tk.Frame(banner, bg=BANNER)
        top.pack(fill=tk.X)
        tk.Label(top, text="Find Your Perfect Ride", font=("Arial", 20, "bold"), bg=BANNER, fg=TEXT).pack(anchor="w")
        tk.Label(top, text="Affordable. Reliable. Ready when you are.", font=("Arial", 9), bg=BANNER,
                 fg=TEXT).pack(anchor="w")
        tk.Label(top, text=f"Signed in as {self.user['first_name']}", font=("Arial", 9), bg=BANNER,
                 fg=MUTED).pack(anchor="w", pady=(3, 0))
        car_picture(top, 110, bg=BANNER).place(relx=1.0, rely=0.5, anchor="e")

        search_bar = tk.Frame(banner, bg=BANNER)
        search_bar.pack(fill=tk.X, pady=(12, 0))
        for col in range(4):
            search_bar.columnconfigure(col, weight=1, uniform="bar")

        boxes = []
        for col, title in enumerate(["Pick-up Date (mm/dd/yyyy)", "Return Date (mm/dd/yyyy)", "Car Type"]):
            box = tk.Frame(search_bar, bg=WHITE, padx=10, pady=6)
            box.grid(row=0, column=col, sticky="ew", padx=(0, 12))
            tk.Label(box, text=title, font=("Arial", 9), bg=WHITE, fg=MUTED).pack(anchor="w")
            boxes.append(box)

        self.pickup_entry = tk.Entry(boxes[0], font=("Arial", 11), relief="solid", bd=1)
        self.pickup_entry.pack(fill=tk.X)
        self.return_entry = tk.Entry(boxes[1], font=("Arial", 11), relief="solid", bd=1)
        self.return_entry.pack(fill=tk.X)
        self.type_box = ttk.Combobox(boxes[2], state="readonly")
        self.type_box.pack(fill=tk.X)
        tk.Button(search_bar, text="Search", font=("Arial", 12, "bold"), bg=DARK, fg="white",
                  command=self.search).grid(row=0, column=3, sticky="nsew")

        self.search_error = tk.Label(banner, text="", font=("Arial", 9), bg=BANNER, fg=RED, justify="left")
        self.search_error.pack(anchor="w", pady=(5, 0))

        self.pickup_entry.bind("<Return>", lambda event: self.search())
        self.return_entry.bind("<Return>", lambda event: self.search())
        self.type_box.bind("<<ComboboxSelected>>", lambda event: self.search())

    def build_filters(self, parent):
        # Filters Panel (left side of Wireframe 1)
        panel = tk.Frame(parent, bg=GREY, padx=15, pady=12, width=230)
        panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 14))
        panel.pack_propagate(False)
        tk.Label(panel, text="Filters", font=("Arial", 13, "bold"), bg=GREY, fg=TEXT).pack(anchor="w")

        # Price Range
        tk.Label(panel, text="Price Range (per day)", font=("Arial", 11, "bold"), bg=GREY, fg=TEXT).pack(anchor="w", pady=(10, 0))
        self.price_label = tk.Label(panel, text=f"$0 - ${MAX_PRICE}+", font=("Arial", 9), bg=GREY, fg=TEXT)
        self.price_label.pack(anchor="w")
        self.min_price = tk.IntVar(value=0)
        self.max_price = tk.IntVar(value=MAX_PRICE)
        for title, var in (("Min", self.min_price), ("Max", self.max_price)):
            row = tk.Frame(panel, bg=GREY)
            row.pack(fill=tk.X)
            tk.Label(row, text=title, font=("Arial", 9), bg=GREY, fg=MUTED, width=4, anchor="w").pack(side=tk.LEFT)
            slider = tk.Scale(row, from_=0, to=MAX_PRICE, resolution=5, orient=tk.HORIZONTAL, variable=var,
                              showvalue=False, bg="#7A7A7A", troughcolor=WHITE, highlightthickness=0, bd=0,
                              width=10, sliderlength=16, command=lambda value: self.update_price_label())
            slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
            slider.bind("<ButtonRelease-1>", lambda event: self.search())

        # Vehicle Type checkboxes
        tk.Label(panel, text="Vehicle Type", font=("Arial", 11, "bold"), bg=GREY, fg=TEXT).pack(anchor="w", pady=(10, 2))
        self.type_checks = {}
        self.checks_frame = tk.Frame(panel, bg=GREY)
        self.checks_frame.pack(fill=tk.X)

        # Extra filters
        tk.Label(panel, text="Make", font=("Arial", 11, "bold"), bg=GREY, fg=TEXT).pack(anchor="w", pady=(10, 2))
        self.make_box = ttk.Combobox(panel, state="readonly")
        self.make_box.pack(fill=tk.X)
        self.make_box.bind("<<ComboboxSelected>>", lambda event: self.search())

        tk.Label(panel, text="Make or Model", font=("Arial", 11, "bold"), bg=GREY, fg=TEXT).pack(anchor="w", pady=(10, 2))
        self.keyword_entry = tk.Entry(panel, font=("Arial", 11), relief="solid", bd=1)
        self.keyword_entry.pack(fill=tk.X)
        self.keyword_entry.bind("<Return>", lambda event: self.search())

        tk.Button(panel, text="Clear Filters", font=("Arial", 11), bg=WHITE, fg=TEXT,
                  command=self.clear_filters).pack(fill=tk.X, pady=(15, 0))

    def build_results(self, parent):
        # Car Cards area (right side of Wireframe 1)
        area = tk.Frame(parent, bg=GREY, padx=12, pady=10)
        area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        top = tk.Frame(area, bg=GREY)
        top.pack(fill=tk.X, pady=(0, 8))
        self.result_label = tk.Label(top, text="", font=("Arial", 11, "bold"), bg=GREY, fg=TEXT)
        self.result_label.pack(side=tk.LEFT)
        self.sort_box = ttk.Combobox(top, values=list(SORT_OPTIONS), state="readonly", width=20)
        self.sort_box.current(0)
        self.sort_box.pack(side=tk.RIGHT)
        self.sort_box.bind("<<ComboboxSelected>>", lambda event: self.search())
        tk.Label(top, text="Sort by", font=("Arial", 11), bg=GREY, fg=TEXT).pack(side=tk.RIGHT, padx=(0, 5))

        # Scrollable area for the cards
        holder = tk.Frame(area, bg=GREY)
        holder.pack(fill=tk.BOTH, expand=True)
        self.cards_canvas = tk.Canvas(holder, bg=GREY, highlightthickness=0)
        scrollbar = ttk.Scrollbar(holder, orient=tk.VERTICAL, command=self.cards_canvas.yview)
        self.cards_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.cards_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.cards_frame = tk.Frame(self.cards_canvas, bg=GREY)
        frame_id = self.cards_canvas.create_window((0, 0), window=self.cards_frame, anchor="nw")
        self.cards_frame.bind("<Configure>", lambda event: self.cards_canvas.configure(
            scrollregion=self.cards_canvas.bbox("all")))
        self.cards_canvas.bind("<Configure>", lambda event: self.cards_canvas.itemconfigure(frame_id, width=event.width))
        for col in range(CARDS_PER_ROW):
            self.cards_frame.columnconfigure(col, weight=1, uniform="card")

    def update_price_label(self):
        low = self.min_price.get()
        high = self.max_price.get()
        high_text = f"${high}+" if high >= MAX_PRICE else f"${high}"
        self.price_label.config(text=f"${low} - {high_text}")

    def load_filter_options(self):
        session = self.app.Session()
        try:
            types, makes = get_filter_options(session)
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not load filters:\n{e}", parent=self.window)
            types, makes = [], []
        finally:
            session.close()

        all_types = VEHICLE_TYPES + [t for t in types if t not in VEHICLE_TYPES]
        self.type_box["values"] = ["All Types"] + all_types
        self.type_box.current(0)
        self.make_box["values"] = ["All Makes"] + makes
        self.make_box.current(0)
        for car_type in all_types:
            var = tk.BooleanVar(value=False)
            tk.Checkbutton(self.checks_frame, text=car_type, variable=var, font=("Arial", 11), bg=GREY, fg=TEXT,
                           activebackground=GREY, highlightthickness=0, command=self.search).pack(anchor="w")
            self.type_checks[car_type] = var

    def clear_filters(self):
        self.pickup_entry.delete(0, tk.END)
        self.return_entry.delete(0, tk.END)
        self.keyword_entry.delete(0, tk.END)
        self.type_box.current(0)
        self.make_box.current(0)
        self.sort_box.current(0)
        self.min_price.set(0)
        self.max_price.set(MAX_PRICE)
        self.update_price_label()
        for var in self.type_checks.values():
            var.set(False)
        self.search()

    def search(self):
        """Search form and filters (CAR-02)"""
        errors, pickup, return_date = check_search(self.pickup_entry.get().strip(), self.return_entry.get().strip(),
                                                   self.min_price.get(), self.max_price.get())
        if errors:
            self.search_error.config(text="\n".join(errors))
            self.show_cards([], None, "Fix the search errors above to see results.")
            return
        self.search_error.config(text="")
        self.dates = (pickup, return_date)
        days = (return_date - pickup).days if pickup else None

        car_type = self.type_box.get()
        make = self.make_box.get()
        ticked = [t for t, var in self.type_checks.items() if var.get()]
        max_price = self.max_price.get()

        session = self.app.Session()
        try:
            cars = search_cars(
                session,
                pickup_date=pickup,
                return_date=return_date,
                car_type=None if car_type == "All Types" else car_type,
                car_types=ticked if ticked else None,
                make=None if make == "All Makes" else make,
                keyword=self.keyword_entry.get().strip() or None,
                min_price=self.min_price.get() or None,
                max_price=None if max_price >= MAX_PRICE else max_price,
                sort=SORT_OPTIONS[self.sort_box.get()],
            )
            # Copy what we need before the session closes
            results = []
            for car in cars:
                loc = car.location
                results.append({"id": car.car_id, "make": car.make, "model": car.model, "type": car.car_type,
                                "year": car.year, "rate": car.daily_rate,
                                "location": loc.location_name if loc else "",
                                "city": f"{loc.city}, {loc.state_province}" if loc else "",
                                "address": f"{loc.address}, {loc.city}, {loc.state_province} {loc.postal_code}" if loc else ""})
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not load cars:\n{e}", parent=self.window)
            return
        finally:
            session.close()

        self.show_cards(results, days)

    def show_cards(self, results, days, message=None):
        """Browse cars page (CAR-01) - one card for each available car"""
        for card in self.cards_frame.winfo_children():
            card.destroy()

        for i, car in enumerate(results):
            card = tk.Frame(self.cards_frame, bg=WHITE, padx=10, pady=12, highlightthickness=1,
                            highlightbackground=BORDER, cursor="hand2")
            card.grid(row=i // CARDS_PER_ROW, column=i % CARDS_PER_ROW, sticky="nsew", padx=6, pady=6)
            car_picture(card, 100).pack()
            tk.Label(card, text=f"{car['make']} {car['model']}", font=("Arial", 11, "bold"), bg=WHITE, fg=TEXT).pack(pady=(5, 0))
            tk.Label(card, text=f"{car['year']} | {car['type']}", font=("Arial", 9), bg=WHITE, fg=TEXT).pack()
            tk.Label(card, text=car["city"], font=("Arial", 9), bg=WHITE, fg=MUTED).pack()
            tk.Label(card, text=f"${car['rate']:.2f} / day", font=("Arial", 11, "bold"), bg=BANNER, fg=TEXT,
                     padx=14, pady=4).pack(pady=(8, 0))
            if days:
                tk.Label(card, text=f"Est. ${car['rate'] * days:.2f} for {days} days", font=("Arial", 9),
                         bg=WHITE, fg=MUTED).pack(pady=(4, 0))
            tk.Label(card, text="View Details", font=("Arial", 10, "underline"), bg=WHITE, fg=TEXT).pack(pady=(6, 0))

            # Clicking anywhere on the card opens its details page
            for widget in [card] + card.winfo_children():
                widget.bind("<Button-1>", lambda event, c=car: self.open_details(c))

        self.cards_canvas.yview_moveto(0)
        if message:
            self.result_label.config(text=message, fg=RED)
        elif not results:
            self.result_label.config(text="No cars match your search. Try different dates or filters.", fg=RED)
        else:
            text = f"{len(results)} cars available" if len(results) != 1 else "1 car available"
            if days:
                text += f" for {days} days"
            self.result_label.config(text=text, fg=TEXT)

    def new_page(self, title):
        """Hides the browse page (or the last page) and returns an empty frame for the next page"""
        self.browse_frame.pack_forget()
        if self.page is not None:
            self.page.destroy()
        self.window.title(f"DriveNow - {title}")
        self.page = tk.Frame(self.window, bg=WHITE, padx=40, pady=20)
        self.page.pack(fill=tk.BOTH, expand=True)
        return self.page

    def open_details(self, car):
        """Car Details & Booking page (CAR-03) based on Wireframe 2. Book Now creates the booking (RENT-01)."""
        page = self.new_page(f"{car['make']} {car['model']}")
        self.details_car = car
        tk.Label(page, text="Car Details & Booking", font=("Arial", 20, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
        tk.Label(page, text="Review your selected vehicle and enter your rental details to make a reservation.",
                 font=("Arial", 9), bg=WHITE, fg=MUTED).pack(anchor="w", pady=(0, 12))

        columns = tk.Frame(page, bg=WHITE)
        columns.pack(fill=tk.BOTH, expand=True)
        columns.columnconfigure(0, weight=3)
        columns.columnconfigure(1, weight=2)

        # Left side - picture and vehicle info
        left = tk.Frame(columns, bg=WHITE)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 25))
        picture = tk.Frame(left, bg="#F2F2F2", height=180, highlightthickness=1, highlightbackground=BORDER)
        picture.pack(fill=tk.X)
        picture.pack_propagate(False)
        car_picture(picture, 190, bg="#F2F2F2").place(relx=0.5, rely=0.5, anchor="center")

        name_row = tk.Frame(left, bg=WHITE)
        name_row.pack(fill=tk.X, pady=(12, 0))
        tk.Label(name_row, text=f"{car['make']} {car['model']}", font=("Arial", 16, "bold"), bg=WHITE, fg=TEXT).pack(side=tk.LEFT)
        tk.Label(name_row, text=f"${car['rate']:.2f}/day", font=("Arial", 16, "bold"), bg=WHITE, fg=TEXT).pack(side=tk.RIGHT)
        tk.Label(left, text=f"{car['year']}  |  {car['type']}  |  {car['city']}", font=("Arial", 10), bg=WHITE,
                 fg=MUTED).pack(anchor="w")

        # Vehicle details (make, model and price are listed separately so it's easier to compare cars)
        tk.Frame(left, bg=BORDER, height=1).pack(fill=tk.X, pady=12)
        tk.Label(left, text="Vehicle details", font=("Arial", 11, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
        features = tk.Frame(left, bg=WHITE)
        features.pack(fill=tk.X, pady=(5, 0))
        details = [("Make", car["make"]), ("Model", car["model"]), ("Year", car["year"]),
                   ("Vehicle type", car["type"]), ("Price per day", f"${car['rate']:.2f}"),
                   ("Price for 7 days", f"${car['rate'] * 7:.2f}")]
        for i, (title, value) in enumerate(details):
            row = (i // 3) * 2
            col = i % 3
            features.columnconfigure(col, weight=1)
            tk.Label(features, text=title, font=("Arial", 9), bg=WHITE, fg=MUTED).grid(row=row, column=col, sticky="w")
            tk.Label(features, text=value, font=("Arial", 11), bg=WHITE, fg=TEXT).grid(row=row + 1, column=col,
                                                                                       sticky="w", pady=(0, 8))

        tk.Label(left, text="Pick-up branch", font=("Arial", 11, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w", pady=(6, 2))
        branch = f"{car['location']}\n{car['address']}" if car["location"] else "-"
        tk.Label(left, text=branch, font=("Arial", 11), bg=WHITE, fg=TEXT, justify="left").pack(anchor="w")

        # Right side - "Book this car" box (RENT-01.2 booking form)
        right = tk.Frame(columns, bg=WHITE, padx=18, pady=15, highlightthickness=1, highlightbackground=BORDER)
        right.grid(row=0, column=1, sticky="new")
        tk.Label(right, text="Book this car", font=("Arial", 14, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
        tk.Label(right, text="Choose your dates and pick-up location.", font=("Arial", 9), bg=WHITE,
                 fg=MUTED).pack(anchor="w", pady=(0, 10))

        tk.Label(right, text="Pick-up date (mm/dd/yyyy)", font=("Arial", 11), bg=WHITE, fg=TEXT).pack(anchor="w")
        self.details_pickup = tk.Entry(right, font=("Arial", 11), relief="solid", bd=1)
        self.details_pickup.pack(fill=tk.X, ipady=3, pady=(2, 8))
        tk.Label(right, text="Return date (mm/dd/yyyy)", font=("Arial", 11), bg=WHITE, fg=TEXT).pack(anchor="w")
        self.details_return = tk.Entry(right, font=("Arial", 11), relief="solid", bd=1)
        self.details_return.pack(fill=tk.X, ipady=3, pady=(2, 8))
        if self.dates[0]:
            self.details_pickup.insert(0, self.dates[0].strftime("%m/%d/%Y"))
            self.details_return.insert(0, self.dates[1].strftime("%m/%d/%Y"))

        tk.Label(right, text="Pick-up location", font=("Arial", 11), bg=WHITE, fg=TEXT).pack(anchor="w")
        self.location_box = ttk.Combobox(right, state="readonly")
        self.location_box.pack(fill=tk.X, pady=(2, 4))
        self.location_ids = {}  # location name -> location_id
        session = self.app.Session()
        try:
            for loc in get_locations(session):
                self.location_ids[loc.location_name] = loc.location_id
        finally:
            session.close()
        self.location_box["values"] = list(self.location_ids)
        if car["location"]:
            self.location_box.set(car["location"])

        self.details_error = tk.Label(right, text="", font=("Arial", 9), bg=WHITE, fg=RED, justify="left",
                                      wraplength=330)
        self.details_error.pack(anchor="w")
        tk.Frame(right, bg=BORDER, height=1).pack(fill=tk.X, pady=8)

        # Price Summary
        tk.Label(right, text="Price summary", font=("Arial", 11, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
        summary = tk.Frame(right, bg=WHITE)
        summary.pack(fill=tk.X)
        summary.columnconfigure(1, weight=1)
        self.duration_title = tk.Label(summary, text="Rental duration", font=("Arial", 9), bg=WHITE, fg=MUTED)
        self.duration_title.grid(row=0, column=0, sticky="w")
        self.duration_value = tk.Label(summary, text="-", font=("Arial", 9), bg=WHITE, fg=TEXT)
        self.duration_value.grid(row=0, column=1, sticky="e")
        self.price_title = tk.Label(summary, text="Rental price", font=("Arial", 9), bg=WHITE, fg=MUTED)
        self.price_title.grid(row=1, column=0, sticky="w")
        self.price_value = tk.Label(summary, text="-", font=("Arial", 9), bg=WHITE, fg=TEXT)
        self.price_value.grid(row=1, column=1, sticky="e")
        tk.Label(summary, text=f"Deposit option ({payment_rules.DEPOSIT_PERCENT}%)", font=("Arial", 9), bg=WHITE,
                 fg=MUTED).grid(row=2, column=0, sticky="w")
        self.deposit_value = tk.Label(summary, text="-", font=("Arial", 9), bg=WHITE, fg=TEXT)
        self.deposit_value.grid(row=2, column=1, sticky="e")
        tk.Frame(right, bg=BORDER, height=1).pack(fill=tk.X, pady=6)
        total_row = tk.Frame(right, bg=WHITE)
        total_row.pack(fill=tk.X)
        tk.Label(total_row, text="Total cost", font=("Arial", 11, "bold"), bg=WHITE, fg=TEXT).pack(side=tk.LEFT)
        self.total_value = tk.Label(total_row, text="-", font=("Arial", 11, "bold"), bg=WHITE, fg=TEXT)
        self.total_value.pack(side=tk.RIGHT)

        tk.Button(right, text="Book Now", font=("Arial", 11, "bold"), bg=DARK, fg="white",
                  command=self.book_now).pack(fill=tk.X, ipady=3, pady=(12, 6))
        tk.Button(right, text="Back to Search", font=("Arial", 11), bg=WHITE, fg=TEXT,
                  command=self.back_to_search).pack(fill=tk.X, ipady=3)

        for entry in (self.details_pickup, self.details_return):
            entry.bind("<KeyRelease>", lambda event: self.update_price_summary())
        self.update_price_summary()

    def update_price_summary(self):
        rate = self.details_car["rate"]
        pickup_text = self.details_pickup.get().strip()
        return_text = self.details_return.get().strip()
        for label in (self.duration_value, self.price_value, self.total_value, self.deposit_value):
            label.config(text="-")
        self.price_title.config(text="Rental price")
        self.details_error.config(text="")
        if not pickup_text or not return_text:
            return

        errors, pickup, return_date = check_search(pickup_text, return_text, 0, 0)
        if errors:
            self.details_error.config(text="\n".join(errors))
            return
        days = booking_rules.rental_days(pickup, return_date)
        total = booking_rules.calculate_total(rate, pickup, return_date)
        self.duration_value.config(text=f"{days} days" if days != 1 else "1 day")
        self.price_title.config(text=f"Rental price (${rate:.2f} x {days} days)")
        self.price_value.config(text=f"${total:.2f}")
        self.deposit_value.config(text=f"${payment_rules.deposit_amount(total):.2f}")
        self.total_value.config(text=f"${total:.2f}")

    def book_now(self):
        """Book Now (RENT-01.2) - checks the form, creates the booking, then shows the confirmation page"""
        pickup_text = self.details_pickup.get().strip()
        return_text = self.details_return.get().strip()
        if not pickup_text or not return_text:
            self.details_error.config(text="Please enter both a pick-up date and a return date.")
            return
        pickup = read_date(pickup_text)
        return_date = read_date(return_text)
        if pickup is None or return_date is None:
            self.details_error.config(text="Enter dates as mm/dd/yyyy.")
            return

        # Same booking rules the backend uses (booking_rules.py)
        ok, message = booking_rules.validate_booking_dates(pickup, return_date)
        if not ok:
            self.details_error.config(text=message)
            return
        location = self.location_box.get()
        if location not in self.location_ids:
            self.details_error.config(text="Please choose a pick-up location.")
            return

        session = self.app.Session()
        try:
            success, message, reservation_id = create_booking(session, self.user["user_id"], self.details_car["id"],
                                                              pickup, return_date, self.location_ids[location])
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not create the booking:\n{e}", parent=self.window)
            return
        finally:
            session.close()

        if not success:
            # For example, someone else booked the car for those dates first
            self.details_error.config(text=message)
            return
        booking_ui.show_confirmation(self, reservation_id)

    def back_to_search(self):
        # Goes back to the browse page with the same filters as before.
        # The search runs again so a car that was just booked drops out of the results.
        if self.page is not None:
            self.page.destroy()
            self.page = None
            self.browse_frame.pack(fill=tk.BOTH, expand=True)
            self.window.title("DriveNow - Browse Cars")
            self.search()
