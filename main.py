import asyncio
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from aiogram import Bot, Dispatcher
from config import settings
from database.db import init_db
from webapp.routes import router as webapp_router
from bot.handlers import router as bot_router

# Lifespan Context Manager (FastAPI 0.115+ zamonaviy standarti)
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("⚡ Database muvaffaqiyatli ishga tushdi!")
    bot_task = None
    if settings.BOT_TOKEN and settings.BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
        print("🤖 Telegram Bot ishga tushmoqda...")
        bot_task = asyncio.create_task(dp.start_polling(bot))
    
    yield
    
    if bot_task:
        bot_task.cancel()

app = FastAPI(title="Telegram Giveaway Bot & WebApp", lifespan=lifespan)

# Localtunnel / Tunnel warning bypass middleware
@app.middleware("http")
async def add_tunnel_header(request, call_next):
    response = await call_next(request)
    response.headers["bypass-tunnel-reminder"] = "true"
    return response

# Static files & WebApp HTML route

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def serve_webapp():
    return FileResponse("frontend/index.html")

# REST API Router
app.include_router(webapp_router)

# Aiogram Bot setup
bot = Bot(token=settings.BOT_TOKEN) if settings.BOT_TOKEN != "YOUR_BOT_TOKEN_HERE" else None
dp = Dispatcher()
dp.include_router(bot_router)

if __name__ == "__main__":
    print("🚀 Giveaway App Server tayyorlanmoqda (Port 7070)...")
    uvicorn.run(app, host="0.0.0.0", port=7070)


