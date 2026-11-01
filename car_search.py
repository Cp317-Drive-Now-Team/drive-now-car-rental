"""CAR-02.3 - Search/filter + exclude cars booked on overlapping dates."""
from datetime import date
from sqlalchemy import and_
from sqlalchemy.orm import Session
from models import Car, Reservation

# Reservations in these statuses block a car. Cancelled/Completed don't.
BLOCKING = ("Pending", "Confirmed")


def search_cars(session: Session, start_date: date = None, end_date: date = None,
                car_type=None, make=None, model=None,
                min_price=None, max_price=None, location_id=None):
    """Every filter is optional. Returns a list of Car."""
    if bool(start_date) != bool(end_date):
        raise ValueError("Please give both a start date and an end date.")
    if start_date and end_date and end_date < start_date:
        raise ValueError("End date cannot be before start date.")

    q = session.query(Car).filter(Car.is_active.is_(True), Car.status != "Maintenance")

    if car_type:     q = q.filter(Car.car_type == car_type)
    if make:         q = q.filter(Car.make.ilike(f"%{make.strip()}%"))
    if model:        q = q.filter(Car.model.ilike(f"%{model.strip()}%"))
    if min_price is not None: q = q.filter(Car.daily_rate >= min_price)
    if max_price is not None: q = q.filter(Car.daily_rate <= max_price)
    if location_id:  q = q.filter(Car.location_id == location_id)

    if start_date and end_date:
        # Overlap rule: each range starts on/before the day the other ends.
        #   existing.start <= search_end  AND  existing.end >= search_start
        overlapping = (session.query(Reservation.car_id)
                       .filter(Reservation.status.in_(BLOCKING),
                               and_(Reservation.start_date <= end_date,
                                    Reservation.end_date >= start_date)))
        q = q.filter(~Car.car_id.in_(overlapping))

    return q.order_by(Car.daily_rate).all()
