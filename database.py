import aiosqlite
import os
from pathlib import Path


class Database:
    def __init__(self, db_path: str = "data/bot.db"):
        self.db_path = db_path
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """Ensure the data directory exists"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    async def connect(self):
        """Create database connection"""
        self.conn = await aiosqlite.connect(self.db_path)
        await self.init_db()

    async def close(self):
        """Close database connection"""
        await self.conn.close()

    async def init_db(self):
        """Initialize database tables"""
        # Example table - customize based on your needs
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await self.conn.commit()

    async def add_user(self, user_id: int, username: str = None, first_name: str = None):
        """Add or update user in database"""
        await self.conn.execute("""
            INSERT OR REPLACE INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
        """, (user_id, username, first_name))
        await self.conn.commit()

    async def get_user(self, user_id: int):
        """Get user from database"""
        cursor = await self.conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        )
        return await cursor.fetchone()
