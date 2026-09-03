# 🏆 Telegram Giveaway Bot & WebApp (Mini App)

Telegram kanallar uchun obunalarni tekshiruvchi, chiptalar tarqatuvchi va g'oliblarni tasodifiy aniqlovchi mukammal Bot va WebApp tizimi.

## 🚀 O'rnatish va Ishga tushirish

### 1. Reformat / Virtual Environment yaratish
```bash
python -m venv venv
venv\Scripts\activate   # Windows uchun
source venv/bin/activate # Linux/Mac uchun
pip install -r requirements.txt
```

### 2. Sozlamalar (`config.py` yoki `.env`)
`config.py` faylida o'zingizning Telegram Bot tokeningizni va domen manzilingizni kiriting:
```python
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
WEBAPP_URL = "https://your-domain-or-ngrok.ngrok-free.app"
```

### 3. Serverni ishga tushirish
```bash
python main.py
```
Server `http://localhost:8000` portida va Telegram Bot asinxron rejimda birga ishlaydi!

---

## 🎨 WebApp UI & Texnologiyalar
- **Backend:** FastAPI + SQLAlchemy (Async ORM) + Aiogram 3
- **Frontend:** Glassmorphism UI (TailwindCSS + WebApp SDK)
- **Xavfsizlik:** Telegram `initData` HMAC-SHA256 binar tekshiruvi.
