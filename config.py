import os
from pydantic import BaseModel

class Settings(BaseModel):
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "8895855607:AAFzkjhUmU7oVjkrnC6dnROYMZuszU6YSVM")
    WEBAPP_URL: str = os.getenv("WEBAPP_URL", "https://grumpy-planets-feel.loca.lt")  # ngrok yoki domen
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./giveaway.db")
    ADMIN_IDS: list[int] = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

settings = Settings()
