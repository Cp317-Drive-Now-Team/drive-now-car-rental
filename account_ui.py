import tkinter as tk
from tkinter import ttk
from profile_service import get_profile, update_profile, change_password, check_profile_fields
from booking_service import get_rental_history
from notification_service import get_my_emails
from booking_ui import show_receipt
import rental_status

# Colours (greyscale to match the wireframes)
WHITE = "#FFFFFF"
GREY = "#E6E6E6"
BORDER = "#D0D0D0"
DARK = "#3F3F3F"
TEXT = "#1F1F1F"
MUTED = "#595959"
RED = "#B00020"
GREEN = "#1E7B34"


def money(amount):
    return f"${amount:,.2f}"


def nice_date(d):
    return d.strftime("%b %d, %Y")  # e.g. Nov 22, 2026


def show_my_account(browse, open_tab=0):
    """Builds the My Account page inside the customer's window"""
    page = browse.new_page("My Account")
    tk.Label(page, text="My Account", font=("Arial", 20, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
    tk.Label(page, text="Manage your details, see your rental history, and read the emails we've sent you.",
             font=("Arial", 9), bg=WHITE, fg=MUTED).pack(anchor="w", pady=(0, 10))

    tabs = ttk.Notebook(page)
    tabs.pack(fill=tk.BOTH, expand=True)
    tabs.enable_traversal()  # Ctrl+Tab switches tabs with the keyboard (UI-01)

    profile_tab = tk.Frame(tabs, bg=WHITE, padx=15, pady=12)
    history_tab = tk.Frame(tabs, bg=WHITE, padx=15, pady=12)
    emails_tab = tk.Frame(tabs, bg=WHITE, padx=15, pady=12)
    tabs.add(profile_tab, text="  Profile  ")
    tabs.add(history_tab, text="  Rental History  ")
    tabs.add(emails_tab, text="  Emails  ")

    build_profile_tab(browse, profile_tab)
    build_history_tab(browse, history_tab)
    build_emails_tab(browse, emails_tab)
    tabs.select(open_tab)


# ---------------- PROFILE (ACC-01) ----------------
def build_profile_tab(browse, tab):
    session = browse.app.Session()
    try:
        profile = get_profile(session, browse.user["user_id"])
    finally:
        session.close()
    if profile is None:
        tk.Label(tab, text="Could not load your account.", font=("Arial", 11), bg=WHITE, fg=RED).pack(anchor="w")
        return

    columns = tk.Frame(tab, bg=WHITE)
    columns.pack(fill=tk.BOTH, expand=True)
    columns.columnconfigure(0, weight=3)
    columns.columnconfigure(1, weight=2)

    # Left side - your details
    left = tk.Frame(columns, bg=WHITE, padx=20, pady=15, highlightthickness=1, highlightbackground=BORDER,
                    highlightcolor=BORDER)
    left.grid(row=0, column=0, sticky="new", padx=(0, 20))
    tk.Label(left, text="Your details", font=("Arial", 14, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
    if profile["member_since"]:
        tk.Label(left, text=f"Member since {nice_date(profile['member_since'])}", font=("Arial", 9),
                 bg=WHITE, fg=MUTED).pack(anchor="w")
    status = tk.Label(left, text="", font=("Arial", 10, "bold"), bg=WHITE, fg=GREEN, wraplength=480,
                      justify="left")
    status.pack(anchor="w", pady=(4, 4))

    form = tk.Frame(left, bg=WHITE)
    form.pack(fill=tk.X)
    form.columnconfigure(0, weight=1, uniform="col")
    form.columnconfigure(1, weight=1, uniform="col")
    # (field name, label, row, column)
    fields = [
        ("first_name", "First Name *", 0, 0),
        ("last_name", "Last Name *", 0, 1),
        ("email", "Email *", 3, 0),
        ("phone", "Phone Number *", 3, 1),
        ("licence", "Driver's Licence Number", 6, 0),
    ]
    entries = {}
    errors = {}
    for name, label, row, col in fields:
        pad = (0, 10) if col == 0 else (10, 0)
        tk.Label(form, text=label, font=("Arial", 11), bg=WHITE, fg=TEXT).grid(row=row, column=col, sticky="w", padx=pad)
        entry = tk.Entry(form, font=("Arial", 11), relief="solid", bd=1, disabledbackground="#F2F2F2",
                         disabledforeground=TEXT)
        entry.grid(row=row + 1, column=col, sticky="ew", ipady=3, padx=pad)
        error = tk.Label(form, text="", font=("Arial", 9), bg=WHITE, fg=RED, wraplength=230, justify="left")
        error.grid(row=row + 2, column=col, sticky="w", padx=pad, pady=(0, 4))
        entries[name] = entry
        errors[name] = error

    def fill_in(values):
        for name, entry in entries.items():
            entry.config(state=tk.NORMAL)
            entry.delete(0, tk.END)
            entry.insert(0, values[name])
            entry.config(state=tk.DISABLED)  # read only until Edit Details is clicked
    fill_in(profile)

    buttons = tk.Frame(left, bg=WHITE)
    buttons.pack(anchor="w", pady=(8, 0))
    edit_btn = tk.Button(buttons, text="Edit Details", font=("Arial", 11, "bold"), bg=DARK, fg="white")
    save_btn = tk.Button(buttons, text="Save Changes", font=("Arial", 11, "bold"), bg=DARK, fg="white")
    cancel_btn = tk.Button(buttons, text="Cancel", font=("Arial", 11), bg=WHITE, fg=TEXT)

    def start_editing():
        status.config(text="")
        for entry in entries.values():
            entry.config(state=tk.NORMAL)
        edit_btn.pack_forget()
        save_btn.pack(side=tk.LEFT, padx=(0, 8), ipady=2)
        cancel_btn.pack(side=tk.LEFT, ipady=2)
        entries["first_name"].focus_set()

    def stop_editing():
        for label in errors.values():
            label.config(text="")
        fill_in(profile)
        save_btn.pack_forget()
        cancel_btn.pack_forget()
        edit_btn.pack(side=tk.LEFT, ipady=2)

    def save():
        values = {name: entry.get().strip() for name, entry in entries.items()}
        for label in errors.values():
            label.config(text="")
        # Check the form first so the customer sees every problem at once
        problems = check_profile_fields(values["first_name"], values["last_name"], values["email"], values["phone"])
        if not problems:
            session = browse.app.Session()
            try:
                success, message, problems = update_profile(session, browse.user["user_id"], values["first_name"],
                                                            values["last_name"], values["email"], values["phone"],
                                                            values["licence"])
                if success:
                    profile.update(get_profile(session, browse.user["user_id"]))
            finally:
                session.close()
            if success:
                stop_editing()
                browse.user["first_name"] = profile["first_name"]
                status.config(text=message + " If you changed your email, use the new one to sign in next time.",
                              fg=GREEN)
                return
            if not problems:
                status.config(text=message, fg=RED)
        for name, message in problems.items():
            errors[name].config(text=message)
        status.config(text="Please fix the highlighted fields.", fg=RED)

    edit_btn.config(command=start_editing)
    save_btn.config(command=save)
    cancel_btn.config(command=lambda: (stop_editing(), status.config(text="")))
    edit_btn.pack(side=tk.LEFT, ipady=2)

    # Right side - change password
    right = tk.Frame(columns, bg=WHITE, padx=20, pady=15, highlightthickness=1, highlightbackground=BORDER,
                     highlightcolor=BORDER)
    right.grid(row=0, column=1, sticky="new")
    tk.Label(right, text="Change password", font=("Arial", 14, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
    password_status = tk.Label(right, text="", font=("Arial", 10, "bold"), bg=WHITE, fg=GREEN, wraplength=300,
                               justify="left")
    password_status.pack(anchor="w", pady=(4, 4))
    password_entries = {}
    password_errors = {}
    for name, label in (("current", "Current password"), ("new", "New password (8+ characters)"),
                        ("confirm", "Confirm new password")):
        tk.Label(right, text=label, font=("Arial", 11), bg=WHITE, fg=TEXT).pack(anchor="w")
        entry = tk.Entry(right, font=("Arial", 11), relief="solid", bd=1, show="*")
        entry.pack(fill=tk.X, ipady=3)
        error = tk.Label(right, text="", font=("Arial", 9), bg=WHITE, fg=RED)
        error.pack(anchor="w", pady=(0, 4))
        password_entries[name] = entry
        password_errors[name] = error

    def save_password():
        for label in password_errors.values():
            label.config(text="")
        session = browse.app.Session()
        try:
            success, message, problems = change_password(session, browse.user["user_id"],
                                                         password_entries["current"].get(),
                                                         password_entries["new"].get(),
                                                         password_entries["confirm"].get())
        finally:
            session.close()
        for name, error in problems.items():
            password_errors[name].config(text=error)
        password_status.config(text=message, fg=GREEN if success else RED)
        if success:
            for entry in password_entries.values():
                entry.delete(0, tk.END)

    tk.Button(right, text="Change Password", font=("Arial", 11), bg=WHITE, fg=TEXT,
              command=save_password).pack(fill=tk.X, ipady=2, pady=(6, 0))


# ---------------- RENTAL HISTORY (ACC-03) ----------------
def build_history_tab(browse, tab):
    session = browse.app.Session()
    try:
        history = get_rental_history(session, browse.user["user_id"])
    except Exception as e:
        tk.Label(tab, text=f"Could not load your rental history: {e}", font=("Arial", 11), bg=WHITE,
                 fg=RED).pack(anchor="w")
        return
    finally:
        session.close()

    # Summary boxes
    boxes = tk.Frame(tab, bg=WHITE)
    boxes.pack(fill=tk.X, pady=(0, 10))
    completed = [h for h in history if h["status"] == "Completed"]
    upcoming = [h for h in history if h["status"] in ("Upcoming", "Active")]
    summary = [("Total bookings", str(len(history))), ("Completed trips", str(len(completed))),
               ("Upcoming", str(len(upcoming))), ("Total spent", money(sum(h["paid"] for h in history)))]
    for col, (title, value) in enumerate(summary):
        boxes.columnconfigure(col, weight=1, uniform="box")
        box = tk.Frame(boxes, bg=GREY, padx=14, pady=8)
        box.grid(row=0, column=col, sticky="nsew", padx=(0, 10) if col < 3 else 0)
        tk.Label(box, text=title, font=("Arial", 10), bg=GREY, fg=MUTED).pack(anchor="w")
        tk.Label(box, text=value, font=("Arial", 16, "bold"), bg=GREY, fg=TEXT).pack(anchor="w")

    # Status filter
    top = tk.Frame(tab, bg=WHITE)
    top.pack(fill=tk.X, pady=(0, 6))
    tk.Label(top, text="Show", font=("Arial", 11), bg=WHITE, fg=TEXT).pack(side=tk.LEFT)
    status_filter = ttk.Combobox(top, values=["All"] + list(rental_status.RENTAL_STATUSES), state="readonly", width=14)
    status_filter.set("All")
    status_filter.pack(side=tk.LEFT, padx=(6, 0))
    count = tk.Label(top, text="", font=("Arial", 10), bg=WHITE, fg=MUTED)
    count.pack(side=tk.LEFT, padx=(12, 0))

    # Bookings table
    columns = [("id", "Booking", 70), ("car", "Car", 190), ("start", "Pick-up", 105), ("end", "Return", 105),
               ("days", "Days", 50), ("total", "Total", 90), ("paid", "Paid", 90), ("status", "Status", 100)]
    table = ttk.Treeview(tab, columns=[c[0] for c in columns], show="headings", height=7, selectmode="browse")
    for key, title, width in columns:
        table.heading(key, text=title)
        table.column(key, width=width, anchor="w" if key == "car" else "center")
    table.pack(fill=tk.X)

    if not history:
        tk.Label(tab, text="You haven't made any bookings yet.", font=("Arial", 10), bg=WHITE,
                 fg=MUTED).pack(anchor="w", pady=4)

    # Payments for the selected booking
    tk.Label(tab, text="Payments for the selected booking", font=("Arial", 12, "bold"), bg=WHITE,
             fg=TEXT).pack(anchor="w", pady=(12, 4))
    pay_columns = [("receipt", "Receipt", 80), ("date", "Date", 120), ("type", "Type", 120),
                   ("amount", "Amount", 100), ("status", "Status", 100)]
    payments = ttk.Treeview(tab, columns=[c[0] for c in pay_columns], show="headings", height=4,
                            selectmode="browse")
    for key, title, width in pay_columns:
        payments.heading(key, text=title)
        payments.column(key, width=width, anchor="center")
    payments.pack(fill=tk.X)

    message = tk.Label(tab, text="", font=("Arial", 10), bg=WHITE, fg=RED)
    message.pack(anchor="w", pady=(4, 0))

    def load_table():
        table.delete(*table.get_children())
        payments.delete(*payments.get_children())
        shown = [h for h in history if status_filter.get() in ("All", h["status"])]
        for h in shown:
            table.insert("", tk.END, iid=str(h["id"]), values=(
                f"#{h['id']}", h["car"], nice_date(h["start"]), nice_date(h["end"]), h["days"],
                money(h["total"]), money(h["paid"]), h["status"]))
        count.config(text=f"{len(shown)} booking(s)")

    def show_payments(event=None):
        payments.delete(*payments.get_children())
        message.config(text="")
        selected = table.selection()
        if not selected:
            return
        booking = next(h for h in history if h["id"] == int(selected[0]))
        for p in booking["payments"]:
            payments.insert("", tk.END, iid=str(p["receipt_no"]), values=(
                f"#{p['receipt_no']}", p["date"].strftime("%b %d, %Y") if p["date"] else "", p["type"],
                money(p["amount"]), p["status"]))
        if not booking["payments"]:
            message.config(text="No payments on this booking yet.", fg=MUTED)

    def view_receipt():
        selected = payments.selection()
        if not selected:
            message.config(text="Select a payment in the table first.", fg=RED)
            return
        row = payments.item(selected[0])["values"]
        if row[4] == "Failed":
            message.config(text="There's no receipt for a payment that was declined.", fg=RED)
            return
        show_receipt(browse, payment_id=int(selected[0]))

    status_filter.bind("<<ComboboxSelected>>", lambda event: load_table())
    table.bind("<<TreeviewSelect>>", show_payments)
    tk.Button(tab, text="View Receipt", font=("Arial", 11), bg=DARK, fg="white",
              command=view_receipt).pack(anchor="w", pady=(4, 0), ipady=2)
    load_table()


# ---------------- EMAILS (NOTIF-01) ----------------
def build_emails_tab(browse, tab):
    from auth_service import app_session
    email_address = app_session.user.email if app_session.is_logged_in else ""
    emails = get_my_emails(email_address)

    tk.Label(tab, text=f"Booking emails sent to {email_address}", font=("Arial", 12, "bold"), bg=WHITE,
             fg=TEXT).pack(anchor="w")
    tk.Label(tab, text="You get an email whenever you make, change or cancel a booking.", font=("Arial", 9),
             bg=WHITE, fg=MUTED).pack(anchor="w", pady=(0, 8))

    if not emails:
        tk.Label(tab, text="No emails yet.", font=("Arial", 10), bg=WHITE, fg=MUTED).pack(anchor="w")
        return

    columns = tk.Frame(tab, bg=WHITE)
    columns.pack(fill=tk.BOTH, expand=True)
    inbox = ttk.Treeview(columns, columns=("date", "subject"), show="headings", selectmode="browse")
    inbox.heading("date", text="Date")
    inbox.heading("subject", text="Subject")
    inbox.column("date", width=175, anchor="w")
    inbox.column("subject", width=320, anchor="w")
    inbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    body = tk.Text(columns, font=("Courier", 11), bg="#F7F7F7", fg=TEXT, relief="solid", bd=1, wrap="word",
                   width=52, padx=10, pady=8)
    body.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(12, 0))

    for i, e in enumerate(emails):
        inbox.insert("", tk.END, iid=str(i), values=(e["date"], e["subject"]))

    def open_email(event=None):
        selected = inbox.selection()
        if not selected:
            return
        body.config(state=tk.NORMAL)
        body.delete("1.0", tk.END)
        body.insert("1.0", emails[int(selected[0])]["body"])
        body.config(state=tk.DISABLED)  # read only

    inbox.bind("<<TreeviewSelect>>", open_email)
    inbox.selection_set("0")  # open the newest email
    open_email()
