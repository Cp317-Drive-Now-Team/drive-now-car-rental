"""Run:  python test_albina_backend.py   (throwaway in-memory database, mock payments)
Note: row locks (with_for_update) only matter on MySQL; SQLite ignores them."""
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Car, Location, User
from booking_service import BookingError, cancel_reservation, create_reservation
from payment_service import pay, payment_summary
from receipt_service import list_receipts

engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
S = sessionmaker(bind=engine)()
S.add_all([Location(location_id=1, location_name="A", address="x", city="c", state_province="s", postal_code="p"),
           User(user_id=1, first_name="a", last_name="b", email="a@x.com", password_hash="h"),
           User(user_id=2, first_name="c", last_name="d", email="c@x.com", password_hash="h"),
           Car(car_id=1, make="Toyota", model="Corolla", year=2022, car_type="Sedan",
               daily_rate=Decimal("50.00"), location_id=1)])
S.commit()
d = lambda n: date.today() + timedelta(days=n)


def expect_error(fn, text):
    try:
        fn()
    except BookingError as e:
        assert text in str(e), str(e)
        return
    raise AssertionError("expected error: " + text)


r = create_reservation(S, 1, 1, d(5), d(8))
assert r.total_cost == Decimal("150.00") and r.status == "Pending"
expect_error(lambda: create_reservation(S, 2, 1, d(6), d(9)), "already booked")   # overlap
create_reservation(S, 2, 1, d(8), d(10))                                          # same-day handover ok
expect_error(lambda: create_reservation(S, 1, 1, d(-1), d(2)), "past")
expect_error(lambda: create_reservation(S, 1, 1, d(12), d(11)), "after")

res = pay(S, 1, r.reservation_id, "deposit", "pm_card_chargeDeclined")
assert res["success"] is False
res = pay(S, 1, r.reservation_id, "deposit", "pm_card_visa")
assert res["success"] and res["receipt"]["amount_paid"] == Decimal("30.00")
assert res["receipt"]["balance_remaining"] == Decimal("120.00")
res = pay(S, 1, r.reservation_id, "full", "pm_card_visa")                         # pays the balance
assert res["balance"] == 0 and res["receipt"]["amount_paid"] == Decimal("120.00")
assert len(list_receipts(S, 1, r.reservation_id)) == 2
expect_error(lambda: pay(S, 1, r.reservation_id, "full", "pm_card_visa"), "fully paid")

out = cancel_reservation(S, 1, r.reservation_id)
assert out["refund_amount"] == Decimal("150.00") and out["reservation"].status == "Cancelled"
create_reservation(S, 2, 1, d(5), d(8))                                           # car free again
expect_error(lambda: cancel_reservation(S, 1, r.reservation_id), "already cancelled")
print("All checks passed")
