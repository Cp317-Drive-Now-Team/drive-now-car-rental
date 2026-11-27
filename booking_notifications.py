"""NOTIF-01.3 - Email notifications for bookings (backend).

Sends an email when a customer books, changes or cancels a rental. The email shows the car, the dates and the total cost.

Works with models.py as it is (no new tables). Two modes, chosen by settings, so the app runs on any laptop:
  - REAL mode: set DRIVENOW_SMTP_HOST (and DRIVENOW_SMTP_USER / DRIVENOW_SMTP_PASSWORD / DRIVENOW_SMTP_FROM)
    in your environment and the email is sent through that mail server (for example Gmail's app-password SMTP).
  - TEST mode (default, nothing to set up): the email is saved as a .txt file in the 'outbox' folder, like the
    test-mode payments. Good for the demo video.

IMPORTANT: a failed email must NEVER undo or block a booking, so notify_booking_event() never raises an error.
Passwords for the mail server come from the environment and are never written in the code.
"""
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage

from sqlalchemy.orm import Session

from models import Reservation, Payment

EVENTS = ("booked", "changed", "cancelled")

_HEADLINES = {
    "booked": ("Your DriveNow booking was made", "Thanks for booking with DriveNow! Here are your booking details."),
    "changed": ("Your DriveNow booking was changed", "Your booking dates were changed. Here are your updated booking details."),
    "cancelled": ("Your DriveNow booking was cancelled", "Your booking was cancelled. Here is what was cancelled."),
}


def _outbox_dir():
    return os.getenv("DRIVENOW_OUTBOX_DIR", "outbox")


def build_email(session: Session, reservation_id: int, event: str):
    """
    Builds the email for one booking. Returns (to_address, subject, body) or None if the booking can't be found.
    Nothing is sent here, so this is easy to test.
    """
    booking = session.get(Reservation, reservation_id)
    if booking is None or event not in EVENTS:
        return None
    car, user = booking.car, booking.user
    subject, intro = _HEADLINES[event]
    pickup = booking.pickup_location.location_name if booking.pickup_location else "-"

    lines = [
        f"Hi {user.first_name},", "",
        intro, "",
        f"Booking number: #{booking.reservation_id}",
        f"Car:            {car.year} {car.make} {car.model}",
        f"Pick-up date:   {booking.start_date}",
        f"Return date:    {booking.end_date}",
        f"Pick-up place:  {pickup}",
        f"Total cost:     ${float(booking.total_cost):.2f}",
        f"Status:         {booking.status}",
    ]
    if event == "cancelled":
        refunded = sum(float(p.amount) for p in booking.payments if p.payment_type == "Refund")
        if refunded > 0:
            lines.append(f"Refund:         ${refunded:.2f} will be returned to your card")
    lines += ["", "Thank you for choosing DriveNow."]
    return user.email, subject, "\n".join(lines)


def _send_smtp(to_address, subject, body):
    host = os.getenv("DRIVENOW_SMTP_HOST")
    sender = os.getenv("DRIVENOW_SMTP_FROM", os.getenv("DRIVENOW_SMTP_USER", "no-reply@drivenow.example"))
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = sender, to_address, subject
    msg.set_content(body)
    with smtplib.SMTP(host, int(os.getenv("DRIVENOW_SMTP_PORT", "587")), timeout=10) as server:
        server.starttls()
        user = os.getenv("DRIVENOW_SMTP_USER")
        if user:
            server.login(user, os.getenv("DRIVENOW_SMTP_PASSWORD", ""))
        server.send_message(msg)


def _save_to_outbox(reservation_id, event, to_address, subject, body):
    folder = _outbox_dir()
    os.makedirs(folder, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    path = os.path.join(folder, f"{stamp}_booking{reservation_id}_{event}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"To: {to_address}\nSubject: {subject}\n\n{body}\n")
    return path


def notify_booking_event(session: Session, reservation_id: int, event: str):
    """
    Call this AFTER a booking was made, changed or cancelled and saved.  event = 'booked' | 'changed' | 'cancelled'
    Returns (sent, message). Never raises: if the email fails, the booking is still fine.
    """
    try:
        built = build_email(session, reservation_id, event)
        if built is None:
            return False, "No email was sent because the booking could not be found."
        to_address, subject, body = built
        if os.getenv("DRIVENOW_SMTP_HOST"):
            _send_smtp(to_address, subject, body)
            return True, f"A confirmation email was sent to {to_address}."
        _save_to_outbox(reservation_id, event, to_address, subject, body)
        return True, f"Test mode: the email for {to_address} was saved in the '{_outbox_dir()}' folder."
    except Exception as e:                       # mail server down, no internet, wrong password, disk problem...
        print(f"Email error: {e}")
        return False, "Your booking was saved, but we could not send the email."
