"""CAR-01.3 - Active car listing data.
Uses the team's search_cars() from car_search.py, which only returns cars
with status 'Available' (removed/unavailable cars are left out).
"""
from sqlalchemy.orm import Session
from car_search_ import search_cars


def get_active_cars(session: Session):
    """All cars customers can see, cheapest first."""
    return search_cars(session)