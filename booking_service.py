import secrets
from datetime import date
from sqlalchemy.orm import Session
from models import Car, Reservation, Payment
import booking_rules
import cancellation_rules
import payment_rules


def create_booking(session: Session, user_id: int, car_id: int, start_date, end_date, pickup_location_id: int):
    """
    Creates a new booking for a customer. Fulfills RENT-01 (Book a Car).
    Returns (success, message, reservation_id).
    """
    # 1. Check the dates with the booking rules (same messages as the booking form)
    ok, message = booking_rules.validate_booking_dates(start_date, end_date)
    if not ok:
        return False, message, None

    try:
        # 2. Lock the car's row so two people booking the same car at the same moment can't both get it
        # (MySQL waits here until the other booking is saved)
        car = session.query(Car).filter(Car.car_id == car_id).with_for_update().first()
        if car is None or not car.is_active or car.status == 'Maintenance':
            session.rollback()
            return False, "This car is no longer available.", None

        # 3. Check for overlapping bookings on this car
        existing = session.query(Reservation.start_date, Reservation.end_date, Reservation.status).filter(
            Reservation.car_id == car_id
        ).all()
        if not booking_rules.is_car_free(existing, start_date, end_date):
            session.rollback()
            return False, "Sorry, this car was just booked for those dates. Please choose different dates.", None

        # 4. Save the booking as Pending until it is paid (PAY-01)
        booking = Reservation(
            user_id=user_id,
            car_id=car_id,
            pickup_location_id=pickup_location_id,
            dropoff_location_id=pickup_location_id,  # cars are returned to the same branch for now
            start_date=start_date,
            end_date=end_date,
            total_cost=booking_rules.calculate_total(car.daily_rate, start_date, end_date),
            status=booking_rules.new_booking_status()
        )
        session.add(booking)
        session.commit()
        print(f"Created booking #{booking.reservation_id} for car #{car_id}")
        return True, "Booking created.", booking.reservation_id
    except Exception as e:
        session.rollback()
        print(f"Booking error: {e}")
        return False, "Could not create the booking. Please try again.", None


def payments_for(booking: Reservation):
    """Returns the booking's payments in the format payment_rules expects: (type, amount, status)."""
    return [(p.payment_type, p.amount, p.payment_status) for p in booking.payments]


def get_my_bookings(session: Session, user_id: int):
    """
    Returns all of a customer's bookings with the amounts already worked out, newest pick-up first.
    Used by the My Bookings page (RENT-02).
    """
    bookings = session.query(Reservation).filter(Reservation.user_id == user_id).order_by(
        Reservation.start_date.desc()).all()
    results = []
    for b in bookings:
        paid = payment_rules.amount_paid(payments_for(b))
        results.append({
            "id": b.reservation_id,
            "car": f"{b.car.year} {b.car.make} {b.car.model}",
            "start": b.start_date,
            "end": b.end_date,
            "total": float(b.total_cost),
            "paid": paid,
            "balance": 0.0 if b.status == 'Cancelled' else payment_rules.balance_due(b.total_cost, payments_for(b)),
            "status": b.status,
            "upcoming": b.status in ('Pending', 'Confirmed') and b.start_date > date.today(),
        })
    return results


def cancel_booking(session: Session, user_id: int, reservation_id: int):
    """
    Cancels an upcoming booking and refunds what the cancellation rules allow. Fulfills RENT-02.
    Returns (success, message).
    """
    # 1. Customers can only cancel their own bookings
    booking = session.query(Reservation).filter(
        Reservation.reservation_id == reservation_id,
        Reservation.user_id == user_id
    ).first()
    if booking is None:
        return False, "Booking not found."

    # 2. Check the cancellation rules (only upcoming bookings)
    ok, message = cancellation_rules.can_cancel(booking.status, booking.start_date)
    if not ok:
        return False, message

    # 3. Work out the refund and record it (no card details are needed for a test refund)
    paid = payment_rules.amount_paid(payments_for(booking))
    refund = cancellation_rules.refund_amount(paid, booking.start_date)
    try:
        if refund > 0:
            session.add(Payment(
                reservation_id=booking.reservation_id,
                amount=refund,
                payment_type='Refund',
                payment_method=payment_rules.TEST_METHOD,
                transaction_token="test_refund_" + secrets.token_hex(8),
                payment_status='Refunded'
            ))

        # 4. Cancelled bookings don't block the car, so it becomes available again for those dates
        booking.status = 'Cancelled'
        session.commit()
        print(f"Cancelled booking #{reservation_id}, refund ${refund:.2f}")
    except Exception as e:
        session.rollback()
        print(f"Cancel error: {e}")
        return False, "Could not cancel the booking. Please try again."

    if refund > 0:
        return True, f"Your booking was cancelled. A refund of ${refund:.2f} will be returned to your card."
    return True, "Your booking was cancelled."


def refund_preview(session: Session, user_id: int, reservation_id: int):
    """Returns the refund the customer would get, so the Cancel prompt can show it before they confirm."""
    booking = session.query(Reservation).filter(
        Reservation.reservation_id == reservation_id,
        Reservation.user_id == user_id
    ).first()
    if booking is None:
        return 0.0
    paid = payment_rules.amount_paid(payments_for(booking))
    return cancellation_rules.refund_amount(paid, booking.start_date)
