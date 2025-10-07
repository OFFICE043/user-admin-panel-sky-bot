# handlers/user_handlers.py
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CommandHandler,
)
from telegram.constants import ParseMode

# Жобаның басқа файлдарынан импорттау
import database
from keyboards import user_keyboards, admin_keyboards # main.py-дан көшірілді
from config import SUPER_ADMINS, VIP_GREETING_STICKER_ID, ADMIN_IDS

# Логгерді орнату
logger = logging.getLogger(__name__)

# ConversationHandler күйлері
SEARCH_BY_NAME, SEARCH_BY_CODE, GET_REKLAMA, SUGGEST_REKLAMA, WAITING_SUPPORT_MESSAGE, SEARCH_VIA_ADMIN = range(6)


# --- ОРТАҚ ФУНКЦИЯЛАР ---

async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Диалогты тоқтатып, негізгі менюге оралатын ортақ функция."""
    user_id = update.effective_user.id
    role = database.get_user_role(user_id)
    
    # Админ болса, админ менюіне қайтару
    if role == 'admin':
        await update.message.reply_text("👮 Asosiy admin panelidasiz.", reply_markup=admin_keyboards.get_admin_main_keyboard())
    else:
        await update.message.reply_text("Asosiy menyuga qaytdingiz.", reply_markup=user_keyboards.get_main_menu_keyboard())

    return ConversationHandler.END


# --- /START КОМАНДАСЫНЫҢ НЕГІЗГІ ЛОГИКАСЫ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start командасын өңдейді, пайдаланушыны тіркейді және рөліне қарай меню жібереді."""
    user = update.effective_user
    
    try:
        database.add_or_update_user(user.id, user.username, user.first_name)
        role = database.get_user_role(user.id)
        
        if role == 'admin':
            is_super = " (Bosh Admin)" if user.id in SUPER_ADMINS else ""
            # Админге арналған қарлы стикер
            if VIP_GREETING_STICKER_ID:
                await context.bot.send_sticker(chat_id=user.id, sticker=VIP_GREETING_STICKER_ID)
            await update.message.reply_text(
                f"Salom, Admin{is_super}! Admin paneliga xush kelibsiz.",
                reply_markup=admin_keyboards.get_admin_main_keyboard()
            )
        elif role == 'vip':
            if VIP_GREETING_STICKER_ID:
                await context.bot.send_sticker(chat_id=user.id, sticker=VIP_GREETING_STICKER_ID)
            await update.message.reply_text(
                f"Xush kelibsiz, hurmatli VIP a'zo {user.first_name}!",
                reply_markup=user_keyboards.get_main_menu_keyboard()
            )
        else: # role == 'user'
            await update.message.reply_text(
                f"Xush kelibsiz, {user.first_name}!",
                reply_markup=user_keyboards.get_main_menu_keyboard()
            )
    except Exception as e:
        logger.error(f"/start buyrug'ida {user.id} uchun xatolik: {e}")
        await update.message.reply_text("Botda texnik nosozlik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")


# --- ANIME IZLASH БӨЛІМІ ---

async def to_anime_search_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎬 Anime izlash bo'limi. Kerakli buyruqni tanlang:", reply_markup=user_keyboards.get_anime_search_keyboard())

async def search_by_name_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Izlash uchun anime nomini yozing:", reply_markup=user_keyboards.get_back_keyboard())
    return SEARCH_BY_NAME

async def search_by_name_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    anime = database.find_anime_by_name(update.message.text)
    if anime:
        response = f"✅ Topildi!\n\n🎬 *Nomi:* {anime[1]}\n🔢 *Kodi:* `{anime[0]}`" # PostgreSQL tuple индексі
        await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=user_keyboards.get_anime_search_keyboard())
    else:
        await update.message.reply_text("❌ Afsus, bunday nomdagi anime topilmadi.", reply_markup=user_keyboards.get_anime_search_keyboard())
    return ConversationHandler.END

async def search_by_code_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Izlash uchun anime kodini yozing (Masalan: A001):", reply_markup=user_keyboards.get_back_keyboard())
    return SEARCH_BY_CODE

async def search_by_code_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    anime = database.find_anime_by_code(update.message.text)
    if anime:
        response = f"✅ Topildi!\n\n🎬 *Nomi:* {anime[1]}\n🔢 *Kodi:* `{anime[0]}`"
        await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=user_keyboards.get_anime_search_keyboard())
    else:
        await update.message.reply_text("❌ Afsus, bunday kodli anime topilmadi.", reply_markup=user_keyboards.get_anime_search_keyboard())
    return ConversationHandler.END

async def all_animes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    role = database.get_user_role(update.effective_user.id)
    if role not in ['vip', 'admin']:
        await update.message.reply_text("Bu bo'lim faqat VIP a'zo yoki Adminlar uchun.")
        return
    
    animes_list = database.get_all_animes() # get_all_animes_paginated орнына
    if not animes_list:
        await update.message.reply_text("Hozircha animelar mavjud emas.")
        return

    text = "📚 Barcha animelar ro'yxati:\n\n"
    for i, anime in enumerate(animes_list, 1):
        text += f"{i}. `{anime[1]}` - {anime[2]}\n"
    
    # Егер хабарлама тым ұзын болса, бөліп жіберу керек
    if len(text) > 4096:
        for x in range(0, len(text), 4096):
            await update.message.reply_text(text[x:x+4096], parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)

async def top_animes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    role = database.get_user_role(update.effective_user.id)
    if role not in ['vip', 'admin']:
        await update.message.reply_text("Bu bo'lim faqat VIP a'zo yoki Adminlar uchun.")
        return
    
    # Бұл функцияны database.py файлына қосу керек: get_top_viewed_animes
    # top = database.get_top_viewed_animes()
    await update.message.reply_text("🏆 Eng ko'p ko'rilgan animelar (tez kunda)...")

async def search_via_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    role = database.get_user_role(update.effective_user.id)
    if role not in ['vip', 'admin']:
        await update.message.reply_text("Bu bo'lim faqat VIP a'zo yoki Adminlar uchun.")
        return ConversationHandler.END
    
    await update.message.reply_text("Izlayotgan animeingiz haqida qisqacha ma'lumot yozing:", reply_markup=user_keyboards.get_back_keyboard())
    return SEARCH_VIA_ADMIN

async def search_via_admin_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_info = f"Foydalanuvchi: {update.effective_user.mention_html()} (ID: {update.effective_user.id})"
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(admin_id, f"🧑‍💻 Yangi anime so'rovi!\n\n{user_info}\n\nSo'rov: {update.message.text}", parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.error(f"Adminga {admin_id} anime so'rovini yuborishda xatolik: {e}")
            
    await update.message.reply_text("✅ So'rovingiz adminga yuborildi.", reply_markup=user_keyboards.get_anime_search_keyboard())
    return ConversationHandler.END

# --- REKLAMA БӨЛІМІ ---
async def to_reklama_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Reklama olish"], ["Reklama taklif qilish"], ["⬅️ Orqaga"]]
    await update.message.reply_text("📢 Reklama bo'limi:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

async def reklama_olish_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = "Reklama olmoqchi bo'lsangiz, batafsil yozib yuboring (obuna kerakmi, qancha vaqtga va hokazo):"
    await update.message.reply_text(text, reply_markup=user_keyboards.get_back_keyboard())
    return GET_REKLAMA

async def reklama_olish_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_info = f"Foydalanuvchi: {update.effective_user.mention_html()} (ID: {update.effective_user.id})"
    for admin_id in ADMIN_IDS:
        await context.bot.send_message(admin_id, f"💸 Yangi reklama so'rovi!\n\n{user_info}\n\nXabar: {update.message.text}", parse_mode=ParseMode.HTML)
    await update.message.reply_text("✅ Xabaringiz adminga yuborildi.", reply_markup=user_keyboards.get_main_menu_keyboard())
    return ConversationHandler.END

async def reklama_taklif_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("O'zingizni taklifingizni yozing:", reply_markup=user_keyboards.get_back_keyboard())
    return SUGGEST_REKLAMA

async def reklama_taklif_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_info = f"Foydalanuvchi: {update.effective_user.mention_html()} (ID: {update.effective_user.id})"
    for admin_id in ADMIN_IDS:
        await context.bot.send_message(admin_id, f"💡 Yangi reklama taklifi!\n\n{user_info}\n\nTaklif: {update.message.text}", parse_mode=ParseMode.HTML)
    await update.message.reply_text("✅ Taklifingiz uchun rahmat! Xabaringiz adminga yuborildi.", reply_markup=user_keyboards.get_main_menu_keyboard())
    return ConversationHandler.END


# --- VIP ЖӘНЕ SUPPORT БӨЛІМІ ---
async def vip_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    vip_desc = database.get_setting('vip_description')
    final_text = vip_desc if vip_desc else "VIP a'zolik haqida ma'lumot hozircha kiritilmagan."
    
    # Сіздің сипаттамаңыздағыдай толық мәтін
    full_vip_info = f"{final_text}\n\n" \
                    "👑 VIP A'zolik afzalliklari:\n" \
                    "1. VIP a'zolar uchun yaratilgan maxsus komandalarga kirish.\n" \
                    "2. Ular uchun maxsus reaksiya beriladi.\n" \
                    "3. 1 oy hech qanday kanalga obuna bo'lmasdan anime tomosha qilish.\n" \
                    "4. Yangi anime yuklanganda birinchi sizga jo'natiladi."
    await update.message.reply_text(full_vip_info)

async def to_support_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = "Agar jiddiy savol yoki yordam kerak bo'lsa-gina yozing.\nQanday yordam kerakligini yozing:"
    await update.message.reply_text(text, reply_markup=user_keyboards.get_back_keyboard())
    return WAITING_SUPPORT_MESSAGE

async def support_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_info = f"Foydalanuvchi: {update.effective_user.mention_html()} (ID: {update.effective_user.id})"
    for admin_id in ADMIN_IDS:
        await context.bot.send_message(admin_id, f"🆘 Yordam so'rovi (Support)!\n\n{user_info}\n\nMurojaat: {update.message.text}", parse_mode=ParseMode.HTML)
    
    response = "✅ Xabaringiz yuborildi.\n⚠️ Eslatma: Agar xabaringiz jiddiy bo'lmasa, botdan chetlatilishingiz mumkin."
    await update.message.reply_text(response, reply_markup=user_keyboards.get_main_menu_keyboard())
    return ConversationHandler.END

# --- БАРЛЫҚ ХЕНДЛЕРЛЕРДІ ТІРКЕЙТІН ФУНКЦИЯ ---
def register_user_handlers(application: Application):
    """Барлық User Panel хендлерлерін application-ға тіркейді."""
    
    # Conversation Handlers
    anime_search_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📝 Nomi orquali izlash$"), search_by_name_start),
            MessageHandler(filters.Regex("^🔢 Kod orquali izlash$"), search_by_code_start),
            MessageHandler(filters.Regex("^🧑‍💻 Admin orquali izlash$"), search_via_admin_start),
        ],
        states={
            SEARCH_BY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_by_name_receive)],
            SEARCH_BY_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_by_code_receive)],
            SEARCH_VIA_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_via_admin_receive)],
        },
        fallbacks=[MessageHandler(filters.Regex("^⬅️ Orqaga$"), back_to_main_menu)],
    )

    reklama_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^Reklama olish$"), reklama_olish_start),
            MessageHandler(filters.Regex("^Reklama taklif qilish$"), reklama_taklif_start),
        ],
        states={
            GET_REKLAMA: [MessageHandler(filters.TEXT & ~filters.COMMAND, reklama_olish_receive)],
            SUGGEST_REKLAMA: [MessageHandler(filters.TEXT & ~filters.COMMAND, reklama_taklif_receive)],
        },
        fallbacks=[MessageHandler(filters.Regex("^⬅️ Orqaga$"), back_to_main_menu)],
    )

    support_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📞 Support$"), to_support_menu)],
        states={WAITING_SUPPORT_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, support_receive)]},
        fallbacks=[MessageHandler(filters.Regex("^⬅️ Orqaga$"), back_to_main_menu)],
    )
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(anime_search_conv)
    application.add_handler(reklama_conv)
    application.add_handler(support_conv)

    # Қарапайым батырмалар
    application.add_handler(MessageHandler(filters.Regex("^🎬 Anime Izlash$"), to_anime_search_menu))
    application.add_handler(MessageHandler(filters.Regex("^📢 Reklama$"), to_reklama_menu))
    application.add_handler(MessageHandler(filters.Regex("^👑 VIP$"), vip_info))
    application.add_handler(MessageHandler(filters.Regex("^📚 Barcha animelar$"), all_animes))
    application.add_handler(MessageHandler(filters.Regex("^🏆 Ko'p ko'rilgan 20 anime$"), top_animes))
    application.add_handler(MessageHandler(filters.Regex("^⬅️ Orqaga$"), back_to_main_menu))
    
    logger.info("User panel handler-lari muvaffaqiyatli o'rnatildi.")

