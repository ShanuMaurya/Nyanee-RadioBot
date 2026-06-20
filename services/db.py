import aiosqlite
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'radio.db')

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                dj_role_id INTEGER,
                channel_id INTEGER,
                station_url TEXT,
                station_name TEXT
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_favorites (
                user_id INTEGER,
                station_name TEXT,
                station_url TEXT,
                UNIQUE(user_id, station_url)
            )
        ''')
        await db.commit()

async def add_favorite(user_id: int, station_name: str, station_url: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('INSERT OR IGNORE INTO user_favorites (user_id, station_name, station_url) VALUES (?, ?, ?)', (user_id, station_name, station_url))
        await db.commit()

async def get_favorites(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT station_name, station_url FROM user_favorites WHERE user_id = ?', (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [{'name': row[0], 'url': row[1]} for row in rows]

async def remove_favorite(user_id: int, station_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('DELETE FROM user_favorites WHERE user_id = ? AND station_name = ?', (user_id, station_name))
        await db.commit()

async def get_guild_settings(guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT dj_role_id, channel_id, station_url, station_name FROM guild_settings WHERE guild_id = ?', (guild_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    'dj_role_id': row[0],
                    'channel_id': row[1],
                    'station_url': row[2],
                    'station_name': row[3]
                }
            return None

async def set_dj_role(guild_id: int, role_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO guild_settings (guild_id, dj_role_id)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET dj_role_id = excluded.dj_role_id
        ''', (guild_id, role_id))
        await db.commit()

async def set_24_7(guild_id: int, channel_id: int, station_url: str, station_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO guild_settings (guild_id, channel_id, station_url, station_name)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET 
                channel_id = excluded.channel_id,
                station_url = excluded.station_url,
                station_name = excluded.station_name
        ''', (guild_id, channel_id, station_url, station_name))
        await db.commit()

async def disable_24_7(guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            UPDATE guild_settings
            SET channel_id = NULL, station_url = NULL, station_name = NULL
            WHERE guild_id = ?
        ''', (guild_id,))
        await db.commit()

async def get_all_24_7_settings():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT guild_id, channel_id, station_url, station_name FROM guild_settings WHERE channel_id IS NOT NULL') as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    'guild_id': row[0],
                    'channel_id': row[1],
                    'station_url': row[2],
                    'station_name': row[3]
                } for row in rows
            ]
