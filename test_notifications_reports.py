"""NOTIF-01 and ADMIN-03 backend tests. Run:  python test_notifications_reports.py
Uses a throwaway in-memory database and a temporary outbox folder. No MySQL, no real emails."""
import os, tempfile, glob
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

OUT = tempfile.mkdtemp()
os.environ["DRIVENOW_OUTBOX_DIR"] = OUT
os.environ.pop("DRIVENOW_SMTP_HOST", None)

from models import Base, Car, Location, User, Reservation
from booking_service import create_booking, cancel_booking
from booking_modify_service import modify_booking
from payment_service import make_payment
import booking_notifications as n
import admin_report_service as rep

d = lambda k: date.today() + timedelta(days=k)
engine = create_engine("sqlite://"); Base.metadata.create_all(engine)
s = sessionmaker(bind=engine)()
h = generate_password_hash("password1")
s.add_all([Location(location_id=1, location_name="Campus", address="x", city="c", state_province="s", postal_code="p"),
           User(user_id=1, first_name="Ann", last_name="Lee", email="ann@x.com", password_hash=h),
           User(user_id=2, first_name="Bob", last_name="Ray", email="bob@x.com", password_hash=h),
           User(user_id=9, first_name="Ada", last_name="Min", email="admin@x.com", password_hash=h, role="Administrator"),
           Car(car_id=1, make="Toyota", model="Corolla", year=2022, car_type="Economy", daily_rate=50, location_id=1),
           Car(car_id=2, make="Honda", model="Civic", year=2023, car_type="Sedan", daily_rate=60, location_id=1),
           Car(car_id=3, make="Ford", model="Transit", year=2021, car_type="Van", daily_rate=90, location_id=1),
           Car(car_id=4, make="Old", model="Removed", year=2010, car_type="Sedan", daily_rate=30, location_id=1, is_active=False)])
s.commit()

# ---------- NOTIF-01
ok, _, rid = create_booking(s, 1, 1, d(10), d(13), 1)
sent, msg = n.notify_booking_event(s, rid, "booked")
assert sent and "saved" in msg
files = glob.glob(os.path.join(OUT, "*_booking%d_booked.txt" % rid))
assert len(files) == 1
text = open(files[0], encoding="utf-8").read()
assert "To: ann@x.com" in text and "2022 Toyota Corolla" in text and str(d(10)) in text and str(d(13)) in text
assert "$150.00" in text and "Campus" in text                                    # criterion 2: car, dates, total cost

ok, _ = modify_booking(s, 1, rid, d(10), d(15))[:2]
assert ok and n.notify_booking_event(s, rid, "changed")[0]
changed = open(glob.glob(os.path.join(OUT, "*_changed.txt"))[0], encoding="utf-8").read()
assert "$250.00" in changed and "was changed" in changed                         # shows the NEW total

make_payment(s, 1, rid, "Deposit", "4242 4242 4242 4242", "12/30", "123")
assert cancel_booking(s, 1, rid)[0]
assert n.notify_booking_event(s, rid, "cancelled")[0]
cancelled = open(glob.glob(os.path.join(OUT, "*_cancelled.txt"))[0], encoding="utf-8").read()
assert "was cancelled" in cancelled and "Cancelled" in cancelled

assert n.notify_booking_event(s, 9999, "booked")[0] is False                      # unknown booking: no crash
assert n.notify_booking_event(s, rid, "banana")[0] is False                       # unknown event: no crash

# a broken mail server must NEVER raise or undo anything
os.environ["DRIVENOW_SMTP_HOST"] = "mail.invalid.example"
sent, msg = n.notify_booking_event(s, rid, "booked")
assert sent is False and "booking was saved" in msg
assert s.get(Reservation, rid) is not None
os.environ.pop("DRIVENOW_SMTP_HOST")

# ---------- ADMIN-03
create_booking(s, 1, 1, d(20), d(22), 1)       # Corolla, 2 days
create_booking(s, 2, 1, d(30), d(31), 1)       # Corolla, 1 day
ok, _, civic = create_booking(s, 2, 2, d(40), d(45), 1)    # Civic, 5 days
ok, _, gone = create_booking(s, 1, 2, d(60), d(61), 1)
cancel_booking(s, 1, gone)                      # cancelled Civic booking

assert rep.get_booking_report(s, 1)[:2] == (False, rep.NOT_ADMIN_MESSAGE)       # criterion 3: customers blocked
assert rep.get_booking_report(s, 12345)[0] is False and rep.get_booking_report(s, None)[0] is False

ok, msg, r = rep.get_booking_report(s, 9)
by = {x["car_id"]: x for x in r["rows"]}
assert ok
assert by[1]["bookings"] == 2 and by[1]["days_booked"] == 3 and by[1]["revenue"] == 150.0   # cancelled first booking not counted
assert by[1]["cancelled"] == 1
assert by[2]["bookings"] == 1 and by[2]["cancelled"] == 1 and by[3]["bookings"] == 0       # criterion 1; unused car still listed
assert 4 not in by                                                                           # removed car with no history is hidden
assert r["rows"][0]["car_id"] in (1, 2) and r["most_rented"] == "2022 Toyota Corolla"
assert r["total_bookings"] == 3

# criterion 2: date range (overlap rule)
ok, _, r = rep.get_booking_report(s, 9, d(35), d(50))
assert {x["car_id"]: x["bookings"] for x in r["rows"]}[2] == 1 and {x["car_id"]: x["bookings"] for x in r["rows"]}[1] == 0
ok, _, r = rep.get_booking_report(s, 9, str(d(0)), str(d(21)))                    # text dates work too
assert {x["car_id"]: x["bookings"] for x in r["rows"]}[1] == 1                    # only the d(20)-d(22) booking overlaps
ok, _, r = rep.get_booking_report(s, 9, d(200), d(210))
assert ok and r["total_bookings"] == 0 and r["most_rented"] is None              # empty range: no crash
assert rep.get_booking_report(s, 9, d(10), d(5))[1] == "The end date cannot be earlier than the start date."
assert rep.get_booking_report(s, 9, "next week", None)[1] == "Please enter dates as YYYY-MM-DD."
print("All NOTIF-01 and ADMIN-03 backend tests passed.")
