import json
import random
import string
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from database.db import get_db
from database.models import Contest, User, Participant, SponsorChannel
from webapp.security import verify_telegram_webapp_data
from aiogram import Bot
from config import settings

router = APIRouter(prefix="/api", tags=["webapp"])
bot = Bot(token=settings.BOT_TOKEN) if settings.BOT_TOKEN != "YOUR_BOT_TOKEN_HERE" else None

@router.get("/contest/{contest_id}")
async def get_contest_details(
    contest_id: int,
    x_telegram_init_data: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    # Telegram Auth Data
    user_data = {}
    if x_telegram_init_data:
        parsed = verify_telegram_webapp_data(x_telegram_init_data)
        if "user" in parsed:
            user_data = json.loads(parsed["user"])

    user_id = user_data.get("id")

    # Contest ma'lumotlarini olish
    stmt = (
        select(Contest)
        .where(Contest.id == contest_id)
        .options(selectinload(Contest.sponsors), selectinload(Contest.participants))
    )
    result = await db.execute(stmt)
    contest = result.scalar_one_or_none()

    if not contest:
        raise HTTPException(status_code=404, detail="Konkurs topilmadi")

    # Foydalanuvchi allaqachon qo'shilganmi?
    is_joined = False
    ticket_code = None
    if user_id:
        p_stmt = select(Participant).where(
            Participant.contest_id == contest_id,
            Participant.user_id == user_id
        )
        p_res = await db.execute(p_stmt)
        participant = p_res.scalar_one_or_none()
        if participant:
            is_joined = True
            ticket_code = participant.ticket_code

    sponsors_list = []
    for s in contest.sponsors:
        # Obuna holatini tekshirish (Bot API orqali)
        is_subbed = False
        if user_id and settings.BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
            try:
                member = await bot.get_chat_member(chat_id=s.channel_id, user_id=user_id)
                if member.status in ["creator", "administrator", "member", "restricted"]:
                    is_subbed = True
            except Exception:
                is_subbed = False

        sponsors_list.append({
            "id": s.id,
            "title": s.channel_title,
            "invite_link": s.invite_link,
            "is_subscribed": is_subbed
        })

    return {
        "id": contest.id,
        "title": contest.title,
        "description": contest.description,
        "media_url": contest.media_url,
        "end_date": contest.end_date.isoformat(),
        "is_active": contest.is_active,
        "participants_count": len(contest.participants),
        "max_participants": contest.max_participants,
        "is_joined": is_joined,
        "ticket_code": ticket_code,
        "sponsors": sponsors_list,
        "user_info": user_data
    }


@router.post("/contest/{contest_id}/join")
async def join_contest(
    contest_id: int,
    x_telegram_init_data: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    parsed = verify_telegram_webapp_data(x_telegram_init_data)
    if "user" not in parsed:
        raise HTTPException(status_code=400, detail="Foydalanuvchi ma'lumotlari topilmadi")

    user_info = json.loads(parsed["user"])
    user_id = user_info["id"]

    # User ni DB ga saqlash / yangilash
    user = await db.get(User, user_id)
    if not user:
        user = User(
            id=user_id,
            first_name=user_info.get("first_name", "User"),
            last_name=user_info.get("last_name"),
            username=user_info.get("username")
        )
        db.add(user)
        await db.commit()

    # Contest tekshirish
    stmt = (
        select(Contest)
        .where(Contest.id == contest_id)
        .options(selectinload(Contest.sponsors))
    )
    result = await db.execute(stmt)
    contest = result.scalar_one_or_none()

    if not contest or not contest.is_active:
        raise HTTPException(status_code=400, detail="Konkurs tugatilgan yoki faol emas!")

    # Maksimal qatnashchilar soni to'lgan bo'lsa auto-stop
    if contest.max_participants and len(contest.participants) >= contest.max_participants:
        contest.is_active = False
        await db.commit()
        raise HTTPException(status_code=400, detail="⚠️ Ushrbu konkursda maksimal ishtirokchilar soni to'ldi!")


    # Allaqachon qatnashganmi?
    p_stmt = select(Participant).where(
        Participant.contest_id == contest_id,
        Participant.user_id == user_id
    )
    p_res = await db.execute(p_stmt)
    if p_res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Siz allaqachon ushbu konkursda qatnashgansiz!")

    # Barcha kanallarga obuna bo'lganligini qat'iy tekshirish
    if settings.BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
        unsubscribed_channels = []
        for s in contest.sponsors:
            try:
                member = await bot.get_chat_member(chat_id=s.channel_id, user_id=user_id)
                if member.status not in ["creator", "administrator", "member", "restricted"]:
                    unsubscribed_channels.append(s.channel_title)
            except Exception:
                unsubscribed_channels.append(s.channel_title)

        if unsubscribed_channels:
            raise HTTPException(
                status_code=400, 
                detail=f"Siz hali barcha kanallarga obuna bo'lmadingiz: {', '.join(unsubscribed_channels)}"
            )

    # Ticket generator (masalan: TKT-884A2)
    ticket_code = "TKT-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    
    new_participant = Participant(
        contest_id=contest_id,
        user_id=user_id,
        ticket_code=ticket_code
    )
    db.add(new_participant)
    await db.commit()

    return {
        "success": True,
        "message": "Tabriklaymiz! Siz konkursda muvaffaqiyatli ro'yxatdan o'tdingiz.",
        "ticket_code": ticket_code
    }
