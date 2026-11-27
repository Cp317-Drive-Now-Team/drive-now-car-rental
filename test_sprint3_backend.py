"""Sprint 3 backend tests (ACC-03 rental history, ACC-01 profile). Run:  python test_sprint3_backend.py
Uses a throwaway in-memory database, no MySQL needed."""
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash
from models import Base, Car, Location, User, Reservation
from booking_service import create_booking, cancel_booking
from payment_service import make_payment
from rental_history_service import get_rental_history, get_booking_summary
import account_profile_service as p

d = lambda n: date.today() + timedelta(days=n)
engine = create_engine("sqlite://")
Base.metadata.create_all(engine)
s = sessionmaker(bind=engine)()
s.add_all([Location(location_id=1, location_name="Campus", address="x", city="c", state_province="s", postal_code="p"),
           User(user_id=1, first_name="Ann", last_name="Lee", email="a@x.com", password_hash=generate_password_hash("password1"),
                driver_license_number="D1"),
           User(user_id=2, first_name="Bob", last_name="Ray", email="b@x.com", password_hash=generate_password_hash("password2"),
                driver_license_number="D2"),
           Car(car_id=1, make="Toyota", model="Corolla", year=2022, car_type="Economy", daily_rate=50, location_id=1),
           Car(car_id=2, make="Honda", model="Civic", year=2023, car_type="Sedan", daily_rate=60, location_id=1)])
s.commit()

# ---------- ACC-03: rental history
assert get_rental_history(s, 1) == {"upcoming": [], "past": []}                 # new customer: empty, no crash

ok, _, near = create_booking(s, 1, 1, d(5), d(7), 1)
ok, _, far = create_booking(s, 1, 2, d(20), d(22), 1)
ok, _, gone = create_booking(s, 1, 1, d(30), d(32), 1)
ok, _, bobs = create_booking(s, 2, 2, d(40), d(42), 1)
assert cancel_booking(s, 1, gone)[0]
s.get(Reservation, far).status = 'Completed'; s.commit()                         # pretend this one already finished

h = get_rental_history(s, 1)
assert [r["id"] for r in h["upcoming"]] == [near]
assert {r["id"] for r in h["past"]} == {far, gone}
row = h["upcoming"][0]
assert row["car"] == "2022 Toyota Corolla" and row["status"] == "Pending" and row["paid"] == 0.0
assert row["can_modify"] and row["can_cancel"] and row["has_receipt"] is False
assert not any(r["id"] == bobs for r in h["upcoming"] + h["past"])               # criterion 3: only my own bookings
assert h["past"][0]["can_modify"] is False and h["past"][0]["can_cancel"] is False
assert get_booking_summary(s, 1, bobs) == (False, None)                           # someone else's booking
assert get_booking_summary(s, 1, near)[0] is True

# a booking with a deposit shows the amount paid, the balance and its receipt id
ok, msg, pid = make_payment(s, 1, near, "Deposit", "4242 4242 4242 4242", "12/30", "123")
assert ok, msg
row = get_rental_history(s, 1)["upcoming"][0]
assert row["paid"] == 20.0 and row["balance"] == 80.0 and row["receipt_ids"] == [pid] and row["has_receipt"]
assert row["can_pay"] is True

# ---------- ACC-01: profile
assert p.get_profile(s, 1)["email"] == "a@x.com" and "password_hash" not in p.get_profile(s, 1)
assert p.update_profile(s, 1, "Anna", "Lee", "A@X.com", "519-555-0100", "D1") == (True, "Your profile was saved.")
assert p.get_profile(s, 1)["first_name"] == "Anna" and p.get_profile(s, 1)["phone"] == "519-555-0100"
assert p.update_profile(s, 1, "Anna", "Lee", "b@x.com")[1] == "Email already exists."           # someone else's email
assert p.update_profile(s, 1, "Anna", "Lee", "a@x.com", None, "D2")[1] == "Driver's license is already registered."
assert p.update_profile(s, 1, "", "Lee", "a@x.com")[1] == "Please fill in all required fields."
assert p.update_profile(s, 1, "Anna", "Lee", "not-an-email")[1] == "Please enter a valid email address."
assert p.update_profile(s, 99, "A", "B", "z@x.com")[1] == "Account not found."
assert s.get(User, 1).role == "Customer"                                                         # role never changes

assert p.change_password(s, 1, "wrong", "newpassword1")[1] == "Your current password is not correct."
assert p.change_password(s, 1, "password1", "short")[0] is False
assert p.change_password(s, 1, "password1", "password1")[0] is False
assert p.change_password(s, 1, "password1", "newpassword1") == (True, "Your password was changed.")
assert s.get(User, 1).password_hash != "newpassword1"                                            # stored hashed
from werkzeug.security import check_password_hash
assert check_password_hash(s.get(User, 1).password_hash, "newpassword1")
print("All Sprint 3 backend tests passed.")
