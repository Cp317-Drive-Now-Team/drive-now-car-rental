import re

try:
    from email_validator import validate_email, EmailNotValidError
    HAVE_LIBRARY = True
except ImportError:
    # If someone hasn't installed the library yet, the app still runs with a simpler check
    HAVE_LIBRARY = False
    print("email-validator is not installed, using the basic email check (pip install email-validator)")


def check_email(email):
    """
    Checks an email address. Returns (ok, message, cleaned_email).
    cleaned_email is the version to save: spaces removed and all lowercase.
    """
    email = (email or "").strip()
    if not email:
        return False, "This field is required.", ""
    if len(email) > 100:
        return False, "Email must be 100 characters or less.", ""

    if HAVE_LIBRARY:
        try:
            # check_deliverability=False means it checks the format only and doesn't go online.
            # Set it to True to also check that the domain (like gmail.com) can actually receive email.
            result = validate_email(email, check_deliverability=False)
            return True, "", result.normalized.lower()
        except EmailNotValidError:
            return False, "Enter a valid email address (like name@example.com).", ""

    # Basic check: one @, something before it, and a domain with a dot after it
    if re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$", email) and ".." not in email:
        return True, "", email.lower()
    return False, "Enter a valid email address (like name@example.com).", ""
