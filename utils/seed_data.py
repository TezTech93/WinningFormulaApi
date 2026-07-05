# utils/seed_data.py
from sqlalchemy.orm import Session
from core.database import SessionLocal
from models.user import User, UserTier
from core.security import hash_password

def seed_users():
    db = SessionLocal()
    try:
        # Check if users exist
        if db.query(User).count() == 0:
            # Create a test user
            test_user = User(
                username="testuser",
                email="test@example.com",
                password_hash=hash_password("test123"),
                tier=UserTier.FREE
            )
            db.add(test_user)
            
            # Create the super user
            super_user = User(
                username="Shawntez32",
                email="shawnteztech93@gmail.com",
                password_hash=hash_password("Tezzyk32"),
                tier=UserTier.PLUS
            )
            db.add(super_user)
            
            db.commit()
            print("✅ Users seeded successfully")
            print(f"   - test@example.com / test123")
            print(f"   - shawnteztech93@gmail.com / Tezzyk32")
        else:
            print("✅ Users already exist")
            
    except Exception as e:
        print(f"❌ Error seeding users: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_users()