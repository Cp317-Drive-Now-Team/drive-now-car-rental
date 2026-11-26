# Author: Dheeraj Bashal (Student ID: 169057697) - Group 22, CP317A
"""RENT-03  Modify Booking: rules (Dheeraj Bashal, Product Owner).

Pure rules with no database access. The modify page and booking_modify_service.py both use them.
Rules for a change of dates:
  1. Only upcoming bookings (Pending or Confirmed, pick-up after today) can be changed.
  2. The new dates must pass the normal booking rules (booking_rules.validate_booking_dates).
  3. The change is only saved if the car is free on the new dates. The booking's own old dates do not count against it.
  4. The new total is shown before the customer confirms.
  5. If the customer has already paid more than the new total, the extra is refunded.
     If the new total is higher, the difference is added to the balance and paid from My Bookings.
  6. The old dates open up for other customers as soon as the change is saved.
"""
from datetime import date

MODIFIABLE_STATUSES = ('Pending', 'Confirmed')


def can_modify(status: str, start_date: date, today=None):
    """Returns (True, "") or (False, message)."""
    today = today or date.today()
    if status == 'Cancelled':
        return False, "A cancelled booking cannot be changed."
    if status == 'Completed':
        return False, "A completed booking cannot be changed."
    if status not in MODIFIABLE_STATUSES:
        return False, "This booking cannot be changed."
    if start_date <= today:
        return False, "Only upcoming bookings can be changed."
    return True, ""


def dates_changed(old_start: date, old_end: date, new_start: date, new_end: date) -> bool:
    return (old_start, old_end) != (new_start, new_end)


def price_change(old_total, new_total):
    """New total minus old total. Positive means the customer owes more."""
    return round(float(new_total) - float(old_total), 2)


def excess_to_refund(amount_paid, new_total):
    """Money to give back when the customer has already paid more than the new total."""
    return round(max(float(amount_paid) - float(new_total), 0.0), 2)
