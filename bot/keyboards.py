from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from config import settings

def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="➕ Yangi Konkurs Yaratish", callback_data="create_contest")],
        [InlineKeyboardButton(text="📊 Mening Konkurslarim", callback_data="my_contests")],
        [InlineKeyboardButton(text="ℹ️ Yordam & Qo'llanma", callback_data="help_info")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_sponsors_keyboard(added_count: int = 0):
    keyboard = []
    if added_count > 0:
        keyboard.append([InlineKeyboardButton(text=f"✅ Tayyor! ({added_count} ta kanal qo'shildi)", callback_data="finish_sponsors")])
    keyboard.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_creation")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_contest_webapp_keyboard(contest_id: int, button_text: str = "🎉 Konkursda Qatnashish", bot_username: str = "irandsbot"):
    # Telegram Kanallarda ham WebApp oyna bo'lib ochilishi uchun Direct Mini App Link (t.me link) ishlatiladi!
    # Masalan: https://t.me/irandsbot/app?startapp=1
    url = f"https://t.me/{bot_username}/app?startapp={contest_id}"
    keyboard = [
        [InlineKeyboardButton(text=button_text, url=url)]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)



def get_publish_keyboard(contest_id: int, bot_username: str = ""):
    keyboard = [
        [InlineKeyboardButton(text="🚀 Kanallarga Avto-Xabar Yuborish", callback_data=f"publish_auto_{contest_id}")],
        [InlineKeyboardButton(text="🔗 Inline-Mode Orqali Ulashish", switch_inline_query=f"contest_{contest_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

