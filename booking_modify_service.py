# Author: Dheeraj Bashal (Student ID: 169057697) - Group 22, CP317A
"""RENT-03  Modify Booking: backend (Dheeraj Bashal, Product Owner).

Works with models.py as it is (no new tables or columns) and uses the same helpers as booking_service.py.
Returns (success, message, ...) tuples like the other services, so the UI can show the message directly.
"""
import secrets
from sqlalchemy.orm import Session
from models import Car, Reservation, Payment
import booking_rules
import modify_rules
import payment_rules
from booking_service import payments_for


def _find_booking(session: Session, user_id: int, reservation_id: int):
    # Customers can only change their own bookings
    return session.query(Reservation).filter(
        Reservation.reservation_id == reservation_id,
        Reservation.user_id == user_id
    ).first()


def _check_change(session: Session, booking: Reservation, new_start, new_end):
    """
    Runs every rule for the change and returns (ok, message, info).
    info has the old and new totals, what has been paid, the balance after the change and any refund.
    """
    ok, message = modify_rules.can_modify(booking.status, booking.start_date)
    if not ok:
        return False, message, None
    ok, message = booking_rules.validate_booking_dates(new_start, new_end)
    if not ok:
        return False, message, None
    if not modify_rules.dates_changed(booking.start_date, booking.end_date, new_start, new_end):
        return False, "These are the same dates as your current booking.", None

    # The car must be free on the new dates. This booking's own old dates are left out of the check.
    others = session.query(Reservation.start_date, Reservation.end_date, Reservation.status).filter(
        Reservation.car_id == booking.car_id,
        Reservation.reservation_id != booking.reservation_id
    ).all()
    if not booking_rules.is_car_free(others, new_start, new_end):
        return False, "This car is already booked for those dates. Please choose different dates.", None

    new_total = booking_rules.calculate_total(booking.car.daily_rate, new_start, new_end)
    paid = payment_rules.amount_paid(payments_for(booking))
    refund = modify_rules.excess_to_refund(paid, new_total)
    return True, "", {
        "old_total": float(booking.total_cost),
        "new_total": new_total,
        "difference": modify_rules.price_change(booking.total_cost, new_total),
        "paid": paid,
        "refund": refund,
        "balance_after": round(max(new_total - paid, 0.0), 2),
    }


def preview_change(session: Session, user_id: int, reservation_id: int, new_start, new_end):
    """Shows the new total before the customer confirms. Saves nothing. Returns (ok, message, info)."""
    booking = _find_booking(session, user_id, reservation_id)
    if booking is None:
        return False, "Booking not found.", None
    return _check_change(session, booking, new_start, new_end)


def modify_booking(session: Session, user_id: int, reservation_id: int, new_start, new_end):
    """
    Changes the dates of an upcoming booking. Fulfills RENT-03 (Modify Booking).
    Returns (success, message).
    """
    try:
        booking = _find_booking(session, user_id, reservation_id)
        if booking is None:
            return False, "Booking not found."

        # Lock the car's row so two customers can't take the same dates at the same moment (MySQL waits here)
        session.query(Car).filter(Car.car_id == booking.car_id).with_for_update().first()
        session.refresh(booking)

        ok, message, info = _check_change(session, booking, new_start, new_end)
        if not ok:
            session.rollback()
            return False, message

        # Give back anything paid above the new total (test-mode refund, same as a cancellation)
        if info["refund"] > 0:
            session.add(Payment(
                reservation_id=booking.reservation_id,
                amount=info["refund"],
                payment_type='Refund',
                payment_method=payment_rules.TEST_METHOD,
                transaction_token="test_refund_" + secrets.token_hex(8),
                payment_status='Refunded'
            ))

        # Saving the new dates frees the old ones, because availability is worked out from the reservation dates
        booking.start_date = new_start
        booking.end_date = new_end
        booking.total_cost = info["new_total"]
        session.commit()
        print(f"Changed booking #{reservation_id} to {new_start} - {new_end}, total ${info['new_total']:.2f}")
    except Exception as e:
        session.rollback()
        print(f"Modify error: {e}")
        return False, "Could not change the booking. Please try again."

    if info["refund"] > 0:
        return True, f"Your booking was changed. A refund of ${info['refund']:.2f} will be returned to your card."
    if info["balance_after"] > 0:
        return True, f"Your booking was changed. The remaining balance is ${info['balance_after']:.2f}."
    return True, "Your booking was changed."
