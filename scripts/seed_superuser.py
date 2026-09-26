# scripts/seed_superuser.py
"""
  python -m scripts.seed_superuser
"""
import logging
from core.config import settings
from core.database import SessionLocal
from models.user import User

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("seed-superuser")


def seed() -> bool:
    email = (settings.SUPERUSER_EMAIL or "").strip().lower()
    if not email:
        log.warning("SUPERUSER_EMAIL not set — skipping")
        return False

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            log.warning(f"No user found with email {email!r} — register first, then re-run")
            return False

        changed = False
        if not user.is_superuser:
            user.is_superuser = True
            changed = True
        if user.subscription_status != "active":
            user.subscription_status = "active"
            changed = True
        if user.subscription_tier != "plus":
            user.subscription_tier = "plus"
            changed = True
        if user.subscription_source != "superuser":
            user.subscription_source = "superuser"
            changed = True

        if changed:
            db.commit()
            log.info(f"✅ Superuser seeded: {email} (id={user.id})")
        else:
            log.info(f"✓ Superuser already configured: {email}")
        return True
    finally:
        db.close()


if __name__ == "__main__":
    seed()