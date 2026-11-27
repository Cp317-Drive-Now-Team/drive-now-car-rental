from sqlalchemy.orm import Session
from models import Car, Reservation
import booking_rules
import payment_rules
from booking_service import payments_for
from auth_service import app_session


def rental_report(session: Session, from_date=None, to_date=None):
    """
    Builds the rental report. Only bookings whose pick-up date is between from_date and to_date are counted
    (both are optional). Returns (rows, totals):
      rows   - one per car: bookings, cancellations, days rented and revenue, most booked first
      totals - the same numbers for the whole fleet, plus the most booked car
    """
    # 1. Only administrators can see reports (backend check, same as ADMIN-01 and ADMIN-02)
    if not app_session.is_logged_in or app_session.user.role != 'Administrator':
        raise PermissionError("Only administrators can view reports.")

    # 2. Get the bookings in the date range
    query = session.query(Reservation)
    if from_date:
        query = query.filter(Reservation.start_date >= from_date)
    if to_date:
        query = query.filter(Reservation.start_date <= to_date)
    bookings = query.all()

    # 3. Start every car at zero so cars with no bookings still show up in the report
    rows = {}
    for car in session.query(Car).order_by(Car.car_id).all():
        rows[car.car_id] = {
            "car_id": car.car_id,
            "car": f"{car.year} {car.make} {car.model}",
            "type": car.car_type,
            "bookings": 0,
            "cancelled": 0,
            "days": 0,
            "revenue": 0.0,
        }

    # 4. Add up each booking
    for b in bookings:
        row = rows.get(b.car_id)
        if row is None:
            continue
        if b.status == 'Cancelled':
            row["cancelled"] += 1
        else:
            row["bookings"] += 1
            row["days"] += booking_rules.rental_days(b.start_date, b.end_date)
        # Revenue is what was actually kept: payments minus refunds (a late cancellation keeps part of it)
        row["revenue"] += payment_rules.amount_paid(payments_for(b))

    rows = sorted(rows.values(), key=lambda r: (-r["bookings"], -r["revenue"], r["car_id"]))
    for row in rows:
        row["revenue"] = round(row["revenue"], 2)

    totals = {
        "bookings": sum(r["bookings"] for r in rows),
        "cancelled": sum(r["cancelled"] for r in rows),
        "days": sum(r["days"] for r in rows),
        "revenue": round(sum(r["revenue"] for r in rows), 2),
        "most_booked": rows[0]["car"] if rows and rows[0]["bookings"] > 0 else "-",
    }
    return rows, totals
