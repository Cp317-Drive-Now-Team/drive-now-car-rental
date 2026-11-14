# Author: Dheeraj Bashal (Student ID: 169057697) - Group 22, CP317A
"""ADMIN-02.1  Define rental statuses (Dheeraj Bashal, Product Owner).

The database keeps four booking statuses (Pending, Confirmed, Cancelled, Completed).
Administrators see four rental statuses: Upcoming, Active, Completed, Cancelled.
"""
from datetime import date

RENTAL_STATUSES = ('Upcoming', 'Active', 'Completed', 'Cancelled')

# What an administrator can do next. Picked up = car handed over. Returned = car back, rental completed.
ALLOWED_ACTIONS = {
    'Upcoming': ('Mark Picked Up',),
    'Active': ('Mark Returned',),
    'Completed': (),
    'Cancelled': (),
}


def rental_status(db_status: str, start_date: date, end_date: date, picked_up=False, today=None):
    """Turns a reservation's database status and dates into the status shown on the admin rentals page."""
    today = today or date.today()
    if db_status == 'Cancelled':
        return 'Cancelled'
    if db_status == 'Completed':
        return 'Completed'
    if picked_up:
        return 'Active'
    return 'Upcoming'


def next_db_status(action: str):
    """Database status to save after an administrator action (None means no change)."""
    return {'Mark Returned': 'Completed'}.get(action)


def can_do(action: str, status: str) -> bool:
    return action in ALLOWED_ACTIONS.get(status, ())
