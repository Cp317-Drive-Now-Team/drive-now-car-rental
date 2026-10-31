from sqlalchemy.orm import Session
from models import Car, Location, User

CAR_STATUSES = ('Available', 'Rented', 'Maintenance')

# There is no 'Removed' status in the cars table yet, so removing a car sets it to Maintenance.
# Customers only see Available cars, so it gets hidden but the record is still kept.
REMOVED_STATUS = 'Maintenance'


def require_admin(session: Session, user_id: int):
    """
    Checks on the backend that the user is an Administrator before any car changes are made.
    Fulfills ADMIN-01 and the role-based access control from our ethical considerations.
    """
    user = session.get(User, user_id)
    if not user or user.role != 'Administrator':
        raise PermissionError("Only administrators can manage cars.")
    return user


def list_all_cars(session: Session, user_id: int):
    require_admin(session, user_id)
    return session.query(Car).order_by(Car.car_id).all()


def list_locations(session: Session):
    return session.query(Location).order_by(Location.location_name).all()


def add_car(session: Session, user_id: int, car_data: dict):
    """
    Adds a new car to the inventory.
    """
    # 1. Make sure the user is an admin
    require_admin(session, user_id)

    # 2. Create the car and save it
    new_car = Car(**car_data)
    session.add(new_car)
    session.commit()
    print(f"Added car: {new_car.year} {new_car.make} {new_car.model}")
    return new_car


def update_car(session: Session, user_id: int, car_id: int, car_data: dict):
    """
    Updates the details of an existing car.
    """
    require_admin(session, user_id)
    car = session.get(Car, car_id)
    if car is None:
        raise ValueError("That car no longer exists.")

    for field, value in car_data.items():
        setattr(car, field, value)
    session.commit()
    print(f"Updated car #{car_id}")
    return car


def remove_car(session: Session, user_id: int, car_id: int):
    """
    Hides a car from customers instead of deleting it, so past bookings are not lost.
    """
    require_admin(session, user_id)
    car = session.get(Car, car_id)
    if car is None:
        raise ValueError("That car no longer exists.")

    car.status = REMOVED_STATUS
    session.commit()
    print(f"Removed car #{car_id} (status set to {REMOVED_STATUS})")
    return car
