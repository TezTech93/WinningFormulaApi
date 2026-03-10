import datetime as dt
import typing
import psycopg2
from psycopg2 import sql
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserTier:
    FREE = "FREE"  # 50 formulas(algorithms)
    PAID = "PAID"  # 500 formulas(algorithms)
    PLUS = "PLUS"  # 2000 formulas(algorithms)

class UserManager:
    def __init__(self, connection: psycopg2.extensions.connection):
        self.connection = connection
        # Initialize tables when UserManager is created
        self.init_db()

    def init_db(self):
        """Initialize database tables if they don't exist"""
        try:
            with self.connection.cursor() as cursor:
                # Check if tables exist
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'users'
                    );
                """)
                users_table_exists = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'user_formulas'
                    );
                """)
                formulas_table_exists = cursor.fetchone()[0]
                
                if not users_table_exists:
                    logger.info("Creating users table...")
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            id SERIAL PRIMARY KEY,
                            username VARCHAR(50) UNIQUE NOT NULL,
                            email VARCHAR(255) UNIQUE NOT NULL,
                            password_hash VARCHAR(255) NOT NULL,
                            tier VARCHAR(20) DEFAULT 'FREE',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    logger.info("Users table created successfully")
                
                if not formulas_table_exists:
                    logger.info("Creating user_formulas table...")
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS user_formulas (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                            formula_id INTEGER NOT NULL,
                            formula_name VARCHAR(255) NOT NULL,
                            formula TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    logger.info("User formulas table created successfully")
                
                # Create indexes for better performance (if they don't exist)
                logger.info("Creating indexes...")
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                    CREATE INDEX IF NOT EXISTS idx_user_formulas_user_id ON user_formulas(user_id);
                    CREATE INDEX IF NOT EXISTS idx_user_formulas_formula_id ON user_formulas(formula_id);
                """)
                logger.info("Indexes created successfully")
                
                self.connection.commit()
                logger.info("Database initialization completed successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            self.connection.rollback()
            raise

    def create_user(self, username: str, email: str, password_hash: str) -> int:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (username, email, password_hash, tier, created_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (username, email, password_hash, UserTier.FREE, dt.datetime.utcnow())
            )
            user_id = cursor.fetchone()[0]
            self.connection.commit()
            logger.info(f"User created with ID: {user_id}")
            return user_id

    def get_user_by_id(self, user_id: int) -> typing.Optional[dict]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, username, email, tier, created_at
                FROM users
                WHERE id = %s
                """,
                (user_id,)
            )
            result = cursor.fetchone()
            if result:
                return {
                    "id": result[0],
                    "username": result[1],
                    "email": result[2],
                    "tier": result[3],
                    "created_at": result[4]
                }
            return None

    def get_user_by_email(self, email: str) -> typing.Optional[dict]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, username, email, tier, created_at
                FROM users
                WHERE email = %s
                """,
                (email,)
            )
            result = cursor.fetchone()
            if result:
                return {
                    "id": result[0],
                    "username": result[1],
                    "email": result[2],
                    "tier": result[3],
                    "created_at": result[4]
                }
            return None

    def update_user_password(self, user_id: int, new_password_hash: str) -> bool:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET password_hash = %s
                WHERE id = %s
                """,
                (new_password_hash, user_id)
            )
            self.connection.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Password updated for user ID: {user_id}")
            return success

    def update_user_tier(self, user_id: int, tier: str) -> bool:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET tier = %s
                WHERE id = %s
                """,
                (tier, user_id)
            )
            self.connection.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Tier updated to {tier} for user ID: {user_id}")
            return success

    def add_user_formula(self, user_id: int, formula_id: int, formula_name: str, formula: str):
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO user_formulas (user_id, formula_id, formula_name, formula, created_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, formula_id, formula_name, formula, dt.datetime.utcnow())
            )
            self.connection.commit()
            logger.info(f"Formula added for user ID: {user_id}, formula ID: {formula_id}")

    def get_user_formulas(self, user_id: int) -> typing.List[dict]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, user_id, formula_id, formula_name, formula, created_at
                FROM user_formulas
                WHERE user_id = %s
                ORDER BY created_at DESC
                """,
                (user_id,)
            )
            results = cursor.fetchall()
            formulas = []
            for result in results:
                formulas.append({
                    "id": result[0],
                    "user_id": result[1],
                    "formula_id": result[2],
                    "formula_name": result[3],
                    "formula": result[4],
                    "created_at": result[5]
                })
            return formulas

    def get_formula_by_id(self, user_id: int, formula_record_id: int) -> typing.Optional[dict]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, user_id, formula_id, formula_name, formula, created_at
                FROM user_formulas
                WHERE user_id = %s AND id = %s
                """,
                (user_id, formula_record_id)
            )
            result = cursor.fetchone()
            if result:
                return {
                    "id": result[0],
                    "user_id": result[1],
                    "formula_id": result[2],
                    "formula_name": result[3],
                    "formula": result[4],
                    "created_at": result[5]
                }
            return None

    def delete_user_formula(self, user_id: int, formula_id: int) -> bool:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM user_formulas
                WHERE user_id = %s AND id = %s
                """,
                (user_id, formula_id)
            )
            self.connection.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Formula ID {formula_id} deleted for user ID: {user_id}")
            return success

    def get_formula_count(self, user_id: int) -> int:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) FROM user_formulas
                WHERE user_id = %s
                """,
                (user_id,)
            )
            return cursor.fetchone()[0]

    def get_user_tier_limit(self, user_id: int) -> int:
        """Get the formula limit for a user based on their tier"""
        user = self.get_user_by_id(user_id)
        if not user:
            return 0
        
        tier = user.get("tier", UserTier.FREE)
        tier_limits = {
            UserTier.FREE: 50,
            UserTier.PAID: 500,
            UserTier.PLUS: 2000
        }
        return tier_limits.get(tier, 50)

    def can_add_formula(self, user_id: int) -> bool:
        """Check if user can add more formulas based on their tier limit"""
        current_count = self.get_formula_count(user_id)
        limit = self.get_user_tier_limit(user_id)
        return current_count < limit

    def get_all_users(self) -> typing.List[dict]:
        """Get all users (admin function)"""
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, username, email, tier, created_at
                FROM users
                ORDER BY created_at DESC
                """
            )
            results = cursor.fetchall()
            users = []
            for result in results:
                users.append({
                    "id": result[0],
                    "username": result[1],
                    "email": result[2],
                    "tier": result[3],
                    "created_at": result[4]
                })
            return users

    def delete_user(self, user_id: int) -> bool:
        """Delete a user and all their formulas (cascades due to foreign key)"""
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM users
                WHERE id = %s
                """,
                (user_id,)
            )
            self.connection.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info(f"User ID {user_id} deleted")
            return success