"""Run:  python test_backend.py     (uses an in-memory DB, no MySQL needed)"""
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Car, Location, Reservation
from account_service import register_customer
import auth_service
from car_listing import get_active_cars
from car_search import search_cars

engine = create_engine("sqlite://")
Base.metadata.create_all(engine)
s = sessionmaker(bind=engine)()

s.add(Location(location_name="Campus", address="75 University Ave W", city="Waterloo",
                state_province="Ontario", postal_code="N2L 3C5"))
s.add_all([Car(make="Toyota", model="Corolla", year=2022, car_type="Economy", daily_rate=45, location_id=1),
            Car(make="Toyota", model="RAV4", year=2023, car_type="SUV", daily_rate=70, location_id=1),
            Car(make="Old", model="Removed", year=2010, car_type="Sedan", daily_rate=20, location_id=1, is_active=False)])
s.commit()

# --- ACC-01.3
assert register_customer(s, "", "A", "a@x.com", "password1")[0] is False
assert "valid email" in register_customer(s, "A", "B", "bad", "password1")[1]
assert "at least" in register_customer(s, "A", "B", "a@x.com", "short")[1]
assert register_customer(s, "Ann", "Lee", "ann@x.com", "password1") == (True, "Account created.")
assert register_customer(s, "Ann", "Lee", "ANN@x.com", "password1") == (False, "Email already exists.")
u = s.query(User).filter_by(email="ann@x.com").one()
assert u.role == "Customer" and u.password_hash != "password1"

# --- ACC-02.3
ok, msg, page = auth_service.login(s, "ann@x.com", "password1")
assert ok and page == "customer_home" and auth_service.can_access("browse_cars")
assert not auth_service.can_access("admin_dashboard")
auth_service.logout()
m1 = auth_service.login(s, "ann@x.com", "wrongpass")[1]
m2 = auth_service.login(s, "nobody@x.com", "password1")[1]
assert m1 == m2 == "Invalid email or password."

# --- CAR-01.3
assert [c.model for c in get_active_cars(s)] == ["Corolla", "RAV4"]   # removed car hidden

# --- CAR-02.3 : Corolla booked 20-23 March
s.add(Reservation(user_id=u.user_id, car_id=1, pickup_location_id=1, dropoff_location_id=1,
                  start_date=date(2027, 3, 20), end_date=date(2027, 3, 23),
                  total_cost=180, status="Confirmed"))
s.commit()
names = lambda r: [c.model for c in r]
assert "Corolla" not in names(search_cars(s, date(2027, 3, 22), date(2027, 3, 25)))  # overlap -> hide
assert "Corolla" in names(search_cars(s, date(2027, 3, 24), date(2027, 3, 26)))      # no overlap -> show
assert "Corolla" not in names(search_cars(s, date(2027, 3, 23), date(2027, 3, 24)))  # touches end day
assert names(search_cars(s, car_type="SUV")) == ["RAV4"]
print("ALL TESTS PASSED")
