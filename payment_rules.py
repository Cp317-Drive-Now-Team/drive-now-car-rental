# Author: Dheeraj Bashal (Student ID: 169057697) - Group 22, CP317A
"""PAY-01.1 Define payment flow, PAY-02.1 Define deposit rule (Dheeraj Bashal, Product Owner).

Test-mode payments only. The database stores a transaction token and the amount.
Card numbers, expiry dates and security codes are never saved anywhere.
"""
import secrets

PAYMENT_TYPES = ('Deposit', 'Full Payment', 'Refund')      # matches payments.payment_type
PAYMENT_STATUSES = ('Successful', 'Failed', 'Refunded')    # matches payments.payment_status

# OPEN DECISION (PAY-02.1): deposit is a share of the total. Product Owner confirms the percentage.
DEPOSIT_PERCENT = 20

TEST_METHOD = "Test Card"
TEST_DECLINE_CARD = "4000000000000002"   # this number is always declined in test mode


def deposit_amount(total):
    return round(float(total) * DEPOSIT_PERCENT / 100, 2)


def balance_due(total, payments):
    """payments: list of (payment_type, amount, payment_status). Refunds reduce what has been paid."""
    return round(float(total) - amount_paid(payments), 2)


def amount_paid(payments):
    paid = 0.0
    for ptype, amount, status in payments:
        if status == 'Failed':
            continue
        paid += -float(amount) if ptype == 'Refund' else float(amount)
    return round(paid, 2)


def luhn_ok(number: str) -> bool:
    digits = [int(c) for c in number if c.isdigit()]
    if len(digits) < 13:
        return False
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d = d * 2 - 9 if d * 2 > 9 else d * 2
        total += d
    return total % 10 == 0


def validate_card(number: str, expiry: str, cvv: str):
    """Checks the format only. Returns (True, "") or (False, message). Nothing is stored."""
    clean = number.replace(" ", "")
    if not clean.isdigit() or not luhn_ok(clean):
        return False, "Enter a valid card number."
    parts = expiry.split("/")
    if len(parts) != 2 or not all(p.isdigit() for p in parts) or not 1 <= int(parts[0]) <= 12:
        return False, "Enter the expiry date as MM/YY."
    if not cvv.isdigit() or len(cvv) not in (3, 4):
        return False, "Enter the 3 or 4 digit security code."
    return True, ""


def process_test_payment(number: str):
    """
    Test-mode gateway. Returns (status, transaction_token).
    The token is random, so it says nothing about the card.
    """
    clean = number.replace(" ", "")
    if clean == TEST_DECLINE_CARD:
        return 'Failed', "test_decl_" + secrets.token_hex(8)
    return 'Successful', "test_ok_" + secrets.token_hex(8)
