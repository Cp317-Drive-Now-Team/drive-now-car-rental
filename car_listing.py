"""CAR-01.3 - Active car listing data. Leaves out removed cars."""
from sqlalchemy.orm import Session
from models import Car


def get_active_cars(session: Session):
    """All active cars (not removed, not in maintenance), cheapest first."""
    return (session.query(Car)
            .filter(Car.is_active.is_(True), Car.status != "Maintenance")
            .order_by(Car.daily_rate, Car.make, Car.model)
            .all())
