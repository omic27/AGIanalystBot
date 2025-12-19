import re
import uuid

def parse_packages(packages_str: str) -> list[tuple[int,int]]:
    # "10:10,25:30"
    out = []
    for part in packages_str.split(","):
        part = part.strip()
        if not part:
            continue
        a, q = part.split(":")
        out.append((int(a), int(q)))
    return out

def safe_topic_title(user_id: int, username: str | None) -> str:
    base = f"User {user_id}"
    if username:
        base = f"@{username} ({user_id})"
    # Telegram topic title max ~128, clean
    base = re.sub(r"[^\w@\s\(\)\-\.]", "", base)
    return base[:120]

def new_payload_id() -> str:
    return uuid.uuid4().hex[:10]
