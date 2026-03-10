import datetime as dt
import typing
import sqlite3
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserTier:
    FREE = "FREE"  # 50 formulas(algorithms)
    PAID = "PAID"  # 500 formulas(algorithms)
    PLUS = "PLUS"  # 2000 formulas(algorithms)

class UserManager:
    def __init__(self, db_path: str = "winners_formula.db"):
        """Initialize with SQLite database path"""
        self.db_path = db_path
        self.connection = None
        self.init_db()

    def get_connection(self):
        """Get a database connection"""
        if not self.connection:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # This enables column access by name
        return self.connection

    def close_connection(self):
        """Close the database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def init_db(self):
        """Initialize database tables if they don't exist"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if tables exist
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='users'
            """)
            users_table_exists = cursor.fetchone() is not None
            
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='user_formulas'
            """)
            formulas_table_exists = cursor.fetchone() is not None
            
            if not users_table_exists:
                logger.info("Creating users table...")
                cursor.execute("""
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        tier TEXT DEFAULT 'FREE',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("Users table created successfully")
            
            if not formulas_table_exists:
                logger.info("Creating user_formulas table...")
                cursor.execute("""
                    CREATE TABLE user_formulas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        formula_id INTEGER NOT NULL,
                        formula_name TEXT NOT NULL,
                        formula TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)
                logger.info("User formulas table created successfully")
            
            # Create indexes for better performance
            logger.info("Creating indexes...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_formulas_user_id 
                ON user_formulas(user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_formulas_formula_id 
                ON user_formulas(formula_id)
            """)
            logger.info("Indexes created successfully")
            
            conn.commit()
            logger.info("Database initialization completed successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            if self.connection:
                self.connection.rollback()
            raise

    def create_user(self, username: str, email: str, password_hash: str) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash, tier, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (username, email, password_hash, UserTier.FREE, dt.datetime.utcnow())
        )
        conn.commit()
        user_id = cursor.lastrowid
        logger.info(f"User created with ID: {user_id}")
        return user_id

    def get_user_by_id(self, user_id: int) -> typing.Optional[dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, username, email, tier, created_at
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        )
        result = cursor.fetchone()
        if result:
            return dict(result)
        return None

    def get_user_by_email(self, email: str) -> typing.Optional[dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, username, email, tier, created_at
            FROM users
            WHERE email = ?
            """,
            (email,)
        )
        result = cursor.fetchone()
        if result:
            return dict(result)
        return None

    def update_user_password(self, user_id: int, new_password_hash: str) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE users
            SET password_hash = ?
            WHERE id = ?
            """,
            (new_password_hash, user_id)
        )
        conn.commit()
        success = cursor.rowcount > 0
        if success:
            logger.info(f"Password updated for user ID: {user_id}")
        return success

    def update_user_tier(self, user_id: int, tier: str) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE users
            SET tier = ?
            WHERE id = ?
            """,
            (tier, user_id)
        )
        conn.commit()
        success = cursor.rowcount > 0
        if success:
            logger.info(f"Tier updated to {tier} for user ID: {user_id}")
        return success

    def add_user_formula(self, user_id: int, formula_id: int, formula_name: str, formula: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO user_formulas (user_id, formula_id, formula_name, formula, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, formula_id, formula_name, formula, dt.datetime.utcnow())
        )
        conn.commit()
        logger.info(f"Formula added for user ID: {user_id}, formula ID: {formula_id}")

    def get_user_formulas(self, user_id: int) -> typing.List[dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, user_id, formula_id, formula_name, formula, created_at
            FROM user_formulas
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,)
        )
        results = cursor.fetchall()
        return [dict(row) for row in results]

    def get_formula_by_id(self, user_id: int, formula_record_id: int) -> typing.Optional[dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, user_id, formula_id, formula_name, formula, created_at
            FROM user_formulas
            WHERE user_id = ? AND id = ?
            """,
            (user_id, formula_record_id)
        )
        result = cursor.fetchone()
        if result:
            return dict(result)
        return None

    def delete_user_formula(self, user_id: int, formula_id: int) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM user_formulas
            WHERE user_id = ? AND id = ?
            """,
            (user_id, formula_id)
        )
        conn.commit()
        success = cursor.rowcount > 0
        if success:
            logger.info(f"Formula ID {formula_id} deleted for user ID: {user_id}")
        return success

    def get_formula_count(self, user_id: int) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) FROM user_formulas
            WHERE user_id = ?
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
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, username, email, tier, created_at
            FROM users
            ORDER BY created_at DESC
            """
        )
        results = cursor.fetchall()
        return [dict(row) for row in results]

    def delete_user(self, user_id: int) -> bool:
        """Delete a user and all their formulas (cascades due to foreign key)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM users
            WHERE id = ?
            """,
            (user_id,)
        )
        conn.commit()
        success = cursor.rowcount > 0
        if success:
            logger.info(f"User ID {user_id} deleted")
        return success

    def __del__(self):
        """Clean up connection when object is destroyed"""
        self.close_connection()