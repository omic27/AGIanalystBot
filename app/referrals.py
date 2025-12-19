import aiosqlite
from .db import get_user, inc_referrals, add_queries

async def process_referral(db: aiosqlite.Connection, inviter_code: str, new_user_id: int, bonus1: int, bonus5: int):
    # Find inviter by code
    cur = await db.execute("SELECT user_id FROM users WHERE ref_code=?", (inviter_code,))
    row = await cur.fetchone()
    if not row:
        return None

    inviter_id = int(row[0])
    if inviter_id == new_user_id:
        return None

    # Prevent double referral: if new user already has referred_by set
    cur2 = await db.execute("SELECT referred_by FROM users WHERE user_id=?", (new_user_id,))
    r2 = await cur2.fetchone()
    if r2 and r2[0]:
        return None

    # Set referred_by
    await db.execute("UPDATE users SET referred_by=? WHERE user_id=?", (inviter_id, new_user_id))
    await db.commit()

    await inc_referrals(db, inviter_id, 1)

    # Award bonuses
    await add_queries(db, inviter_id, bonus1)

    # If reached 5, add extra bonus5 (as milestone)
    cur3 = await db.execute("SELECT referrals_count FROM users WHERE user_id=?", (inviter_id,))
    r3 = await cur3.fetchone()
    if r3 and int(r3[0]) == 5:
        await add_queries(db, inviter_id, bonus5)

    return inviter_id
