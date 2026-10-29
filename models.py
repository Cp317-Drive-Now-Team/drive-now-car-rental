from sqlalchemy import (
    Column, Integer, String, Numeric, Enum, DateTime, Date, ForeignKey, Index, Text
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=True)
    driver_license_number = Column(String(50), nullable=True, unique=True)
    role = Column(Enum('Customer', 'Administrator'), nullable=False, default='Customer')
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    reservations = relationship("Reservation", back_populates="user", cascade="all, delete")


class Location(Base):
    __tablename__ = 'locations'

    location_id = Column(Integer, primary_key=True, autoincrement=True)
    location_name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=False)
    city = Column(String(50), nullable=False)
    state_province = Column(String(50), nullable=False)
    postal_code = Column(String(20), nullable=False)

    # Relationships
    cars = relationship("Car", back_populates="location")
    pickup_reservations = relationship("Reservation", foreign_keys="[Reservation.pickup_location_id]", back_populates="pickup_location")
    dropoff_reservations = relationship("Reservation", foreign_keys="[Reservation.dropoff_location_id]", back_populates="dropoff_location")


class Car(Base):
    __tablename__ = 'cars'

    car_id = Column(Integer, primary_key=True, autoincrement=True)
    make = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    car_type = Column(String(30), nullable=False)
    daily_rate = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum('Available', 'Rented', 'Maintenance'), nullable=False, default='Available')
    location_id = Column(Integer, ForeignKey('locations.location_id', ondelete='RESTRICT'), nullable=False)

    # Relationships
    location = relationship("Location", back_populates="cars")
    reservations = relationship("Reservation", back_populates="car")

    # Index matching your database index
    __table_args__ = (
        Index('idx_car_search', 'make', 'model', 'year', 'car_type', 'status'),
    )


class Reservation(Base):
    __tablename__ = 'reservations'

    reservation_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    car_id = Column(Integer, ForeignKey('cars.car_id', ondelete='RESTRICT'), nullable=False)
    pickup_location_id = Column(Integer, ForeignKey('locations.location_id', ondelete='RESTRICT'), nullable=False)
    dropoff_location_id = Column(Integer, ForeignKey('locations.location_id', ondelete='RESTRICT'), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_cost = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum('Pending', 'Confirmed', 'Cancelled', 'Completed'), nullable=False, default='Pending')
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="reservations")
    car = relationship("Car", back_populates="reservations")
    pickup_location = relationship("Location", foreign_keys=[pickup_location_id], back_populates="pickup_reservations")
    dropoff_location = relationship("Location", foreign_keys=[dropoff_location_id], back_populates="dropoff_reservations")
    payments = relationship("Payment", back_populates="reservation", cascade="all, delete")

    # Index matching your database index for double-booking prevention
    __table_args__ = (
        Index('idx_reservation_dates', 'car_id', 'start_date', 'end_date', 'status'),
    )


class Payment(Base):
    __tablename__ = 'payments'

    payment_id = Column(Integer, primary_key=True, autoincrement=True)
    reservation_id = Column(Integer, ForeignKey('reservations.reservation_id', ondelete='CASCADE'), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_type = Column(Enum('Deposit', 'Full Payment', 'Refund'), nullable=False)
    payment_method = Column(String(50), nullable=False)
    transaction_token = Column(String(255), nullable=False) # Tokenized compliance field
    payment_status = Column(Enum('Successful', 'Failed', 'Refunded'), nullable=False, default='Successful')
    payment_date = Column(DateTime, default=datetime.utcnow)

    # Relationships
    reservation = relationship("Reservation", back_populates="payments")