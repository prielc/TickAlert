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
        # Users table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Events table (matches, concerts, etc.)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                event_date TEXT,
                category TEXT DEFAULT 'football',
                team TEXT,
                venue TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Subscriptions table (users subscribed to events)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, event_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (event_id) REFERENCES events(event_id)
            )
        """)
        
        # Tickets table (tickets posted for sale)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                price TEXT,
                details TEXT,
                contact_info TEXT,
                is_sold INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (event_id) REFERENCES events(event_id)
            )
        """)
        
        # Notifications log (track sent notifications)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Rate limiting for spam prevention
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS rate_limits (
                user_id INTEGER PRIMARY KEY,
                last_ticket_post TIMESTAMP,
                ticket_count_today INTEGER DEFAULT 0,
                last_reset_date TEXT
            )
        """)
        
        await self.conn.commit()
        
        # Initialize default events (Beitar Jerusalem matches)
        await self._init_default_events()

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
