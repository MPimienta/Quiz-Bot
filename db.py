import aiosqlite
import sqlite3
from config import DB_FILE

DB_NAME = "scores.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS score (
            user_id INTEGER PRIMARY KEY,
            score INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

async def get_user_score(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT score FROM score WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else 0

async def update_user_score(user_id, score):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO score (user_id, score)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET score=excluded.score
        """, (user_id, score))
        await db.commit()
