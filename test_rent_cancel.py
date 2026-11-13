# Author: Dheeraj Bashal (Student ID: 169057697) - Group 22, CP317A
"""RENT-02.4 Test cancellation (+ rule tests for RENT-01.1, ADMIN-02.1).
Run:  python test_rent_cancel.py     (no MySQL needed)
"""
from datetime import date
import booking_rules as b
import cancellation_rules as c
import rental_status as rs

TODAY = date(2026, 11, 20)

# --- Cancellation (RENT-02)
assert c.can_cancel('Confirmed', date(2026, 12, 1), TODAY) == (True, "")
assert c.can_cancel('Pending', date(2026, 12, 1), TODAY)[0] is True
ok, msg = c.can_cancel('Confirmed', date(2026, 11, 10), TODAY); assert not ok and "upcoming" in msg
assert c.can_cancel('Confirmed', TODAY, TODAY)[0] is False             # starts today: too late
assert c.can_cancel('Cancelled', date(2026, 12, 1), TODAY)[1] == "This booking is already cancelled."
assert c.can_cancel('Completed', date(2026, 12, 1), TODAY)[0] is False
assert c.refund_amount(135, date(2026, 11, 25), TODAY) == 135.0         # 5 days ahead: full
assert c.refund_amount(135, date(2026, 11, 22), TODAY) == 135.0         # exactly 2 days ahead: full
assert c.refund_amount(135, date(2026, 11, 21), TODAY) == 67.5          # 1 day ahead: 50%
assert c.refund_amount(0, date(2026, 11, 25), TODAY) == 0.0             # nothing paid: nothing to refund

# A cancelled booking frees the car again (RENT-02.3 depends on this)
booked = [(date(2026, 12, 10), date(2026, 12, 13), 'Confirmed')]
assert b.is_car_free(booked, date(2026, 12, 11), date(2026, 12, 12)) is False
booked = [(date(2026, 12, 10), date(2026, 12, 13), 'Cancelled')]
assert b.is_car_free(booked, date(2026, 12, 11), date(2026, 12, 12)) is True

# --- Booking rules (RENT-01)
assert b.validate_booking_dates(date(2026, 12, 10), date(2026, 12, 13), TODAY) == (True, "")
assert b.validate_booking_dates(date(2026, 12, 20), date(2026, 12, 18), TODAY)[1] == "Return date must be after pick-up date."
assert b.validate_booking_dates(date(2026, 11, 1), date(2026, 11, 5), TODAY)[1] == "Pick-up date cannot be in the past."
assert b.validate_booking_dates(None, date(2026, 12, 1), TODAY)[0] is False
assert b.validate_booking_dates(date(2026, 12, 1), date(2027, 2, 1), TODAY)[0] is False   # over 30 days
assert b.calculate_total(45, date(2026, 12, 10), date(2026, 12, 13)) == 135.0
assert b.dates_overlap(date(2026, 11, 22), date(2026, 11, 25), date(2026, 11, 20), date(2026, 11, 23))
assert not b.dates_overlap(date(2026, 11, 24), date(2026, 11, 26), date(2026, 11, 20), date(2026, 11, 23))
assert b.new_booking_status() == 'Pending'

# --- Rental statuses (ADMIN-02)
d1, d2 = date(2026, 12, 1), date(2026, 12, 4)
assert rs.rental_status('Confirmed', d1, d2) == 'Upcoming'
assert rs.rental_status('Confirmed', d1, d2, picked_up=True) == 'Active'
assert rs.rental_status('Completed', d1, d2) == 'Completed'
assert rs.rental_status('Cancelled', d1, d2) == 'Cancelled'
assert rs.can_do('Mark Picked Up', 'Upcoming') and not rs.can_do('Mark Returned', 'Upcoming')
assert rs.can_do('Mark Returned', 'Active') and not rs.can_do('Mark Picked Up', 'Completed')
assert rs.next_db_status('Mark Returned') == 'Completed' and rs.next_db_status('Mark Picked Up') is None

print("All cancellation, booking and rental status tests passed.")
