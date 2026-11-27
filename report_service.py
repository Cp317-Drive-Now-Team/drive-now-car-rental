"""ADMIN-03.3 - Rental reports for administrators (backend).

Shows how many times each car was booked, optionally for a date range. Works with models.py as it is.

Rules (same wording as the backlog's acceptance criteria):
  1. The report shows how many times each car has been booked.
  2. It can be filtered by date range.
  3. Only administrators can view it - checked HERE on the backend, not just by hiding the button.

How we count (so the team can explain it in the report):
  - "Booked" = Pending, Confirmed or Completed bookings. Cancelled ones are shown in their own column.
  - Date range = bookings whose rental period OVERLAPS the range (a booking from Dec 28 to Jan 3 counts in a January report).
  - Cars with 0 bookings are listed too, so the admin can see which cars are never rented.
"""
from datetime import date, datetime

from sqlalchemy.orm import Session

from models import Car, Reservation, User
import booking_rules

NOT_ADMIN_MESSAGE = "Only administrators can view reports."


def _as_date(value):
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()


def get_booking_report(session: Session, admin_user_id: int, start_date=None, end_date=None):
    """
    Returns (success, message, report).
    report = {"rows": [...], "total_bookings": n, "most_rented": "2022 Toyota Corolla" or None, "start": d, "end": d}
    Each row: car_id, car, car_type, bookings, cancelled, days_booked, revenue, active (False = removed from the fleet).
    Rows are sorted with the most-booked car first.
    """
    # 1. Admin check on the backend (same pattern as car_admin.py)
    user = session.get(User, admin_user_id) if admin_user_id else None
    if user is None or user.role != 'Administrator':
        return False, NOT_ADMIN_MESSAGE, None

    # 2. Check the date range
    try:
        start, end = _as_date(start_date), _as_date(end_date)
    except ValueError:
        return False, "Please enter dates as YYYY-MM-DD.", None
    if start and end and end < start:
        return False, "The end date cannot be earlier than the start date.", None

    # 3. Count per car
    rows = {}
    for car in session.query(Car).all():
        rows[car.car_id] = {"car_id": car.car_id, "car": f"{car.year} {car.make} {car.model}", "car_type": car.car_type,
                            "bookings": 0, "cancelled": 0, "days_booked": 0, "revenue": 0.0, "active": bool(car.is_active)}

    query = session.query(Reservation)
    if start:
        query = query.filter(Reservation.end_date >= start)       # period overlaps the range
    if end:
        query = query.filter(Reservation.start_date <= end)
    for r in query.all():
        row = rows.get(r.car_id)
        if row is None:
            continue
        if r.status == 'Cancelled':
            row["cancelled"] += 1
        else:
            row["bookings"] += 1
            row["days_booked"] += booking_rules.rental_days(r.start_date, r.end_date)
            row["revenue"] = round(row["revenue"] + float(r.total_cost), 2)

    # Removed cars only appear if they have history in this range
    result = [r for r in rows.values() if r["active"] or r["bookings"] or r["cancelled"]]
    result.sort(key=lambda r: (-r["bookings"], r["car"]))
    total = sum(r["bookings"] for r in result)
    most = result[0]["car"] if result and result[0]["bookings"] > 0 else None
    return True, "Report ready.", {"rows": result, "total_bookings": total, "most_rented": most,
                                   "start": start, "end": end}
