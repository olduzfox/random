import hmac
import hashlib
from urllib.parse import parse_qsl
from fastapi import HTTPException, Header, Depends
from config import settings

def verify_telegram_webapp_data(init_data: str) -> dict:
    """
    Telegram WebApp initData ni HMAC-SHA256 yordamida tekshirish.
    Soxtalashtirish va cheating ning oldini oladi.
    """
    if not init_data:
        raise HTTPException(status_code=401, detail="initData taqdim etilmadi")

    try:
        parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))
        if "hash" not in parsed_data:
            raise HTTPException(status_code=400, detail="Hash topilmadi")
        
        received_hash = parsed_data.pop("hash")
        
        # Kalitlarni alifbo bo'yicha saralash
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
        
        # Secret key: HMAC-SHA256("WebAppData", BOT_TOKEN)
        secret_key = hmac.new(b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256).digest()
        
        # Calculated hash: HMAC-SHA256(secret_key, data_check_string)
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        # Production muvofiqligi uchun (bot token sozlangan bo'lsa tekshiradi):
        if settings.BOT_TOKEN != "YOUR_BOT_TOKEN_HERE" and calculated_hash != received_hash:
            raise HTTPException(status_code=403, detail="Xavfsizlik tekshiruvi muvaffaqiyatsiz (Invalid initData hash)")
            
        return parsed_data
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=f"initData validation xatosi: {str(e)}")
