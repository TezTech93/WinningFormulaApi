# routers/billing.py
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.dependencies import get_current_user
from models.user import User

router = APIRouter(prefix="/billing", tags=["billing"])
stripe.api_key = settings.STRIPE_SECRET_KEY

# Map our plan names to Stripe Price IDs (set in env)
PLANS = {
    "standard": settings.STRIPE_PRICE_STANDARD,
    "plus": settings.STRIPE_PRICE_PLUS,
}


class CheckoutRequest(BaseModel):
    plan: str


@router.post("/create-checkout-session")
async def create_checkout_session(
    body: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.plan not in PLANS:
        raise HTTPException(400, f"Invalid plan: {body.plan}")
    if not PLANS[body.plan]:
        raise HTTPException(500, f"Stripe price ID not configured for {body.plan}")

    # Create a Stripe Customer the first time this user subscribes
    if not current_user.stripe_customer_id:
        try:
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={"user_id": str(current_user.id)},
            )
        except stripe.error.StripeError as e:
            raise HTTPException(500, f"Stripe customer creation failed: {e.user_message or str(e)}")
        current_user.stripe_customer_id = customer.id
        db.commit()

    try:
        session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{"price": PLANS[body.plan], "quantity": 1}],
            mode="subscription",
            success_url="http://localhost:8081/?checkout=success",
            cancel_url="http://localhost:8081/?checkout=cancel",
            metadata={
                "user_id": str(current_user.id),
                "plan": body.plan,
            },
        )
    except stripe.error.StripeError as e:
        raise HTTPException(500, f"Stripe checkout failed: {e.user_message or str(e)}")

    return {"checkout_url": session.url}


@router.post("/create-portal-session")
async def create_portal_session(
    current_user: User = Depends(get_current_user),
):
    if not current_user.stripe_customer_id:
        raise HTTPException(400, "No Stripe customer for this user")
    try:
        session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url="http://localhost:8081/",
        )
    except stripe.error.StripeError as e:
        raise HTTPException(500, f"Stripe portal failed: {e.user_message or str(e)}")
    return {"portal_url": session.url}


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
):
    payload = await request.body()

    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(500, "STRIPE_WEBHOOK_SECRET not configured")

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(400, "Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid signature")

    # Open a fresh DB session — webhook runs outside the request scope
    from core.database import SessionLocal
    db = SessionLocal()
    try:
        event_type = event["type"]

        if event_type in ("checkout.session.completed", "customer.subscription.created", "customer.subscription.updated"):
            obj = event["data"]["object"]
            _handle_subscription_upsert(db, obj, event_type)
        elif event_type == "customer.subscription.deleted":
            obj = event["data"]["object"]
            _handle_subscription_deleted(db, obj)
        elif event_type == "invoice.payment_failed":
            obj = event["data"]["object"]
            _handle_payment_failed(db, obj)

    finally:
        db.close()

    return {"status": "ok"}


# --- Internal helpers ---

def _find_user_by_customer(db, customer_id):
    return db.query(User).filter(User.stripe_customer_id == customer_id).first()


def _handle_subscription_upsert(db, obj, event_type):
    customer_id = obj.get("customer")
    if not customer_id:
        return
    user = _find_user_by_customer(db, customer_id)
    if not user:
        print(f"[stripe] webhook: no user for customer {customer_id}")
        return

    # For checkout.session.completed, subscription fields live one level down
    sub_id = obj.get("subscription") or obj.get("id")
    status = obj.get("status") or "active"

    plan = None
    metadata = obj.get("metadata") or {}
    plan = metadata.get("plan")

    # Map status → our status vocabulary
    if status in ("active", "trialing"):
        our_status = "active"
    elif status in ("past_due", "unpaid"):
        our_status = "past_due"
    elif status in ("canceled", "incomplete_expired"):
        our_status = "canceled"
    else:
        our_status = "free"

    user.stripe_subscription_id = sub_id
    user.subscription_status = our_status
    if plan:
        user.subscription_tier = plan
    user.subscription_source = "stripe"
    db.commit()


def _handle_subscription_deleted(db, obj):
    customer_id = obj.get("customer")
    if not customer_id:
        return
    user = _find_user_by_customer(db, customer_id)
    if not user:
        return
    user.subscription_status = "canceled"
    user.subscription_tier = "free"
    user.stripe_subscription_id = None
    db.commit()


def _handle_payment_failed(db, obj):
    customer_id = obj.get("customer")
    if not customer_id:
        return
    user = _find_user_by_customer(db, customer_id)
    if not user:
        return
    user.subscription_status = "past_due"
    db.commit()