# routers/billing.py
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from core.config import settings
from core.database import get_db
from core.dependencies import get_current_user
from models.user import User

router = APIRouter(prefix="/billing", tags=["billing"])
stripe.api_key = settings.STRIPE_SECRET_KEY

# Define your plans and their corresponding Stripe Price IDs
PLANS = {
    "standard": {"price_id": settings.STRIPE_PRICE_STANDARD, "name": "Standard"},
    "plus": {"price_id": settings.STRIPE_PRICE_PLUS, "name": "Plus"},
}

@router.post("/create-checkout-session")
async def create_checkout_session(
    plan: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Creates a Stripe Checkout Session for a new subscription."""
    if plan not in PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan")

    # Create a Stripe Customer if one doesn't exist for this user
    if not current_user.stripe_customer_id:
        customer = stripe.Customer.create(
            email=current_user.email,
            metadata={"user_id": current_user.id},
        )
        current_user.stripe_customer_id = customer.id
        db.commit()

    try:
        checkout_session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{"price": PLANS[plan]["price_id"], "quantity": 1}],
            mode="subscription",
            success_url="https://your-app.com/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="https://your-app.com/cancel",
            metadata={"user_id": current_user.id, "plan": plan},
        )
        return {"checkout_url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    """Handles all incoming Stripe webhook events."""
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Handle the event types
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        # Fulfill the purchase, e.g., update user's subscription in your DB
        # You would get the user_id from session.metadata
        # and the subscription_id from session.subscription
        # Then, update your user model.
    elif event["type"] == "invoice.paid":
        # Continue to provision the subscription as payments are made.
        pass
    elif event["type"] == "invoice.payment_failed":
        # The payment failed or the customer does not have a valid payment method.
        # The subscription becomes past_due.
        pass
    elif event["type"] == "customer.subscription.deleted":
        # The subscription has been canceled.
        pass

    return {"status": "ok"}

# routers/billing.py (add this)
@router.post("/create-portal-session")
async def create_portal_session(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No Stripe customer found")
    
    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url="https://your-app.com/account",
        )
        return {"portal_url": portal_session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))