"""PAY-01.3 (pay), PAY-02.3 (deposit and balance) and refunds for cancellations.

No schema changes: deposit and balance are worked out from the payments table.
  Payment.payment_type: 'Deposit' | 'Full Payment' (also used for the final balance) | 'Refund'
  Payment.transaction_token: reference number only. Card details are never stored.
"""
import uuid
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session

import payment_gateway
from booking_service import BookingError
from models import Payment, Reservation

DEPOSIT_PERCENT = Decimal("20")   # TODO: Dheeraj to confirm (PAY-02.1)
REFUND_POLICY = "full"            # TODO: Dheeraj to confirm: 'full' | 'deposit_forfeit' | 'none'

TWO_PLACES = Decimal("0.01")


def _money(x) -> Decimal:
    return Decimal(x).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def paid_so_far(r: Reservation) -> Decimal:
    return _money(sum((p.amount for p in r.payments
                       if p.payment_status == "Successful" and p.payment_type != "Refund"),
                      Decimal("0")))


def deposit_amount(r: Reservation) -> Decimal:
    return _money(r.total_cost * DEPOSIT_PERCENT / 100)


def payment_summary(session: Session, user_id: int, reservation_id: int) -> dict:
    """What Sadaf's payment page shows: total, deposit option, balance."""
    r = session.get(Reservation, reservation_id)
    if r is None or r.user_id != user_id:
        raise BookingError("Booking not found.")
    paid = paid_so_far(r)
    return {"reservation_id": r.reservation_id, "status": r.status,
            "total": _money(r.total_cost), "paid": paid,
            "balance": _money(r.total_cost) - paid,
            "deposit_percent": DEPOSIT_PERCENT, "deposit_amount": deposit_amount(r),
            "deposit_available": paid == 0}


def pay(session: Session, user_id: int, reservation_id: int, mode: str, payment_token: str,
        payment_method: str = "Card") -> dict:
    """mode = 'full' or 'deposit'. If a deposit was already paid, this pays the remaining balance.
    Returns {'success', 'message', 'payment_id', 'receipt', 'balance'}."""
    from receipt_service import build_receipt  # local import avoids a circular import

    if mode not in ("full", "deposit"):
        raise BookingError("Choose full payment or deposit.")
    try:
        r = session.execute(  # lock: two clicks / two windows cannot pay the same booking twice
            select(Reservation).where(Reservation.reservation_id == reservation_id).with_for_update()
        ).scalar_one_or_none()
        if r is None or r.user_id != user_id:
            raise BookingError("Booking not found.")
        if r.status not in ("Pending", "Confirmed"):
            raise BookingError(f"A {r.status.lower()} booking cannot be paid.")

        total, paid = _money(r.total_cost), paid_so_far(r)
        if paid >= total:
            raise BookingError("This booking is already fully paid.")
        if paid > 0:
            amount, ptype = total - paid, "Full Payment"          # balance after a deposit
        elif mode == "deposit":
            amount, ptype = deposit_amount(r), "Deposit"
        else:
            amount, ptype = total, "Full Payment"

        result = payment_gateway.charge(
            amount, payment_token, idempotency_key=f"res{reservation_id}-{ptype}-{paid}-{uuid.uuid4().hex[:6]}")

        payment = Payment(reservation_id=reservation_id, amount=amount, payment_type=ptype,
                          payment_method=payment_method, transaction_token=result.reference,
                          payment_status="Successful" if result.ok else "Failed")
        session.add(payment)
        if not result.ok:
            session.commit()   # keep a record of the failed attempt
            return {"success": False, "message": result.message or "Payment failed.",
                    "payment_id": payment.payment_id, "receipt": None, "balance": total - paid}

        r.status = "Confirmed"
        session.flush()
        session.refresh(r)
        receipt = build_receipt(session, user_id, payment.payment_id)   # PAY-03.2 automatic receipt
        session.commit()
        return {"success": True, "message": "Payment successful.", "payment_id": payment.payment_id,
                "receipt": receipt, "balance": total - paid_so_far(r)}
    except Exception:
        session.rollback()
        raise


def refund_for_cancellation(session: Session, r: Reservation) -> Decimal:
    """Called by cancel_reservation inside its transaction. Adds Refund rows; does not commit."""
    paid = paid_so_far(r)
    if paid <= 0 or REFUND_POLICY == "none":
        return Decimal("0.00")
    if REFUND_POLICY == "deposit_forfeit":
        deposit = next((p.amount for p in r.payments
                        if p.payment_type == "Deposit" and p.payment_status == "Successful"), Decimal("0"))
        to_refund = max(Decimal("0"), paid - _money(deposit))
    else:
        to_refund = paid

    remaining, refunded = _money(to_refund), Decimal("0.00")
    originals = sorted((p for p in r.payments
                        if p.payment_status == "Successful" and p.payment_type != "Refund"),
                       key=lambda p: p.payment_id, reverse=True)
    for p in originals:
        if remaining <= 0:
            break
        part = min(remaining, _money(p.amount))
        res = payment_gateway.refund(p.transaction_token, part)
        if not res.ok:
            raise BookingError("The refund could not be processed. The booking was not cancelled.")
        session.add(Payment(reservation_id=r.reservation_id, amount=part, payment_type="Refund",
                            payment_method=p.payment_method, transaction_token=res.reference,
                            payment_status="Refunded"))
        remaining -= part
        refunded += part
    return refunded
