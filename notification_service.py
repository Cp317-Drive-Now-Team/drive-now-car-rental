import os
import smtplib
from datetime import datetime
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from email.utils import formatdate
from models import Reservation
import payment_rules
from booking_service import payments_for

OUTBOX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outbox")
FROM_ADDRESS = "Drive Now Car Rentals <no-reply@drivenow.example>"

try:
    import config
except ImportError:
    config = None


def email_settings():
    """Returns the real email settings from config.py, or None to stay in test mode."""
    host = getattr(config, "EMAIL_HOST", None)
    if not host:
        return None
    return {
        "host": host,
        "port": getattr(config, "EMAIL_PORT", 587),
        "user": getattr(config, "EMAIL_USER", ""),
        "password": getattr(config, "EMAIL_PASSWORD", ""),
    }


def send_email(to_address, subject, body, file_label="email"):
    """
    Saves the email to the outbox, and also sends it for real if email settings are in config.py.
    Returns (success, message). A failed email never stops the booking itself.
    """
    msg = EmailMessage()
    msg["From"] = FROM_ADDRESS
    msg["To"] = to_address
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg.set_content(body)

    # 1. Always keep a copy in the outbox
    try:
        os.makedirs(OUTBOX, exist_ok=True)
        filename = f"{datetime.now():%Y%m%d_%H%M%S_%f}_{file_label}.eml"
        with open(os.path.join(OUTBOX, filename), "wb") as f:
            f.write(msg.as_bytes())
    except OSError as e:
        print(f"Could not save email: {e}")
        return False, "Could not save the email."

    # 2. Send for real only if the team added email settings to config.py
    settings = email_settings()
    if settings is None:
        print(f"[TEST MODE] Email to {to_address}: {subject}")
        return True, f"A confirmation email was sent to {to_address}."
    try:
        with smtplib.SMTP(settings["host"], settings["port"], timeout=10) as server:
            server.starttls()
            server.login(settings["user"], settings["password"])
            server.send_message(msg)
        print(f"Email sent to {to_address}: {subject}")
        return True, f"A confirmation email was sent to {to_address}."
    except Exception as e:
        print(f"Email error: {e}")
        return False, "Your booking was saved, but the confirmation email could not be sent."


def nice_date(d):
    return d.strftime("%b %d, %Y")  # e.g. Nov 22, 2026


def send_booking_email(session, reservation_id, kind, refund=0.0):
    """
    Builds and sends the email for a booking. kind is 'created', 'changed' or 'cancelled'.
    Includes the car, dates and total cost (NOTIF-01 acceptance criteria).
    """
    booking = session.get(Reservation, reservation_id)
    if booking is None:
        return False, "Booking not found."

    car = f"{booking.car.year} {booking.car.make} {booking.car.model}"
    location = booking.pickup_location.location_name if booking.pickup_location else ""
    paid = payment_rules.amount_paid(payments_for(booking))
    balance = payment_rules.balance_due(booking.total_cost, payments_for(booking))

    headlines = {
        "created": (f"Your Drive Now booking #{booking.reservation_id} is reserved",
                    "Thanks for booking with Drive Now! Your car is reserved. "
                    "If you haven't paid yet, you can pay from My Bookings to confirm it."),
        "changed": (f"Your Drive Now booking #{booking.reservation_id} was changed",
                    "The dates on your booking were changed. Here are your new booking details."),
        "cancelled": (f"Your Drive Now booking #{booking.reservation_id} was cancelled",
                      "Your booking was cancelled. Here are the details of the booking you cancelled."),
    }
    subject, intro = headlines[kind]

    lines = [
        f"Hi {booking.user.first_name},",
        "",
        intro,
        "",
        f"Booking number:   #{booking.reservation_id}",
        f"Car:              {car}",
        f"Pick-up date:     {nice_date(booking.start_date)}",
        f"Return date:      {nice_date(booking.end_date)}",
        f"Pick-up location: {location}",
        f"Total cost:       ${float(booking.total_cost):,.2f}",
    ]
    if kind == "cancelled":
        lines.append(f"Refund:           ${refund:,.2f}")
    else:
        lines.append(f"Paid so far:      ${paid:,.2f}")
        lines.append(f"Balance:          ${balance:,.2f}")
    lines += ["", "Thanks for choosing Drive Now Car Rentals!",
              "This is an automatic email, please don't reply."]

    return send_email(booking.user.email, subject, "\n".join(lines),
                      file_label=f"booking{booking.reservation_id}_{kind}")


def get_my_emails(email_address):
    """Returns the emails in the outbox that were sent to this address, newest first (My Account > Emails)."""
    emails = []
    if not os.path.isdir(OUTBOX):
        return emails
    for filename in sorted(os.listdir(OUTBOX), reverse=True):
        if not filename.endswith(".eml"):
            continue
        try:
            with open(os.path.join(OUTBOX, filename), "rb") as f:
                msg = BytesParser(policy=policy.default).parse(f)
        except OSError:
            continue
        if (msg["To"] or "").strip().lower() != email_address.strip().lower():
            continue
        sent = msg["Date"].datetime if msg["Date"] else None
        emails.append({
            "date": sent.strftime("%b %d, %Y %I:%M %p") if sent else "",
            "subject": msg["Subject"],
            "body": msg.get_body(preferencelist=("plain",)).get_content(),
        })
    return emails
