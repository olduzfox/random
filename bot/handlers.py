from datetime import datetime, timedelta
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, CallbackQuery, InlineQuery, 
    InlineQueryResultArticle, InputTextMessageContent
)
from aiogram.fsm.context import FSMContext
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from database.db import AsyncSessionLocal
from database.models import Contest, SponsorChannel, User
from bot.keyboards import (
    get_main_keyboard, get_sponsors_keyboard, 
    get_contest_webapp_keyboard, get_publish_keyboard
)
from bot.states import CreateContestSG

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandStart = None):
    async with AsyncSessionLocal() as session:
        user = await session.get(User, message.from_user.id)
        if not user:
            user = User(
                id=message.from_user.id,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                username=message.from_user.username
            )
            session.add(user)
            await session.commit()

    # Agar startapp parameter kelgan bo'lsa (Masalan: /start contest_1)
    if command and command.args:
        args = command.args
        if args.startswith("contest_") or args.isdigit():
            contest_id = args.replace("contest_", "")
            url = f"{settings.WEBAPP_URL}/?contest_id={contest_id}"
            await message.answer(
                "🎉 **Konkursda qatnashish uchun pastdagi tugmani bosing:**",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🎁 WebApp ni Ochish", web_app=WebAppInfo(url=url))]
                ])
            )
            return

    text = (
        f"👋 **Assalomu alaykum, {message.from_user.first_name}!**\n\n"
        f"🏆 **Giveaway & Contest Bot**ga xush kelibsiz!\n"
        f"Ushbu bot orqali siz o'z kanallaringiz uchun mukammal konkurslar va sovg'alar o'yinini o'tkazishingiz mumkin.\n\n"
        f"Boshlash uchun pastdagi menyudan foydalaning:"
    )
    await message.answer(text, reply_markup=get_main_keyboard(), parse_mode="Markdown")


@router.callback_query(F.data == "create_contest")
async def start_create_contest(call: CallbackQuery, state: FSMContext):
    await state.set_state(CreateContestSG.title)
    await state.update_data(sponsors=[])
    await call.message.edit_text("📌 **1-Qadam:** Konkurs sarlavhasini (Title) kiriting:\n\n*Masalan: iPhone 15 Pro Max Giveaway!*")

@router.message(CreateContestSG.title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(CreateContestSG.description)
    await message.answer("📝 **2-Qadam:** Konkurs batafsil tavsifini (Description) kiriting:")

@router.message(CreateContestSG.description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(CreateContestSG.winner_count)
    await message.answer("🎁 **3-Qadam:** G'oliblar sonini kiriting (raqamda):\n\n*Masalan: 3*")

@router.message(CreateContestSG.winner_count)
async def process_winner_count(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("⚠️ Iltimos, faqat musbat raqam kiriting!")
    
    await state.update_data(winner_count=int(message.text))
    await state.set_state(CreateContestSG.duration_days)
    await message.answer("⏳ **4-Qadam:** Konkurs necha kun davom etsin? (kunlarda kiriting):\n\n*Masalan: 3*")

@router.message(CreateContestSG.duration_days)
async def process_duration_days(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("⚠️ Iltimos, faqat raqam kiriting!")
    
    await state.update_data(duration_days=int(message.text))
    await state.set_state(CreateContestSG.max_participants)
    await message.answer(
        "👥 **5-Qadam:** Maksimal qatnashchilar chegarasini kiriting (Auto-Stop):\n\n"
        "*(Muayyan son to'lganda konkurs avtomatik to'xtaydi, cheklov bo'lmasa 0 deb kiriting)*\n"
        "*Masalan: 100*"
    )

@router.message(CreateContestSG.max_participants)
async def process_max_participants(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("⚠️ Faqat raqam kiriting!")
    
    val = int(message.text)
    await state.update_data(max_participants=val if val > 0 else None)
    await state.set_state(CreateContestSG.sponsors)
    await message.answer(
        "📢 **6-Qadam:** Majburiy obuna kanallarini yuboring!\n\n"
        "Siz 2 xil usulda kanal qo'shishingiz mumkin:\n"
        "1. Kanal **@username**'ini yuboring (Masalan: `@mychannel`)\n"
        "2. O'sha kanaldan istalgan bir xabarni shu botga **Forward** qiling!\n\n"
        "*(Eslatma: Bot kanallarda Admin bo'lishi kerak!)*\n\n"
        "Barcha kanallarni yuborib bo'lgach, pastdagi **'✅ Tayyor!'** tugmasini bosing.",
        reply_markup=get_sponsors_keyboard(0)
    )


@router.callback_query(F.data == "cancel_creation")
async def cancel_creation_handler(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Konkurs yaratish bekor qilindi.", reply_markup=get_main_keyboard())

@router.message(CreateContestSG.sponsors)
async def process_sponsors(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    sponsors_list = data.get("sponsors", [])
    added_now = []

    if message.forward_from_chat:
        chat = message.forward_from_chat
        if chat.type in ["channel", "supergroup"]:
            invite_link = f"https://t.me/{chat.username}" if chat.username else f"https://t.me/c/{str(chat.id).replace('-100', '')}"
            added_now.append({
                "channel_id": chat.id,
                "title": chat.title or "Sponsor Channel",
                "invite_link": invite_link
            })
    else:
        lines = message.text.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            username = line.replace("https://t.me/", "").replace("@", "").strip()
            try:
                chat = await bot.get_chat(f"@{username}")
                invite_link = f"https://t.me/{chat.username}" if chat.username else f"https://t.me/{username}"
                added_now.append({
                    "channel_id": chat.id,
                    "title": chat.title or "Sponsor Channel",
                    "invite_link": invite_link
                })
            except Exception as e:
                await message.answer(f"⚠️ **Xatolik:** `{line}` kanali topilmadi yoki Bot ushbu kanalda admin emas!")

    if added_now:
        existing_ids = {s["channel_id"] for s in sponsors_list}
        for item in added_now:
            if item["channel_id"] not in existing_ids:
                sponsors_list.append(item)
                existing_ids.add(item["channel_id"])
        
        await state.update_data(sponsors=sponsors_list)
        
        channels_text = "\n".join([f"• {s['title']} ({s['invite_link']})" for s in sponsors_list])
        await message.answer(
            f"✅ **Kanal qo'shildi!**\n\n"
            f"📋 **Hozirgi qo'shilgan kanallar ({len(sponsors_list)} ta):**\n{channels_text}\n\n"
            f"Yana kanal yuborishingiz mumkin yoki bo'lsa pastdagi **'✅ Tayyor!'** tugmasini bosing:",
            reply_markup=get_sponsors_keyboard(len(sponsors_list))
        )
    else:
        await message.answer(
            "⚠️ Kanal topilmadi. Bot kanalda admin ekanligiga ishonch hosil qiling hamda @username yuboring!",
            reply_markup=get_sponsors_keyboard(len(sponsors_list))
        )


@router.callback_query(F.data == "finish_sponsors", CreateContestSG.sponsors)
async def finish_sponsors_step(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    sponsors = data.get("sponsors", [])
    if not sponsors:
        return await call.answer("⚠️ Kamida 1 ta kanal qo'shishingiz kerak!", show_alert=True)

    await state.set_state(CreateContestSG.button_text)
    await call.message.edit_text(
        "🔘 **5-Qadam:** Post ostidagi **Tugma matnini (Button Text)** kiriting:\n\n"
        "*Masalan:* `🎉 Konkursda Qatnashish` yoki `🎁 Sovg'ani Olish`"
    )

@router.message(CreateContestSG.button_text)
async def process_button_text(message: Message, state: FSMContext):
    button_text = message.text.strip()
    data = await state.get_data()
    
    days = data.get("duration_days", 7)
    start_dt = datetime.utcnow()
    end_dt = start_dt + timedelta(days=days)
    max_p = data.get("max_participants")

    # Bazaga saqlash
    async with AsyncSessionLocal() as session:
        new_contest = Contest(
            title=data["title"],
            description=data["description"],
            winner_count=data["winner_count"],
            max_participants=max_p,
            button_text=button_text,
            start_date=start_dt,
            end_date=end_dt,
            creator_id=message.from_user.id,
            is_active=True
        )
        session.add(new_contest)
        await session.commit()
        await session.refresh(new_contest)

        for s in data["sponsors"]:
            sp = SponsorChannel(
                contest_id=new_contest.id,
                channel_id=s["channel_id"],
                channel_title=s["title"],
                invite_link=s["invite_link"]
            )
            session.add(sp)
        await session.commit()
        contest_id = new_contest.id

    await state.clear()


    # Yaratilgan konkurs postining ko'rinishi
    post_text = (
        f"🎉 **{data['title']}**\n\n"
        f"{data['description']}\n\n"
        f"🏆 **G'oliblar soni:** {data['winner_count']} ta\n"
        f"👇 Konkursda qatnashish uchun pastdagi **{button_text}** tugmasini bosing!"
    )
    
    await message.answer(
        f"🎉 **Konkurs muvaffaqiyatli yaratildi! (ID: #{contest_id})**\n\n"
        f"Boshlash va postni kanallarga ulashish usulini tanlang:",
        reply_markup=get_publish_keyboard(contest_id)
    )
    
    # Namuna post
    await message.answer(post_text, reply_markup=get_contest_webapp_keyboard(contest_id, button_text))

@router.callback_query(F.data.startswith("publish_auto_"))
async def auto_publish_to_channels(call: CallbackQuery, bot: Bot):
    contest_id = int(call.data.split("_")[-1])
    
    async with AsyncSessionLocal() as session:
        stmt = select(Contest).where(Contest.id == contest_id).options(selectinload(Contest.sponsors))
        res = await session.execute(stmt)
        contest = res.scalar_one_or_none()

    if not contest:
        return await call.answer("Konkurs topilmadi", show_alert=True)

    post_text = (
        f"🔥 **KONKURS BOSHLANDI!** 🔥\n\n"
        f"🎉 **{contest.title}**\n\n"
        f"{contest.description}\n\n"
        f"🏆 **G'oliblar soni:** {contest.winner_count} ta\n"
        f"👇 Konkursda qatnashish va barcha shartlarni bajarish uchun pastdagi tugmani bosing!"
    )

    published_count = 0
    for sponsor in contest.sponsors:
        try:
            await bot.send_message(
                chat_id=sponsor.channel_id,
                text=post_text,
                reply_markup=get_contest_webapp_keyboard(contest.id, contest.button_text),
                parse_mode="Markdown"
            )
            published_count += 1
        except Exception as e:
            print(f"Channel publish error {sponsor.channel_id}: {e}")

    await call.answer(f"✅ {published_count} ta kanalga konkurs posti va tugmasi yuborildi!", show_alert=True)

# INLINE MODE (Inline-mode orqali istalgan chat / kanalga post joylash)
@router.inline_query()
async def inline_contest_handler(inline_query: InlineQuery, bot: Bot):
    query = inline_query.query.strip()
    
    # Masalan "contest_1" yoki "1"
    contest_id = None
    if query.startswith("contest_"):
        contest_id = int(query.replace("contest_", ""))
    elif query.isdigit():
        contest_id = int(query)

    if not contest_id:
        return

    async with AsyncSessionLocal() as session:
        stmt = select(Contest).where(Contest.id == contest_id)
        res = await session.execute(stmt)
        contest = res.scalar_one_or_none()

    if contest and contest.is_active:
        post_text = (
            f"🎉 **{contest.title}**\n\n"
            f"{contest.description}\n\n"
            f"🏆 **G'oliblar soni:** {contest.winner_count} ta\n"
            f"👇 Konkursda qatnashish uchun pastdagi **{contest.button_text}** tugmasini bosing!"
        )

        item = InlineQueryResultArticle(
            id=str(contest.id),
            title=f"🏆 Konkurs #{contest.id}: {contest.title}",
            description="Ushbu postni kanalga ulashish uchun bosing",
            input_message_content=InputTextMessageContent(
                message_text=post_text,
                parse_mode="Markdown"
            ),
            reply_markup=get_contest_webapp_keyboard(contest.id, contest.button_text)
        )
        await bot.answer_inline_query(inline_query.id, results=[item], cache_time=1)


