import aiosqlite
import secrets
import time

DB_PATH = "bot.sqlite3"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS users (
  user_id INTEGER PRIMARY KEY,
  username TEXT,
  created_at INTEGER NOT NULL,
  queries_balance INTEGER NOT NULL DEFAULT 0,
  ref_code TEXT UNIQUE,
  referred_by INTEGER,
  referrals_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS topics (
  user_id INTEGER PRIMARY KEY,
  topic_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS payments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  network TEXT NOT NULL,
  amount_usd INTEGER NOT NULL,
  queries_to_add INTEGER NOT NULL,
  wallet TEXT NOT NULL,
  memo TEXT NOT NULL,
  status TEXT NOT NULL, -- pending/approved/rejected
  created_at INTEGER NOT NULL,
  tx_proof TEXT
);

CREATE TABLE IF NOT EXISTS forecasts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  match_text TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  response TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reminders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  text TEXT NOT NULL,
  send_at INTEGER NOT NULL,
  sent INTEGER NOT NULL DEFAULT 0
);
"""

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()

def _now() -> int:
    return int(time.time())

def _gen_ref_code() -> str:
    return secrets.token_hex(3).upper()  # 6 chars

def _gen_memo() -> str:
    return secrets.token_hex(3).upper()

async def get_user(db: aiosqlite.Connection, user_id: int):
    cur = await db.execute("SELECT user_id, username, queries_balance, ref_code, referred_by, referrals_count FROM users WHERE user_id=?",
                           (user_id,))
    return await cur.fetchone()

async def create_user_if_needed(db: aiosqlite.Connection, user_id: int, username: str | None, start_queries: int, referred_by: int | None):
    row = await get_user(db, user_id)
    if row:
        # update username if changed
        await db.execute("UPDATE users SET username=? WHERE user_id=?", (username or "", user_id))
        await db.commit()
        return

    ref_code = _gen_ref_code()
    created_at = _now()

    # Ensure unique ref_code
    for _ in range(5):
        try:
            await db.execute(
                "INSERT INTO users(user_id, username, created_at, queries_balance, ref_code, referred_by) VALUES(?,?,?,?,?,?)",
                (user_id, username or "", created_at, start_queries, ref_code, referred_by),
            )
            await db.commit()
            return
        except aiosqlite.IntegrityError:
            ref_code = _gen_ref_code()

    raise RuntimeError("Failed to generate unique ref_code")

async def add_queries(db: aiosqlite.Connection, user_id: int, amount: int):
    await db.execute("UPDATE users SET queries_balance = queries_balance + ? WHERE user_id=?", (amount, user_id))
    await db.commit()

async def spend_query(db: aiosqlite.Connection, user_id: int, amount: int = 1) -> bool:
    cur = await db.execute("SELECT queries_balance FROM users WHERE user_id=?", (user_id,))
    row = await cur.fetchone()
    if not row:
        return False
    bal = int(row[0])
    if bal < amount:
        return False
    await db.execute("UPDATE users SET queries_balance = queries_balance - ? WHERE user_id=?", (amount, user_id))
    await db.commit()
    return True

async def create_payment(db: aiosqlite.Connection, user_id: int, network: str, amount_usd: int, queries_to_add: int, wallet: str):
    memo = _gen_memo()
    created_at = _now()
    await db.execute(
        "INSERT INTO payments(user_id, network, amount_usd, queries_to_add, wallet, memo, status, created_at) VALUES(?,?,?,?,?,?,?,?)",
        (user_id, network, amount_usd, queries_to_add, wallet, memo, "pending", created_at),
    )
    await db.commit()
    cur = await db.execute("SELECT last_insert_rowid()")
    row = await cur.fetchone()
    return int(row[0]), memo

async def set_payment_proof(db: aiosqlite.Connection, payment_id: int, proof: str):
    await db.execute("UPDATE payments SET tx_proof=? WHERE id=?", (proof, payment_id))
    await db.commit()

async def get_payment(db: aiosqlite.Connection, payment_id: int):
    cur = await db.execute("SELECT id,user_id,network,amount_usd,queries_to_add,wallet,memo,status,tx_proof FROM payments WHERE id=?",
                           (payment_id,))
    return await cur.fetchone()

async def set_payment_status(db: aiosqlite.Connection, payment_id: int, status: str):
    await db.execute("UPDATE payments SET status=? WHERE id=?", (status, payment_id))
    await db.commit()

async def save_forecast(db: aiosqlite.Connection, user_id: int, match_text: str, response: str):
    await db.execute(
        "INSERT INTO forecasts(user_id, match_text, created_at, response) VALUES(?,?,?,?)",
        (user_id, match_text, _now(), response),
    )
    await db.commit()

async def get_or_create_topic(db: aiosqlite.Connection, user_id: int):
    cur = await db.execute("SELECT topic_id, title FROM topics WHERE user_id=?", (user_id,))
    return await cur.fetchone()

async def save_topic(db: aiosqlite.Connection, user_id: int, topic_id: int, title: str):
    await db.execute(
        "INSERT OR REPLACE INTO topics(user_id, topic_id, title, created_at) VALUES(?,?,?,?)",
        (user_id, topic_id, title, _now()),
    )
    await db.commit()

async def inc_referrals(db: aiosqlite.Connection, inviter_user_id: int, inc: int = 1):
    await db.execute("UPDATE users SET referrals_count = referrals_count + ? WHERE user_id=?", (inc, inviter_user_id))
    await db.commit()
