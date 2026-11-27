"""ACC-03.3 - View Rental History (backend).

Works with models.py as it is (no new tables or columns).
Builds on get_my_bookings() so the numbers match the My Bookings page, and adds:
  - the booking list split into Upcoming and Past (Wireframe 3)
  - the receipt ids for each booking, so receipts open from the history page (PAY-03 criterion 3)
  - flags that tell the UI whether the Modify and Cancel buttons should be shown
Returns plain dictionaries, so the UI only has to display them.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Payment, Reservation
import cancellation_rules
import modify_rules
from booking_service import get_my_bookings


def _receipt_ids_by_booking(session: Session, reservation_ids):
    """{reservation_id: [payment_id, ...]} for successful payments and deposits (refunds have no receipt)."""
    if not reservation_ids:
        return {}
    rows = session.execute(
        select(Payment.reservation_id, Payment.payment_id).where(
            Payment.reservation_id.in_(reservation_ids),
            Payment.payment_status == "Successful",
            Payment.payment_type != "Refund",
        ).order_by(Payment.payment_id)
    ).all()
    result = {}
    for reservation_id, payment_id in rows:
        result.setdefault(reservation_id, []).append(payment_id)
    return result


def get_rental_history(session: Session, user_id: int, today=None):
    """
    Returns {"upcoming": [...], "past": [...]} for ONE customer.
    The customer is always the user_id given here (taken from the login session, never from a form field),
    which is what makes "customers can only see their own bookings" true.
    Upcoming = Pending/Confirmed with a pick-up date after today, soonest first.
    Past     = everything else (Completed, Cancelled, already started), newest first.
    """
    bookings = get_my_bookings(session, user_id)        # already filtered by user_id
    receipts = _receipt_ids_by_booking(session, [b["id"] for b in bookings])
    start_dates = {}
    if bookings:
        start_dates = dict(session.execute(
            select(Reservation.reservation_id, Reservation.start_date).where(
                Reservation.user_id == user_id)).all())

    upcoming, past = [], []
    for b in bookings:
        row = dict(b)
        row["receipt_ids"] = receipts.get(b["id"], [])
        row["has_receipt"] = bool(row["receipt_ids"])
        row["can_modify"] = modify_rules.can_modify(b["status"], start_dates[b["id"]], today)[0]
        row["can_cancel"] = cancellation_rules.can_cancel(b["status"], start_dates[b["id"]], today)[0]
        row["can_pay"] = row["can_modify"] and b["balance"] > 0
        (upcoming if b["upcoming"] else past).append(row)

    upcoming.sort(key=lambda r: r["start"])              # soonest first
    past.sort(key=lambda r: r["start"], reverse=True)    # newest first
    return {"upcoming": upcoming, "past": past}


def get_booking_summary(session: Session, user_id: int, reservation_id: int):
    """One booking from the customer's own history. Returns (found, row)."""
    history = get_rental_history(session, user_id)
    for row in history["upcoming"] + history["past"]:
        if row["id"] == reservation_id:
            return True, row
    return False, None          # someone else's booking looks the same as one that does not exist
