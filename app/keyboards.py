from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚽ Получить прогноз", callback_data="menu:forecast")],
        [InlineKeyboardButton(text="📊 Мой кабинет", callback_data="menu:cabinet")],
        [InlineKeyboardButton(text="👥 Рефералы", callback_data="menu:ref")],
        [InlineKeyboardButton(text="💳 Пополнить запросы", callback_data="menu:pay")],
        [InlineKeyboardButton(text="🆘 Поддержка", callback_data="menu:support")],
    ])

def match_confirm_kb(payload_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, верно", callback_data=f"match:ok:{payload_id}")],
        [InlineKeyboardButton(text="🔁 Нет, отправлю другой", callback_data=f"match:no:{payload_id}")],
    ])

def pay_network_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="USDT (TON)", callback_data="pay:net:USDT_TON")],
        [InlineKeyboardButton(text="USDT (TRON)", callback_data="pay:net:USDT_TRON")],
        [InlineKeyboardButton(text="TON", callback_data="pay:net:TON")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:back")],
    ])

def packages_kb(packages: list[tuple[int,int]], network: str):
    rows = []
    for amount, queries in packages:
        rows.append([InlineKeyboardButton(text=f"${amount} → {queries} запросов", callback_data=f"pay:pkg:{network}:{amount}")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:pay")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def pay_after_instruction_kb(payment_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"pay:paid:{payment_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:pay")],
    ])

def admin_payment_kb(payment_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"admin:pay:approve:{payment_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin:pay:reject:{payment_id}")
        ]
    ])
