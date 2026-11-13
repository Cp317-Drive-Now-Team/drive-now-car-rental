import tkinter as tk
from tkinter import messagebox, ttk
from booking_service import get_my_bookings, cancel_booking, refund_preview
from payment_service import get_payment_options, make_payment, get_receipt
import payment_rules
import cancellation_rules

# Colours (greyscale to match the wireframes)
WHITE = "#FFFFFF"
GREY = "#E6E6E6"
BORDER = "#D0D0D0"
DARK = "#3F3F3F"
TEXT = "#1F1F1F"
MUTED = "#6B6B6B"
RED = "#B00020"
GREEN = "#1E7B34"


def money(amount):
    return f"${amount:,.2f}"


def nice_date(d):
    return d.strftime("%b %d, %Y")  # e.g. Nov 22, 2026


def info_rows(parent, rows):
    """Shows a list of (label, value) pairs as two lined-up columns"""
    box = tk.Frame(parent, bg=WHITE)
    box.pack(fill=tk.X)
    box.columnconfigure(1, weight=1)
    for i, (label, value) in enumerate(rows):
        tk.Label(box, text=label, font=("Arial", 11), bg=WHITE, fg=MUTED).grid(row=i, column=0, sticky="w", pady=2)
        tk.Label(box, text=value, font=("Arial", 11), bg=WHITE, fg=TEXT).grid(row=i, column=1, sticky="e", pady=2)
    return box


def page_box(page, width=560):
    """White box with a border in the middle of the page, used by the confirmation, payment and receipt pages"""
    box = tk.Frame(page, bg=WHITE, padx=25, pady=20, highlightthickness=1, highlightbackground=BORDER, width=width)
    box.pack(pady=(10, 0))
    return box


def show_confirmation(browse, reservation_id):
    """Booking confirmation page (RENT-01.2). The booking is saved as Pending until it is paid."""
    session = browse.app.Session()
    try:
        info = get_payment_options(session, browse.user["user_id"], reservation_id)
    finally:
        session.close()
    if info is None:
        messagebox.showerror("Error", "Booking not found.", parent=browse.window)
        return

    page = browse.new_page("Booking Confirmed")
    tk.Label(page, text="Your car is reserved!", font=("Arial", 20, "bold"), bg=WHITE, fg=TEXT).pack()
    tk.Label(page, text="Pay now to confirm your booking. Unpaid bookings can be paid later from My Bookings.",
             font=("Arial", 10), bg=WHITE, fg=MUTED).pack(pady=(2, 10))

    box = page_box(page)
    tk.Label(box, text=f"Booking #{info['id']}", font=("Arial", 14, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
    tk.Label(box, text="Status: Pending payment", font=("Arial", 10), bg=WHITE, fg=MUTED).pack(anchor="w", pady=(0, 10))
    days = (info["end"] - info["start"]).days
    info_rows(box, [
        ("Car", info["car"]),
        ("Pick-up date", nice_date(info["start"])),
        ("Return date", nice_date(info["end"])),
        ("Rental duration", f"{days} days" if days != 1 else "1 day"),
        ("Pick-up location", info["location"]),
    ])
    tk.Frame(box, bg=BORDER, height=1).pack(fill=tk.X, pady=8)
    info_rows(box, [("Total cost", money(info["total"]))])

    tk.Button(box, text="Continue to Payment", font=("Arial", 11, "bold"), bg=DARK, fg="white",
              command=lambda: show_payment(browse, reservation_id)).pack(fill=tk.X, ipady=3, pady=(14, 6))
    tk.Button(box, text="Pay Later (go to My Bookings)", font=("Arial", 11), bg=WHITE, fg=TEXT,
              command=lambda: show_my_bookings(browse)).pack(fill=tk.X, ipady=3)


def show_payment(browse, reservation_id):
    """Payment page (PAY-01.2) with the deposit option and remaining balance (PAY-02.2)"""
    session = browse.app.Session()
    try:
        info = get_payment_options(session, browse.user["user_id"], reservation_id)
    finally:
        session.close()
    if info is None:
        messagebox.showerror("Error", "Booking not found.", parent=browse.window)
        return

    page = browse.new_page("Payment")
    tk.Label(page, text="Payment", font=("Arial", 20, "bold"), bg=WHITE, fg=TEXT).pack()
    tk.Label(page, text=f"Booking #{info['id']}  |  {info['car']}  |  {nice_date(info['start'])} to {nice_date(info['end'])}",
             font=("Arial", 10), bg=WHITE, fg=MUTED).pack(pady=(2, 6))

    box = page_box(page)

    # Amounts
    tk.Label(box, text="Amount", font=("Arial", 12, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
    info_rows(box, [("Total cost", money(info["total"])), ("Already paid", money(info["paid"])),
                    ("Balance", money(info["balance"]))])

    # Payment option - pay in full or pay a deposit (only if nothing has been paid yet)
    tk.Label(box, text="How would you like to pay?", font=("Arial", 12, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w", pady=(12, 2))
    choice = tk.StringVar(value="Full Payment")
    full_text = "Pay the remaining balance" if info["paid"] > 0 else "Pay in full"
    tk.Radiobutton(box, text=f"{full_text} ({money(info['balance'])})", variable=choice, value="Full Payment",
                   font=("Arial", 11), bg=WHITE, fg=TEXT, activebackground=WHITE, highlightthickness=0,
                   command=lambda: update_amounts()).pack(anchor="w")
    if info["deposit_allowed"]:
        tk.Radiobutton(box, text=f"Pay a {payment_rules.DEPOSIT_PERCENT}% deposit now ({money(info['deposit'])})",
                       variable=choice, value="Deposit", font=("Arial", 11), bg=WHITE, fg=TEXT,
                       activebackground=WHITE, highlightthickness=0, command=lambda: update_amounts()).pack(anchor="w")

    amounts = tk.Frame(box, bg="#F2F2F2", padx=12, pady=8)
    amounts.pack(fill=tk.X, pady=(8, 0))
    amounts.columnconfigure(1, weight=1)
    tk.Label(amounts, text="You pay today", font=("Arial", 11, "bold"), bg="#F2F2F2", fg=TEXT).grid(row=0, column=0, sticky="w")
    pay_today = tk.Label(amounts, text="", font=("Arial", 11, "bold"), bg="#F2F2F2", fg=TEXT)
    pay_today.grid(row=0, column=1, sticky="e")
    tk.Label(amounts, text="Remaining balance after this", font=("Arial", 10), bg="#F2F2F2", fg=MUTED).grid(row=1, column=0, sticky="w")
    remaining = tk.Label(amounts, text="", font=("Arial", 10), bg="#F2F2F2", fg=TEXT)
    remaining.grid(row=1, column=1, sticky="e")

    def update_amounts():
        amount = info["deposit"] if choice.get() == "Deposit" else info["balance"]
        pay_today.config(text=money(amount))
        remaining.config(text=money(info["balance"] - amount))
    update_amounts()

    # Card details (only checked and sent to the test service, never saved)
    tk.Label(box, text="Card details", font=("Arial", 12, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w", pady=(12, 2))
    tk.Label(box, text="Test mode: use 4242 4242 4242 4242. The card 4000 0000 0000 0002 is always declined.",
             font=("Arial", 9), bg=WHITE, fg=MUTED, wraplength=500, justify="left").pack(anchor="w")
    tk.Label(box, text="Card number", font=("Arial", 10), bg=WHITE, fg=TEXT).pack(anchor="w", pady=(6, 0))
    card_entry = tk.Entry(box, font=("Arial", 11), relief="solid", bd=1)
    card_entry.pack(fill=tk.X, ipady=3)
    row = tk.Frame(box, bg=WHITE)
    row.pack(fill=tk.X, pady=(6, 0))
    row.columnconfigure(0, weight=1)
    row.columnconfigure(1, weight=1)
    tk.Label(row, text="Expiry (MM/YY)", font=("Arial", 10), bg=WHITE, fg=TEXT).grid(row=0, column=0, sticky="w")
    tk.Label(row, text="Security code", font=("Arial", 10), bg=WHITE, fg=TEXT).grid(row=0, column=1, sticky="w", padx=(10, 0))
    expiry_entry = tk.Entry(row, font=("Arial", 11), relief="solid", bd=1)
    expiry_entry.grid(row=1, column=0, sticky="ew", ipady=3)
    cvv_entry = tk.Entry(row, font=("Arial", 11), relief="solid", bd=1, show="*")
    cvv_entry.grid(row=1, column=1, sticky="ew", ipady=3, padx=(10, 0))

    message = tk.Label(box, text="", font=("Arial", 10, "bold"), bg=WHITE, fg=RED, wraplength=500, justify="left")
    message.pack(anchor="w", pady=(8, 0))

    def pay():
        message.config(text="", fg=RED)
        session = browse.app.Session()
        try:
            success, msg, payment_id = make_payment(session, browse.user["user_id"], reservation_id, choice.get(),
                                                    card_entry.get().strip(), expiry_entry.get().strip(),
                                                    cvv_entry.get().strip())
        except Exception as e:
            messagebox.showerror("Error", f"Could not process the payment:\n{e}", parent=browse.window)
            return
        finally:
            session.close()

        if success:
            show_receipt(browse, payment_id=payment_id, just_paid=True)
        else:
            # Clear failure message. The security code is cleared so it doesn't stay on screen.
            message.config(text=msg)
            cvv_entry.delete(0, tk.END)

    tk.Button(box, text="Pay Now", font=("Arial", 11, "bold"), bg=DARK, fg="white",
              command=pay).pack(fill=tk.X, ipady=3, pady=(8, 6))
    tk.Button(box, text="Back to My Bookings", font=("Arial", 11), bg=WHITE, fg=TEXT,
              command=lambda: show_my_bookings(browse)).pack(fill=tk.X, ipady=3)


def show_receipt(browse, payment_id=None, reservation_id=None, just_paid=False):
    """Receipt page (PAY-03.1): booking, car, dates and amount paid"""
    session = browse.app.Session()
    try:
        receipt = get_receipt(session, browse.user["user_id"], payment_id=payment_id, reservation_id=reservation_id)
    finally:
        session.close()
    if receipt is None:
        messagebox.showinfo("Receipt", "There is no payment on this booking yet.", parent=browse.window)
        return

    page = browse.new_page("Receipt")
    if just_paid:
        tk.Label(page, text="Payment successful!", font=("Arial", 20, "bold"), bg=WHITE, fg=GREEN).pack()
        tk.Label(page, text="Your booking is confirmed. Here is your receipt.", font=("Arial", 10), bg=WHITE,
                 fg=MUTED).pack(pady=(2, 6))
    else:
        tk.Label(page, text="Receipt", font=("Arial", 20, "bold"), bg=WHITE, fg=TEXT).pack(pady=(0, 6))

    box = page_box(page)
    top = tk.Frame(box, bg=WHITE)
    top.pack(fill=tk.X)
    tk.Label(top, text="Drive Now Car Rentals", font=("Arial", 13, "bold"), bg=WHITE, fg=TEXT).pack(side=tk.LEFT)
    tk.Label(top, text=f"Receipt #{receipt['receipt_no']}", font=("Arial", 11), bg=WHITE, fg=MUTED).pack(side=tk.RIGHT)
    paid_on = receipt["date"].strftime("%b %d, %Y") if receipt["date"] else ""
    tk.Label(box, text=f"Paid on {paid_on}", font=("Arial", 9), bg=WHITE, fg=MUTED).pack(anchor="w", pady=(0, 8))

    tk.Label(box, text="Booking", font=("Arial", 12, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
    info_rows(box, [
        ("Booking number", f"#{receipt['booking_id']}"),
        ("Car", receipt["car"]),
        ("Pick-up date", nice_date(receipt["start"])),
        ("Return date", nice_date(receipt["end"])),
        ("Pick-up location", receipt["location"]),
    ])
    tk.Frame(box, bg=BORDER, height=1).pack(fill=tk.X, pady=8)
    tk.Label(box, text="Payment", font=("Arial", 12, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
    info_rows(box, [
        ("Payment type", receipt["payment_type"]),
        ("Payment method", receipt["method"]),
        ("Reference number", receipt["reference"]),
        ("Total cost", money(receipt["total"])),
        ("Paid so far", money(receipt["paid_so_far"])),
        ("Remaining balance", money(receipt["balance"])),
    ])
    tk.Frame(box, bg=BORDER, height=1).pack(fill=tk.X, pady=8)
    paid_row = tk.Frame(box, bg=WHITE)
    paid_row.pack(fill=tk.X)
    tk.Label(paid_row, text="Amount paid", font=("Arial", 13, "bold"), bg=WHITE, fg=TEXT).pack(side=tk.LEFT)
    tk.Label(paid_row, text=money(receipt["amount"]), font=("Arial", 13, "bold"), bg=WHITE, fg=TEXT).pack(side=tk.RIGHT)

    tk.Button(box, text="Go to My Bookings", font=("Arial", 11, "bold"), bg=DARK, fg="white",
              command=lambda: show_my_bookings(browse)).pack(fill=tk.X, ipady=3, pady=(14, 6))
    tk.Button(box, text="Back to Search", font=("Arial", 11), bg=WHITE, fg=TEXT,
              command=browse.back_to_search).pack(fill=tk.X, ipady=3)


def show_my_bookings(browse):
    """
    My Bookings page (basic version for RENT-02.2). Upcoming bookings have a Cancel button.
    The full rental history page is ACC-03 in Sprint 3.
    """
    session = browse.app.Session()
    try:
        bookings = get_my_bookings(session, browse.user["user_id"])
    except Exception as e:
        messagebox.showerror("Database Error", f"Could not load your bookings:\n{e}", parent=browse.window)
        return
    finally:
        session.close()

    page = browse.new_page("My Bookings")
    tk.Label(page, text="My Bookings", font=("Arial", 20, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
    tk.Label(page, text="Select a booking to pay, view its receipt, or cancel it.", font=("Arial", 9),
             bg=WHITE, fg=MUTED).pack(anchor="w", pady=(0, 10))

    columns = [("id", "Booking", 70), ("car", "Car", 200), ("start", "Pick-up", 110), ("end", "Return", 110),
               ("total", "Total", 90), ("paid", "Paid", 90), ("balance", "Balance", 90), ("status", "Status", 130)]

    def make_table(parent, rows, height):
        table = ttk.Treeview(parent, columns=[c[0] for c in columns], show="headings", height=height,
                             selectmode="browse")
        for key, title, width in columns:
            table.heading(key, text=title)
            table.column(key, width=width, anchor="w" if key == "car" else "center")
        for b in rows:
            status = "Awaiting payment" if b["status"] == 'Pending' else b["status"]
            table.insert("", tk.END, iid=str(b["id"]), values=(
                f"#{b['id']}", b["car"], nice_date(b["start"]), nice_date(b["end"]),
                money(b["total"]), money(b["paid"]), money(b["balance"]), status))
        table.pack(fill=tk.X)
        return table

    upcoming = [b for b in bookings if b["upcoming"]]
    others = [b for b in bookings if not b["upcoming"]]

    # Upcoming bookings
    tk.Label(page, text="Upcoming", font=("Arial", 13, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
    if upcoming:
        table = make_table(page, upcoming, min(len(upcoming), 6))
    else:
        table = None
        tk.Label(page, text="You have no upcoming bookings.", font=("Arial", 10), bg=WHITE,
                 fg=MUTED).pack(anchor="w", pady=4)

    message = tk.Label(page, text="", font=("Arial", 10), bg=WHITE, fg=TEXT, wraplength=900, justify="left")
    message.pack(anchor="w", pady=(6, 0))

    def selected():
        if table is None or not table.selection():
            message.config(text="Select a booking in the table first.", fg=RED)
            return None
        return int(table.selection()[0])

    def pay_selected():
        booking_id = selected()
        if booking_id is None:
            return
        booking = next(b for b in upcoming if b["id"] == booking_id)
        if booking["balance"] <= 0:
            message.config(text="This booking is already paid in full.", fg=RED)
            return
        show_payment(browse, booking_id)

    def receipt_selected():
        booking_id = selected()
        if booking_id is not None:
            show_receipt(browse, reservation_id=booking_id)

    def cancel_selected():
        """Cancel button with a confirmation prompt (RENT-02.2). Shows the refund before the customer confirms."""
        booking_id = selected()
        if booking_id is None:
            return
        session = browse.app.Session()
        try:
            refund = refund_preview(session, browse.user["user_id"], booking_id)
        finally:
            session.close()

        question = f"Are you sure you want to cancel booking #{booking_id}?"
        if refund > 0:
            question += (f"\n\nYou will get {money(refund)} back. Cancelling less than "
                         f"{cancellation_rules.FULL_REFUND_DAYS_BEFORE} days before pick-up only refunds "
                         f"{cancellation_rules.LATE_REFUND_PERCENT}% of what you paid.")
        if not messagebox.askyesno("Cancel Booking", question, parent=browse.window):
            return

        session = browse.app.Session()
        try:
            success, msg = cancel_booking(session, browse.user["user_id"], booking_id)
        finally:
            session.close()
        if success:
            show_my_bookings(browse)  # reload the page so the booking moves to Past and Cancelled
            browse.my_bookings_message.config(text=msg, fg=GREEN)
        else:
            message.config(text=msg, fg=RED)

    buttons = tk.Frame(page, bg=WHITE)
    buttons.pack(anchor="w", pady=(6, 14))
    tk.Button(buttons, text="Pay / Pay Balance", font=("Arial", 11), bg=DARK, fg="white",
              command=pay_selected).pack(side=tk.LEFT, padx=(0, 8), ipady=2)
    tk.Button(buttons, text="View Receipt", font=("Arial", 11), bg=WHITE, fg=TEXT,
              command=receipt_selected).pack(side=tk.LEFT, padx=(0, 8), ipady=2)
    tk.Button(buttons, text="Cancel Booking", font=("Arial", 11), bg=WHITE, fg=RED,
              command=cancel_selected).pack(side=tk.LEFT, ipady=2)

    # Past and cancelled bookings (read only for now)
    tk.Label(page, text="Past and Cancelled", font=("Arial", 13, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
    if others:
        make_table(page, others, min(len(others), 5))
    else:
        tk.Label(page, text="Nothing here yet.", font=("Arial", 10), bg=WHITE, fg=MUTED).pack(anchor="w", pady=4)

    tk.Button(page, text="Back to Search", font=("Arial", 11), bg=WHITE, fg=TEXT,
              command=browse.back_to_search).pack(anchor="w", pady=(14, 0), ipady=2)

    # Saved so cancel_selected can show its message after the page reloads
    browse.my_bookings_message = message
