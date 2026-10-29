from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, Car, Location, Payment, Reservation

# 1. Database Configuration
# Replace root:1234567890! with your password you set when setting up mysql.
DATABASE_URL = "mysql+pymysql://root:1234567890!@localhost:3306/drivenow_db"

# SQLAlchemy Engine and Session setup
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

def run_database_tests():
    session = SessionLocal()
    try:
        print("=" * 60)
        print("CONNECTING TO DRIVENOW_DB VIA SQLALCHEMY ORM")
        print("=" * 60)

        # Test 1: Query all branch locations
        locations = session.query(Location).all()
        print(f"\n[Locations Found: {len(locations)}]")
        for loc in locations:
            print(f" -> [{loc.location_id}] {loc.location_name} ({loc.city}, {loc.state_province})")

        # Test 2: Query all user accounts (Admins and Customers)
        users = session.query(User).all()
        print(f"\n[User Accounts Found: {len(users)}]")
        for user in users:
            print(f" -> [{user.user_id}] {user.first_name} {user.last_name} ({user.role}) | Email: {user.email}")

        # Test 3: Query all vehicle inventory (Cars, including Subaru Outback)
        cars = session.query(Car).all()
        print(f"\n[Vehicle Inventory Found: {len(cars)} vehicles]")
        for car in cars:
            print(f" -> [{car.car_id}] {car.year} {car.make} {car.model} "
                  f"({car.car_type}) - ${car.daily_rate}/day [Status: {car.status}]")

        # Test 4: Example Filter Query (Available SUVs)
        suvs = session.query(Car).filter(Car.car_type == 'SUV', Car.status == 'Available').all()
        print(f"\n[Filtered Search: Available SUVs ({len(suv_count := suvs)})]")
        for suv in suvs:
            print(f"    -> Match: {suv.year} {suv.make} {suv.model} (${suv.daily_rate}/day)")

        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)

    except Exception as e:
        print(f"\nAn error occurred during database testing: {e}")
    finally:
        session.close()
        print("\nDatabase session closed safely.")

if __name__ == "__main__":
    run_database_tests()