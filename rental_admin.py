from sqlalchemy.orm import Session
from models import Reservation, Car
import rental_status
import payment_rules
from booking_service import payments_for
from auth_service import app_session, update_rental_status_secure


def is_admin():
    return app_session.is_logged_in and app_session.user.role == 'Administrator'


def picked_up(session: Session, booking: Reservation):
    """
    The database has no 'picked up' column, so we use the car's status: when an admin marks a rental as
    picked up, the car is set to 'Rented'. Only the car's earliest open booking counts as the one picked up.
    """
    if booking.status not in ('Pending', 'Confirmed') or booking.car.status != 'Rented':
        return False
    first_open = session.query(Reservation).filter(
        Reservation.car_id == booking.car_id,
        Reservation.status.in_(('Pending', 'Confirmed'))
    ).order_by(Reservation.start_date).first()
    return first_open is not None and first_open.reservation_id == booking.reservation_id


def list_rentals(session: Session, status_filter: str = None):
    """
    Returns every booking for the admin rentals page (ADMIN-02), with the rental status
    (Upcoming, Active, Completed, Cancelled) from rental_status.py.
    """
    if not is_admin():
        raise PermissionError("Only administrators can view rentals.")

    rows = []
    for b in session.query(Reservation).order_by(Reservation.start_date).all():
        status = rental_status.rental_status(b.status, b.start_date, b.end_date, picked_up(session, b))
        if status_filter and status != status_filter:
            continue
        # Short payment label for the table
        paid = payment_rules.amount_paid(payments_for(b))
        if any(p.payment_type == 'Refund' for p in b.payments):
            payment = "Refunded"
        elif paid <= 0:
            payment = "Unpaid"
        elif payment_rules.balance_due(b.total_cost, payments_for(b)) > 0:
            payment = "Deposit"
        else:
            payment = "Paid"
        rows.append({
            "id": b.reservation_id,
            "customer": f"{b.user.first_name} {b.user.last_name}",
            "car": f"{b.car.make} {b.car.model}",
            "start": b.start_date,
            "end": b.end_date,
            "total": float(b.total_cost),
            "payment": payment,
            "status": status,
        })
    return rows


def mark_picked_up(session: Session, reservation_id: int):
    """Admin hands the car over to the customer. The rental becomes Active."""
    if not is_admin():
        return False, "Access Denied: Only administrators are allowed to modify rental statuses."
    booking = session.get(Reservation, reservation_id)
    if booking is None:
        return False, "Reservation not found."

    status = rental_status.rental_status(booking.status, booking.start_date, booking.end_date,
                                         picked_up(session, booking))
    if not rental_status.can_do('Mark Picked Up', status):
        return False, f"A rental that is {status} can't be marked as picked up."
    if booking.status != 'Confirmed':
        return False, "This booking hasn't been paid yet, so the car can't be picked up."

    booking.car.status = 'Rented'
    session.commit()
    print(f"Booking #{reservation_id} picked up")
    return True, f"Rental #{reservation_id} marked as picked up."


def mark_returned(session: Session, reservation_id: int):
    """Admin gets the car back. The rental becomes Completed and the car is available again."""
    booking = session.get(Reservation, reservation_id)
    if booking is None:
        return False, "Reservation not found."
    status = rental_status.rental_status(booking.status, booking.start_date, booking.end_date,
                                         picked_up(session, booking))
    if not rental_status.can_do('Mark Returned', status):
        return False, f"A rental that is {status} can't be marked as returned."

    # Aryan's backend check saves the new status (ADMIN-02.3)
    success, message = update_rental_status_secure(session, reservation_id,
                                                   rental_status.next_db_status('Mark Returned'))
    if not success:
        return False, message

    car = session.get(Car, booking.car_id)
    car.status = 'Available'
    session.commit()
    print(f"Booking #{reservation_id} returned")
    return True, f"Rental #{reservation_id} marked as returned."
