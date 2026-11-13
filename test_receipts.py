# Author: Dheeraj Bashal (Student ID: 169057697) - Group 22, CP317A
"""PAY-03.3 Test receipts (+ rule tests for PAY-01.1 and PAY-02.1).
A receipt shows the amount paid and the balance. These tests check the numbers a receipt is built from.
Run:  python test_receipts.py     (no MySQL needed)
"""
import payment_rules as p

TOTAL = 135.0

# Full payment: nothing left to pay
full = [('Full Payment', 135.0, 'Successful')]
assert p.amount_paid(full) == 135.0 and p.balance_due(TOTAL, full) == 0.0

# Deposit: 20% paid, the rest is the balance
assert p.deposit_amount(TOTAL) == 27.0
dep = [('Deposit', p.deposit_amount(TOTAL), 'Successful')]
assert p.amount_paid(dep) == 27.0 and p.balance_due(TOTAL, dep) == 108.0

# Deposit followed by the balance payment
both = dep + [('Full Payment', 108.0, 'Successful')]
assert p.balance_due(TOTAL, both) == 0.0

# A failed payment does not count, so no receipt amount
assert p.amount_paid([('Full Payment', 135.0, 'Failed')]) == 0.0
assert p.balance_due(TOTAL, [('Full Payment', 135.0, 'Failed')]) == 135.0

# A refund reduces the amount paid (cancelled booking)
refunded = full + [('Refund', 135.0, 'Refunded')]
assert p.amount_paid(refunded) == 0.0

# Card checks (format only) and test-mode gateway
assert p.validate_card("4242 4242 4242 4242", "12/28", "123") == (True, "")
assert p.validate_card("1234 5678 9012 3456", "12/28", "123")[1] == "Enter a valid card number."
assert p.validate_card("4242424242424242", "13/28", "123")[1] == "Enter the expiry date as MM/YY."
assert p.validate_card("4242424242424242", "12/28", "12")[1] == "Enter the 3 or 4 digit security code."
status, token = p.process_test_payment("4242 4242 4242 4242")
assert status == 'Successful' and token.startswith("test_ok_") and "4242" not in token
status, token = p.process_test_payment(p.TEST_DECLINE_CARD)
assert status == 'Failed' and token.startswith("test_decl_")
assert set(p.PAYMENT_TYPES) == {'Deposit', 'Full Payment', 'Refund'}

print("All payment and receipt tests passed.")
