"""PAY-01.3 - Payment service in TEST mode only.

Uses Stripe test mode when the STRIPE_SECRET_KEY environment variable holds an
sk_test_ key. Otherwise a built-in mock is used, so the app and tests run with
no account. The caller passes a payment-method TOKEN (for example Stripe's test
token 'pm_card_visa'). Real card numbers are never passed in, stored or logged.
"""
import os
import uuid
from dataclasses import dataclass
from decimal import Decimal

try:
    import stripe
except ImportError:  # mock mode still works without the stripe package
    stripe = None

CURRENCY = os.environ.get("PAYMENT_CURRENCY", "cad")


@dataclass
class GatewayResult:
    ok: bool
    reference: str          # the only thing we store (transaction_token)
    message: str = ""


def _stripe_enabled() -> bool:
    key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not key:
        return False
    if not key.startswith("sk_test_"):
        raise RuntimeError("Only Stripe TEST keys (sk_test_...) are allowed in this project.")
    if stripe is None:
        raise RuntimeError("Install the stripe package: pip install stripe")
    stripe.api_key = key
    return True


def _cents(amount: Decimal) -> int:
    return int((Decimal(amount) * 100).to_integral_value())


def charge(amount: Decimal, payment_token: str, idempotency_key: str) -> GatewayResult:
    if not payment_token:
        return GatewayResult(False, "none", "No payment method provided.")
    if not _stripe_enabled():
        if "declin" in payment_token.lower():          # e.g. 'pm_card_chargeDeclined'
            return GatewayResult(False, "mock_declined_" + uuid.uuid4().hex[:8], "Your card was declined.")
        return GatewayResult(True, "mock_pi_" + uuid.uuid4().hex[:12])
    try:
        pi = stripe.PaymentIntent.create(
            amount=_cents(amount), currency=CURRENCY, payment_method=payment_token,
            confirm=True,
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            idempotency_key=idempotency_key,
        )
        if pi.status == "succeeded":
            return GatewayResult(True, pi.id)
        return GatewayResult(False, pi.id, "Payment was not completed.")
    except Exception as exc:  # stripe.error.CardError etc.
        return GatewayResult(False, "stripe_error", getattr(exc, "user_message", None) or str(exc))


def refund(reference: str, amount: Decimal) -> GatewayResult:
    if not _stripe_enabled() or reference.startswith("mock_"):
        return GatewayResult(True, "mock_re_" + uuid.uuid4().hex[:12])
    try:
        r = stripe.Refund.create(payment_intent=reference, amount=_cents(amount))
        return GatewayResult(True, r.id)
    except Exception as exc:
        return GatewayResult(False, "stripe_error", str(exc))
