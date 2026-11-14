"""PAY-03.2 - receipts. Built from the payments table, so no new table is needed.
Receipt number = DN-<year>-<payment id>. One receipt per successful payment or deposit."""
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from rental_booking_service import BookingError
from models import Payment, Reservation


def build_receipt(session: Session, user_id: int, payment_id: int, is_admin: bool = False) -> dict:
    p = session.get(Payment, payment_id)
    if p is None or p.payment_type == "Refund" or p.payment_status != "Successful":
        raise BookingError("Receipt not found.")
    r = p.reservation
    if not is_admin and r.user_id != user_id:
        raise BookingError("Receipt not found.")

    paid_to_date = sum((x.amount for x in r.payments
                        if x.payment_status == "Successful" and x.payment_type != "Refund"
                        and x.payment_id is not None and x.payment_id <= p.payment_id), Decimal("0"))
    when = p.payment_date
    return {
        "receipt_number": f"DN-{(when.year if when else 0)}-{p.payment_id:06d}",
        "date": when,
        "payment_type": p.payment_type,                 # 'Deposit' or 'Full Payment'
        "amount_paid": Decimal(p.amount),
        "reference": p.transaction_token,
        "reservation_id": r.reservation_id,
        "car": f"{r.car.year} {r.car.make} {r.car.model}",
        "pickup_date": r.start_date,
        "return_date": r.end_date,
        "total_cost": Decimal(r.total_cost),
        "paid_to_date": Decimal(paid_to_date),
        "balance_remaining": Decimal(r.total_cost) - Decimal(paid_to_date),
    }


def list_receipts(session: Session, user_id: int, reservation_id: int, is_admin: bool = False) -> list[dict]:
    r = session.get(Reservation, reservation_id)
    if r is None or (not is_admin and r.user_id != user_id):
        raise BookingError("Booking not found.")
    ids = session.execute(
        select(Payment.payment_id).where(Payment.reservation_id == reservation_id,
                                         Payment.payment_status == "Successful",
                                         Payment.payment_type != "Refund")
        .order_by(Payment.payment_id)).scalars()
    return [build_receipt(session, user_id, i, is_admin) for i in ids]
