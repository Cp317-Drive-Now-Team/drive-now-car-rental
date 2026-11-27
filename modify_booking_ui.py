# Author: Dheeraj Bashal (Student ID: 169057697) - Group 22, CP317A
"""RENT-03  Modify Booking page. Opened from the Modify Booking button on My Bookings (booking_ui.py)."""
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from booking_modify_service import preview_change, modify_booking
from notification_service import send_booking_email  # added by Sadaf (NOTIF-01)
from booking_ui import (WHITE, BORDER, DARK, TEXT, MUTED, RED, GREEN, money, nice_date,
                        info_rows, page_box, show_my_bookings)


def read_date(text):
    # Accepts mm/dd/yyyy like the rest of the app, or yyyy-mm-dd
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def show_modify(browse, reservation_id):
    """Page where a customer picks new dates for an upcoming booking and sees the new total before confirming."""
    from booking_service import get_my_bookings
    session = browse.app.Session()
    try:
        booking = next((b for b in get_my_bookings(session, browse.user["user_id"]) if b["id"] == reservation_id), None)
    finally:
        session.close()
    if booking is None or not booking["upcoming"]:
        messagebox.showinfo("Modify Booking", "Only upcoming bookings can be changed.", parent=browse.window)
        return

    page = browse.new_page("Modify Booking")
    tk.Label(page, text="Modify Booking", font=("Arial", 20, "bold"), bg=WHITE, fg=TEXT).pack()
    tk.Label(page, text="Choose new dates. The change is only saved if the car is free on those dates.",
             font=("Arial", 10), bg=WHITE, fg=MUTED).pack(pady=(2, 6))
    box = page_box(page)

    tk.Label(box, text=f"Booking #{booking['id']}", font=("Arial", 14, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w")
    info_rows(box, [
        ("Car", booking["car"]),
        ("Current pick-up date", nice_date(booking["start"])),
        ("Current return date", nice_date(booking["end"])),
        ("Current total", money(booking["total"])),
        ("Paid so far", money(booking["paid"])),
    ])
    tk.Frame(box, bg=BORDER, height=1).pack(fill=tk.X, pady=8)

    tk.Label(box, text="New pick-up date (mm/dd/yyyy)", font=("Arial", 10), bg=WHITE, fg=TEXT).pack(anchor="w")
    start_entry = tk.Entry(box, font=("Arial", 11), relief="solid", bd=1)
    start_entry.pack(fill=tk.X, ipady=3)
    start_entry.insert(0, booking["start"].strftime("%m/%d/%Y"))
    tk.Label(box, text="New return date (mm/dd/yyyy)", font=("Arial", 10), bg=WHITE, fg=TEXT).pack(anchor="w", pady=(6, 0))
    end_entry = tk.Entry(box, font=("Arial", 11), relief="solid", bd=1)
    end_entry.pack(fill=tk.X, ipady=3)
    end_entry.insert(0, booking["end"].strftime("%m/%d/%Y"))

    summary = tk.Frame(box, bg="#F2F2F2", padx=12, pady=8)
    summary.pack(fill=tk.X, pady=(10, 0))
    summary.columnconfigure(1, weight=1)
    labels = {}
    for i, (key, text) in enumerate([("new_total", "New total"), ("difference", "Change in price"),
                                     ("note", "After this change")]):
        tk.Label(summary, text=text, font=("Arial", 10, "bold" if key == "new_total" else "normal"),
                 bg="#F2F2F2", fg=TEXT).grid(row=i, column=0, sticky="w")
        labels[key] = tk.Label(summary, text="-", font=("Arial", 10, "bold" if key == "new_total" else "normal"),
                               bg="#F2F2F2", fg=TEXT, wraplength=300, justify="right")
        labels[key].grid(row=i, column=1, sticky="e", padx=(24, 0))

    message = tk.Label(box, text="", font=("Arial", 10, "bold"), bg=WHITE, fg=RED, wraplength=500, justify="left")
    message.pack(anchor="w", pady=(8, 0))

    def read_new_dates():
        start, end = read_date(start_entry.get().strip()), read_date(end_entry.get().strip())
        if start is None or end is None:
            return None, None, "Enter dates as mm/dd/yyyy."
        return start, end, ""

    def check(event=None):
        """Updates the new total every time a date changes (RENT-03 criterion 3: total shown before confirming)."""
        for label in labels.values():
            label.config(text="-")
        start, end, error = read_new_dates()
        if error:
            message.config(text=error, fg=RED)
            return None
        session = browse.app.Session()
        try:
            ok, msg, info = preview_change(session, browse.user["user_id"], reservation_id, start, end)
        finally:
            session.close()
        if not ok:
            message.config(text=msg, fg=RED)
            return None
        message.config(text="", fg=RED)
        labels["new_total"].config(text=money(info["new_total"]))
        diff = info["difference"]
        sign = "+" if diff > 0 else "-" if diff < 0 else ""
        labels["difference"].config(text=f"{sign}{money(abs(diff))}")
        if info["refund"] > 0:
            labels["note"].config(text=f"{money(info['refund'])} will be refunded")
        elif info["balance_after"] > 0:
            labels["note"].config(text=f"Balance to pay: {money(info['balance_after'])}")
        else:
            labels["note"].config(text="Nothing more to pay")
        return info

    def confirm():
        start, end, error = read_new_dates()
        if error:
            message.config(text=error, fg=RED)
            return
        info = check()
        if info is None:
            return
        question = (f"Change booking #{booking['id']} to {nice_date(start)} - {nice_date(end)}?\n\n"
                    f"New total: {money(info['new_total'])}")
        if not messagebox.askyesno("Modify Booking", question, parent=browse.window):
            return
        session = browse.app.Session()
        try:
            success, msg = modify_booking(session, browse.user["user_id"], reservation_id, start, end)
            if success:
                # Send the "booking changed" email (NOTIF-01, added by Sadaf)
                try:
                    sent, email_note = send_booking_email(session, reservation_id, "changed")
                    msg += " " + email_note
                except Exception as e:
                    print(f"Email error: {e}")
        finally:
            session.close()
        if success:
            show_my_bookings(browse)
            browse.my_bookings_message.config(text=msg, fg=GREEN)
        else:
            message.config(text=msg, fg=RED)

    start_entry.bind("<KeyRelease>", check)
    end_entry.bind("<KeyRelease>", check)
    tk.Button(box, text="Confirm Change", font=("Arial", 11, "bold"), bg=DARK, fg="white",
              command=confirm).pack(fill=tk.X, ipady=3, pady=(8, 6))
    tk.Button(box, text="Back to My Bookings", font=("Arial", 11), bg=WHITE, fg=TEXT,
              command=lambda: show_my_bookings(browse)).pack(fill=tk.X, ipady=3)
    check()
