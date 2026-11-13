"""RENT-01.3 (create reservation) and RENT-02.3 (cancel reservation).

Works with models.py as it is: no new tables or columns.
Reservation.status:  Pending = booked, not paid yet | Confirmed = deposit or full payment received
                     Cancelled | Completed.
Pending and Confirmed both block the car, so double bookings are rejected.
"""
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Car, Reservation

BLOCKING_STATUSES = ("Pending", "Confirmed")


class BookingError(Exception):
    """Message is safe to show the user."""


def calculate_total(daily_rate, start: date, end: date) -> Decimal:
    return (Decimal(daily_rate) * (end - start).days).quantize(Decimal("0.01"))


def create_reservation(session: Session, user_id: int, car_id: int, start: date, end: date,
                       pickup_location_id: int | None = None,
                       dropoff_location_id: int | None = None,
                       today: date | None = None) -> Reservation:
    today = today or date.today()
    if not isinstance(start, date) or not isinstance(end, date):
        raise BookingError("Please choose valid pickup and return dates.")
    if start < today:
        raise BookingError("Pickup date cannot be in the past.")
    if end <= start:
        raise BookingError("Return date must be after the pickup date.")

    try:
        # Lock the car row: a second simultaneous request for the same car waits here
        # until this transaction commits, then sees the new reservation in the check below.
        car = session.execute(
            select(Car).where(Car.car_id == car_id).with_for_update()
        ).scalar_one_or_none()
        if car is None or not car.is_active:
            raise BookingError("This car is not available.")
        if car.status == "Maintenance":
            raise BookingError("This car is under maintenance.")

        clash = session.execute(
            select(Reservation.reservation_id).where(
                Reservation.car_id == car_id,
                Reservation.status.in_(BLOCKING_STATUSES),
                Reservation.start_date < end,      # ranges are [start, end): a same-day
                Reservation.end_date > start,      # return and pickup do not clash
            ).limit(1)
        ).first()
        if clash:
            raise BookingError("This car is already booked for those dates.")

        reservation = Reservation(
            user_id=user_id, car_id=car_id,
            pickup_location_id=pickup_location_id or car.location_id,
            dropoff_location_id=dropoff_location_id or car.location_id,
            start_date=start, end_date=end,
            total_cost=calculate_total(car.daily_rate, start, end),
            status="Pending",
        )
        session.add(reservation)
        session.commit()
        return reservation
    except Exception:
        session.rollback()
        raise


def list_user_reservations(session: Session, user_id: int) -> list[Reservation]:
    """Basic My Bookings data for Sadaf's page."""
    return list(session.execute(
        select(Reservation).where(Reservation.user_id == user_id)
        .order_by(Reservation.start_date.desc())
    ).scalars())


def cancel_reservation(session: Session, user_id: int, reservation_id: int,
                       is_admin: bool = False, today: date | None = None) -> dict:
    """Cancels an upcoming booking, frees the car and refunds per the refund policy.
    Returns {'reservation': ..., 'refund_amount': Decimal}."""
    from payment_service import refund_for_cancellation  # local import avoids a circular import

    today = today or date.today()
    try:
        r = session.execute(
            select(Reservation).where(Reservation.reservation_id == reservation_id).with_for_update()
        ).scalar_one_or_none()
        if r is None or (not is_admin and r.user_id != user_id):
            raise BookingError("Booking not found.")
        if r.status == "Cancelled":
            raise BookingError("This booking is already cancelled.")
        if r.status == "Completed" or r.end_date < today:
            raise BookingError("Past bookings cannot be cancelled.")
        if r.start_date <= today:
            raise BookingError("This rental has already started and cannot be cancelled.")

        refund_amount = refund_for_cancellation(session, r)   # adds Refund rows, no commit
        r.status = "Cancelled"                                # leaves BLOCKING_STATUSES -> car is free
        session.commit()
        return {"reservation": r, "refund_amount": refund_amount}
    except Exception:
        session.rollback()
        raise
