from sqlalchemy import or_, func
from sqlalchemy.orm import Session
from models import Car, Location, Reservation

# Bookings with these statuses mean the car is taken for those dates
BLOCKING_STATUSES = ('Pending', 'Confirmed')

SORT_OPTIONS = {
    "Price: Low to High": "price_asc",
    "Price: High to Low": "price_desc",
    "Year: Newest First": "year_desc",
    "Make: A to Z": "make_asc",
}


def get_filter_options(session: Session):
    """
    Returns the car types and makes of active cars, used to fill the dropdowns.
    """
    available_cars = session.query(Car).filter(Car.is_active.is_(True), Car.status != 'Maintenance').all()
    types = sorted({car.car_type for car in available_cars})
    makes = sorted({car.make for car in available_cars})
    return types, makes


def get_locations(session: Session):
    """
    Returns all branch locations for the pick-up location dropdown.
    """
    return session.query(Location).order_by(Location.location_name).all()


def search_cars(session: Session, pickup_date=None, return_date=None, car_type=None, car_types=None, make=None,
                keyword=None, min_price=None, max_price=None, sort="price_asc"):
    """
    Returns available cars that match the search filters. Fulfills CAR-01 (Browse) and CAR-02 (Search).
    Every filter is optional. If both dates are given, cars booked on overlapping dates are left out.
    """
    # 1. Only show active cars, same rule as car_listing.py (removed cars and cars in maintenance are hidden)
    query = session.query(Car).filter(Car.is_active.is_(True), Car.status != 'Maintenance')

    # 2. Apply the filters that were filled in
    if car_type:
        query = query.filter(Car.car_type == car_type)
    if car_types:
        query = query.filter(Car.car_type.in_(car_types))
    if make:
        query = query.filter(Car.make == make)
    if keyword:
        query = query.filter(or_(func.lower(Car.make).like(f"%{keyword.lower()}%"),
                                 func.lower(Car.model).like(f"%{keyword.lower()}%")))
    if min_price is not None:
        query = query.filter(Car.daily_rate >= min_price)
    if max_price is not None:
        query = query.filter(Car.daily_rate <= max_price)

    # 3. Leave out cars that are already booked for those dates
    # Two bookings overlap when each one starts on or before the day the other ends
    if pickup_date and return_date:
        booked_cars = session.query(Reservation.car_id).filter(
            Reservation.status.in_(BLOCKING_STATUSES),
            Reservation.start_date <= return_date,
            Reservation.end_date >= pickup_date
        )
        query = query.filter(~Car.car_id.in_(booked_cars))

    # 4. Sort the results
    if sort == "price_desc":
        query = query.order_by(Car.daily_rate.desc(), Car.car_id)
    elif sort == "year_desc":
        query = query.order_by(Car.year.desc(), Car.daily_rate, Car.car_id)
    elif sort == "make_asc":
        query = query.order_by(Car.make, Car.model, Car.car_id)
    else:
        query = query.order_by(Car.daily_rate, Car.car_id)

    return query.all()
