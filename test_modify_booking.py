# Author: Dheeraj Bashal (Student ID: 169057697) - Group 22, CP317A
"""RENT-03 tests. Run:  python test_modify_booking.py   (throwaway in-memory database, no MySQL needed)"""
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Car, Location, User, Payment
from booking_service import create_booking, cancel_booking
from payment_service import make_payment
import booking_modify_service as m
import modify_rules as r

d = lambda n: date.today() + timedelta(days=n)
TODAY = date(2026, 11, 20)

# --- Rules (no database)
assert r.can_modify('Confirmed', date(2026, 12, 1), TODAY) == (True, "")
assert r.can_modify('Pending', date(2026, 12, 1), TODAY)[0] is True
assert r.can_modify('Cancelled', date(2026, 12, 1), TODAY)[1] == "A cancelled booking cannot be changed."
assert r.can_modify('Completed', date(2026, 12, 1), TODAY)[0] is False
assert r.can_modify('Confirmed', TODAY, TODAY)[1] == "Only upcoming bookings can be changed."
assert r.dates_changed(d(5), d(8), d(5), d(8)) is False and r.dates_changed(d(5), d(8), d(6), d(8)) is True
assert r.price_change(150, 200) == 50.0 and r.price_change(150, 100) == -50.0
assert r.excess_to_refund(150, 100) == 50.0 and r.excess_to_refund(30, 100) == 0.0

# --- Backend on a throwaway database
engine = create_engine("sqlite://")
Base.metadata.create_all(engine)
s = sessionmaker(bind=engine)()
s.add_all([Location(location_id=1, location_name="Campus", address="x", city="c", state_province="s", postal_code="p"),
           User(user_id=1, first_name="Ann", last_name="Lee", email="a@x.com", password_hash="h"),
           User(user_id=2, first_name="Bob", last_name="Ray", email="b@x.com", password_hash="h"),
           Car(car_id=1, make="Toyota", model="Corolla", year=2022, car_type="Economy", daily_rate=50, location_id=1)])
s.commit()

ok, msg, rid = create_booking(s, 1, 1, d(5), d(8), 1)          # 3 days x 50 = 150
assert ok, msg
from models import Reservation

# Preview shows the new total and changes nothing
ok, msg, info = m.preview_change(s, 1, rid, d(5), d(10))       # 5 days = 250
assert ok and info["new_total"] == 250.0 and info["difference"] == 100.0 and info["balance_after"] == 250.0
assert s.get(Reservation, rid).end_date == d(8)

# Bad changes are rejected with a clear message
assert m.modify_booking(s, 1, rid, d(5), d(8)) == (False, "These are the same dates as your current booking.")
assert m.modify_booking(s, 1, rid, d(9), d(7))[1] == "Return date must be after pick-up date."
assert m.modify_booking(s, 1, rid, d(-3), d(2))[1] == "Pick-up date cannot be in the past."
assert m.modify_booking(s, 2, rid, d(6), d(9)) == (False, "Booking not found.")    # someone else's booking

# Another customer holds d(12) to d(15): the change is refused if it runs into those dates
ok, msg, other = create_booking(s, 2, 1, d(12), d(15), 1)
assert ok
ok, msg = m.modify_booking(s, 1, rid, d(5), d(13))
assert not ok and "already booked" in msg
assert s.get(Reservation, rid).end_date == d(8)                 # nothing was saved

# A valid change (own old dates do not block it): saved, new total stored
ok, msg = m.modify_booking(s, 1, rid, d(6), d(9))
assert ok, msg
res = s.get(Reservation, rid)
assert res.start_date == d(6) and res.end_date == d(9) and float(res.total_cost) == 150.0

# Old dates open up for other customers
ok, msg, third = create_booking(s, 2, 1, d(4), d(5), 1)
assert ok, msg

# Longer stay after paying in full: the extra is added to the balance
ok, msg, pid = make_payment(s, 1, rid, 'Full Payment', "4242 4242 4242 4242", "12/28", "123")
assert ok
ok, msg = m.modify_booking(s, 1, rid, d(6), d(11))              # 5 days = 250, paid 150
assert ok and "remaining balance is $100.00" in msg
# Shorter stay after paying: the extra is refunded
ok, msg = m.modify_booking(s, 1, rid, d(6), d(8))              # 2 days = 100, paid 150
assert ok and "refund of $50.00" in msg
refund = s.query(Payment).filter_by(reservation_id=rid, payment_type='Refund').one()
assert float(refund.amount) == 50.0 and refund.payment_status == 'Refunded' and refund.transaction_token.startswith("test_refund_")

# A cancelled booking cannot be changed
ok, msg = cancel_booking(s, 1, rid)
assert ok
assert m.modify_booking(s, 1, rid, d(20), d(22)) == (False, "A cancelled booking cannot be changed.")

print("All modify booking tests passed.")
