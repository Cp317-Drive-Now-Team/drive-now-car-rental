# Author: Dheeraj Bashal (Student ID: 169057697) - Group 22, CP317A
"""RENT-01.1  Define booking rules (Dheeraj Bashal, Product Owner).

Pure rules with no database access, so the booking screen (Sadaf) and the booking
service (Albina) both use the same checks and the same messages.
"""
from datetime import date

# Same statuses car_search.py uses to treat a car as taken for those dates
BLOCKING_STATUSES = ('Pending', 'Confirmed')

MIN_RENTAL_DAYS = 1
MAX_RENTAL_DAYS = 30


def rental_days(start: date, end: date) -> int:
    """Number of rental days. Matches the price summary on Car Details (3 days x $45 = $135)."""
    return max((end - start).days, MIN_RENTAL_DAYS)


def calculate_total(daily_rate, start: date, end: date):
    """Total cost for the rental, rounded to cents."""
    return round(float(daily_rate) * rental_days(start, end), 2)


def validate_booking_dates(start, end, today=None):
    """
    Returns (True, "") if the dates can be booked, otherwise (False, message).
    Messages for the first two cases match the ones already used by CAR-02 search.
    """
    today = today or date.today()
    if start is None or end is None:
        return False, "Please enter both a pick-up date and a return date."
    if end <= start:
        return False, "Return date must be after pick-up date."
    if start < today:
        return False, "Pick-up date cannot be in the past."
    if (end - start).days > MAX_RENTAL_DAYS:
        return False, "A booking can be at most %d days." % MAX_RENTAL_DAYS
    return True, ""


def dates_overlap(start_a: date, end_a: date, start_b: date, end_b: date) -> bool:
    """Two bookings overlap when each starts on or before the day the other ends (same rule as car_search.py)."""
    return start_a <= end_b and end_a >= start_b


def is_car_free(existing, start: date, end: date) -> bool:
    """
    existing: list of (start_date, end_date, status) for one car.
    Cancelled and Completed bookings do not block the car.
    """
    return not any(s in BLOCKING_STATUSES and dates_overlap(start, end, a, b) for a, b, s in existing)


def new_booking_status():
    """A new booking stays Pending until its payment succeeds (PAY-01), then becomes Confirmed."""
    return 'Pending'
