from sqlalchemy.orm import Session
from models import Reservation, Payment
import payment_rules
from booking_service import payments_for


def get_payment_options(session: Session, user_id: int, reservation_id: int):
    """
    Returns what the payment page needs for one booking: total, amount already paid, balance,
    and the deposit amount (PAY-02). Returns None if the booking isn't the customer's.
    """
    booking = session.query(Reservation).filter(
        Reservation.reservation_id == reservation_id,
        Reservation.user_id == user_id
    ).first()
    if booking is None:
        return None

    paid = payment_rules.amount_paid(payments_for(booking))
    return {
        "id": booking.reservation_id,
        "car": f"{booking.car.year} {booking.car.make} {booking.car.model}",
        "start": booking.start_date,
        "end": booking.end_date,
        "location": booking.pickup_location.location_name if booking.pickup_location else "",
        "total": float(booking.total_cost),
        "paid": paid,
        "balance": payment_rules.balance_due(booking.total_cost, payments_for(booking)),
        "deposit": payment_rules.deposit_amount(booking.total_cost),
        "deposit_allowed": paid == 0,  # a deposit is only for the first payment
        "status": booking.status,
    }


def make_payment(session: Session, user_id: int, reservation_id: int, payment_type: str,
                 card_number: str, expiry: str, cvv: str):
    """
    Pays for a booking through the test-mode payment service. Fulfills PAY-01 (full payment) and PAY-02 (deposit).
    payment_type is 'Full Payment' or 'Deposit'.
    Returns (success, message, payment_id). The card number is never saved, only the transaction token.
    """
    # 1. Check the card details look right (format only)
    ok, message = payment_rules.validate_card(card_number, expiry, cvv)
    if not ok:
        return False, message, None

    # 2. Find the booking and work out how much to charge
    info = get_payment_options(session, user_id, reservation_id)
    if info is None:
        return False, "Booking not found.", None
    if info["status"] in ('Cancelled', 'Completed'):
        return False, "This booking can no longer be paid.", None
    if info["balance"] <= 0:
        return False, "This booking is already paid in full.", None

    if payment_type == 'Deposit':
        if not info["deposit_allowed"]:
            return False, "A deposit has already been paid. Please pay the remaining balance.", None
        amount = info["deposit"]
    else:
        amount = info["balance"]  # full payment, or the rest after a deposit

    # 3. Send it to the test-mode payment service
    status, token = payment_rules.process_test_payment(card_number)

    # 4. Save the result (successful or failed) with the token only
    try:
        payment = Payment(
            reservation_id=reservation_id,
            amount=amount,
            payment_type=payment_type,
            payment_method=payment_rules.TEST_METHOD,
            transaction_token=token,
            payment_status=status
        )
        session.add(payment)

        # 5. A booking is Confirmed once any payment goes through (deposit or full)
        if status == 'Successful':
            booking = session.get(Reservation, reservation_id)
            booking.status = 'Confirmed'
        session.commit()
        print(f"Payment #{payment.payment_id} for booking #{reservation_id}: {status}")
    except Exception as e:
        session.rollback()
        print(f"Payment error: {e}")
        return False, "Could not save the payment. Please try again.", None

    if status != 'Successful':
        return False, "Payment declined. Your card was not charged. Please try a different card.", None
    return True, "Payment successful.", payment.payment_id


def get_receipt(session: Session, user_id: int, payment_id: int = None, reservation_id: int = None):
    """
    Builds the receipt for a payment. Fulfills PAY-03 (View Receipts).
    If only reservation_id is given, uses the latest successful payment on that booking.
    Returns a dictionary, or None if there is nothing to show.
    """
    query = session.query(Payment).join(Reservation).filter(Reservation.user_id == user_id)
    if payment_id is not None:
        payment = query.filter(Payment.payment_id == payment_id).first()
    else:
        payment = query.filter(Payment.reservation_id == reservation_id,
                               Payment.payment_status == 'Successful').order_by(Payment.payment_id.desc()).first()
    if payment is None:
        return None

    booking = payment.reservation
    return {
        "receipt_no": payment.payment_id,
        "date": payment.payment_date,
        "booking_id": booking.reservation_id,
        "car": f"{booking.car.year} {booking.car.make} {booking.car.model}",
        "start": booking.start_date,
        "end": booking.end_date,
        "location": booking.pickup_location.location_name if booking.pickup_location else "",
        "payment_type": payment.payment_type,
        "method": payment.payment_method,
        "reference": payment.transaction_token,
        "amount": float(payment.amount),
        "total": float(booking.total_cost),
        "paid_so_far": payment_rules.amount_paid(payments_for(booking)),
        "balance": payment_rules.balance_due(booking.total_cost, payments_for(booking)),
    }
