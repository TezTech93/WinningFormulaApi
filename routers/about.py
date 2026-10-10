# routers/about.py
from fastapi import APIRouter
from core.config import settings

router = APIRouter(tags=["about"])


@router.get("/about")
async def about():
    """
    Public app metadata endpoint. No auth required.
    Frontend hits this on first launch to fetch version, links, and plan info.
    """
    return {
        "app_name": "Winning Formula",
        "version": "1.0.0",
        "description": "Sports analytics, gamelines, and betting insights.",
        "contact": {
            "support_email": "support@winningformula.com",
            "website": "https://winningformula.com",
        },
        "plans": [
            {
                "id": "standard",
                "name": "Standard",
                "price_usd": 3.99,
                "billing_period": "month",
                "features": [
                    "Players",
                    "Formulas",
                    "Parlays",
                    "Predictions",
                ],
            },
            {
                "id": "plus",
                "name": "Plus",
                "price_usd": 5.99,
                "billing_period": "month",
                "features": [
                    "Everything in Standard",
                    "Monte Carlo simulations",
                    "Advanced analytics",
                ],
            },
        ],
        "supported_sports": ["nfl", "nba", "mlb", "nhl", "ncaab", "ncaaf"],
        "terms_url": "https://winningformula.com/terms",
        "privacy_url": "https://winningformula.com/privacy",
    }