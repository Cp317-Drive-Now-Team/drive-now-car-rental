# Author: Dheeraj Bashal (Student ID: 169057697) - Group 22, CP317A
"""RENT-02.1  Define cancellation rules (Dheeraj Bashal, Product Owner).

Refund policy: full refund when cancelling 2 or more days before pick-up, otherwise a partial refund.
"""
from datetime import date

CANCELLABLE_STATUSES = ('Pending', 'Confirmed')

FULL_REFUND_DAYS_BEFORE = 2      # cancel 2 or more days before pick-up: full refund
LATE_REFUND_PERCENT = 50         # cancel less than 2 days before pick-up: 50% refund


def can_cancel(status: str, start_date: date, today=None):
    """Only upcoming bookings that are not already cancelled or completed can be cancelled."""
    today = today or date.today()
    if status == 'Cancelled':
        return False, "This booking is already cancelled."
    if status == 'Completed':
        return False, "A completed booking cannot be cancelled."
    if status not in CANCELLABLE_STATUSES:
        return False, "This booking cannot be cancelled."
    if start_date <= today:
        return False, "Only upcoming bookings can be cancelled."
    return True, ""


def refund_amount(amount_paid, start_date: date, today=None):
    """Refund owed for a cancellation, based on how many days remain before pick-up."""
    today = today or date.today()
    paid = float(amount_paid)
    if paid <= 0:
        return 0.0
    if (start_date - today).days >= FULL_REFUND_DAYS_BEFORE:
        return round(paid, 2)
    return round(paid * LATE_REFUND_PERCENT / 100, 2)
