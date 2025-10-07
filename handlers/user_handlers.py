# handlers/user_handlers.py

import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CommandHandler,
    CallbackQueryHandler,
)
from telegram.constants import ParseMode

# Жобаның басқа модульдерінен импорттау
import database
from main import SUPER_ADMINS, VIP_GREETING_STICKER_ID, ADMIN_IDS

# Логгерді орнату
logger = logging.getLogger(__name__)

# --- ConversationHandler күйлері ---
(
    SEARCH_BY_NAME, SEARCH_BY_CODE, SEARCH_VIA_ADMIN,
    GET_REKLAMA, SUGGEST_REKLAMA,
    WAITING_SUPPORT_MESSAGE
) = range(6)


# --- Батырмалар (Keyboards) ---
# User Panel-ге қатысты батырмалар осы файлда болғаны ыңғайлы
def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Негізгі меню батырмалары."""
    keyboard = [
        [KeyboardButton("🎬 Anime Izlash"), KeyboardButton("📢 Reklama")],
        [KeyboardButton("👑 VIP"), KeyboardButton("📞 Support")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_anime_search_keyboard() -> ReplyKeyboardMarkup:
    """Аниме іздеу менюінің батырмалары."""
    keyboard = [
        [KeyboardButton("📝 Nomi orqali izlash"), KeyboardButton("🔢 Kod orqali izlash")],
        [KeyboardButton("📚 Barcha animelar"), KeyboardButton("🏆 Eng ko'p ko'rilgan 20 anime")],
        [KeyboardButton("🧑‍💻 Admin orqali izlash")],
        [KeyboardButton("⬅️ Orqaga")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
def get_back_keyboard() -> ReplyKeyboardMarkup:
    """Тек "Артқа" батырмасы бар меню."""
    return ReplyKeyboardMarkup([[KeyboardButton("⬅️ Orqaga")]], resize_keyboard=True)


# --- ОРТАҚ ФУНКЦИЯЛАР ---
async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Диалогты тоқтатып, негізгі менюге оралатын ортақ функция."""
    await update.message.reply_text("Asosiy menyuga qaytdingiz.", reply_markup=get_main_menu_keyboard())
    return ConversationHandler.END


# --- /START КОМАНДАСЫ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start командасын өңдейді, пайдаланушыны тіркейді және рөліне қарай меню жібереді."""
    user = update.effective_user
    try:
        database.add_or_update_user(user.id, user.username, user.first_name)
        role = database.get_user_role(user.id)
        
        if role == 'admin':
            await update.message.reply_text(f"Salom, Admin! Admin paneliga o'tish uchun /admin buyrug'ini bosing.")
            # Бұл жерде админ менюін көрсетуге де болады, бірақ бөлек командамен шақырған дұрыс
        elif role == 'vip':
            if VIP_GREETING_STICKER_ID:
                await context.bot.send_sticker(chat_id=user.id, sticker=VIP_GREETING_STICKER_ID)
            await update.message.reply_text(f"Xush kelibsiz, hurmatli VIP a'zo {user.first_name}!", reply_markup=get_main_menu_keyboard())
        else: # role == 'user'
            await update.message.reply_text(f"Xush kelibsiz, {user.first_name}!", reply_markup=get_main_menu_keyboard())
            
    except Exception as e:
        logger.error(f"/start buyrug'ida {user.id} uchun xatolik: {e}")
        await update.message.reply_text("Botda texnik nosozlik yuz berdi.")


# --- ANIME IZLASH БӨЛІМІ ---
async def to_anime_search_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎬 Anime izlash bo'limi. Kerakli buyruqni tanlang:", reply_markup=get_anime_search_keyboard())

# Аты бойынша іздеу
async def search_by_name_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Izlash uchun anime nomini yozing:", reply_markup=get_back_keyboard())
    return SEARCH_BY_NAME

async def search_by_name_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # database.py-дағы find_anime_by_name функциясын қолданамыз
    anime = database.find_anime_by_name(update.message.text)
    if anime:
        response = f"✅ Topildi!\n\n🎬 *Nomi:* {anime[2]}\n🔢 *Kodi:* `{anime[1]}`\n📄 *Tavsif:* {anime[3] or 'Mavjud emas'}"
        await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await update.message.reply_text("❌ Afsus, bunday nomdagi anime topilmadi.")
    await to_anime_search_menu(update, context) # Іздеуден кейін қайта менюге оралу
    return ConversationHandler.END

# Коды бойынша іздеу
async def search_by_code_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Izlash uchun anime kodini yozing:", reply_markup=get_back_keyboard())
    return SEARCH_BY_CODE

async def search_by_code_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    anime = database.find_anime_by_code(update.message.text)
    if anime:
        response = f"✅ Topildi!\n\n🎬 *Nomi:* {anime[2]}\n🔢 *Kodi:* `{anime[1]}`\n📄 *Tavsif:* {anime[3] or 'Mavjud emas'}"
        await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await update.message.reply_text("❌ Afsus, bunday kodli anime topilmadi.")
    await to_anime_search_menu(update, context)
    return ConversationHandler.END

# Барлық анимелер (беттеумен)
async def all_animes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (Бұл функцияның толық кодын келесіде ұсынамын, себебі ол күрделірек)
    await update.message.reply_text("Функция в разработке")

# Көп көрілгендер
async def top_animes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (Бұл функцияның толық кодын келесіде ұсынамын)
    await update.message.reply_text("Функция в разработке")

# Админ арқылы іздеу
async def search_via_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    role = database.get_user_role(update.effective_user.id)
    if role not in ['vip', 'admin']:
        await update.message.reply_text("Bu bo'lim faqat VIP a'zo yoki Adminlar uchun.")
        return ConversationHandler.END
    
    await update.message.reply_text("Izlayotgan animeingiz haqida qisqacha ma'lumot yozing:", reply_markup=get_back_keyboard())
    return SEARCH_VIA_ADMIN

async def search_via_admin_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_info = f"Foydalanuvchi: {update.effective_user.mention_html()} (ID: {update.effective_user.id})"
    for admin_id in ADMIN_IDS:
        await context.bot.send_message(admin_id, f"🧑‍💻 Yangi anime so'rovi!\n\n{user_info}\n\nSo'rov: {update.message.text}", parse_mode=ParseMode.HTML)
            
    await update.message.reply_text("✅ So'rovingiz adminga yuborildi.")
    await to_anime_search_menu(update, context)
    return ConversationHandler.END


# --- REKLAMA БӨЛІМІ ---
async def to_reklama_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Reklama olish"], ["Reklama taklif qilish"], ["⬅️ Orqaga"]]
    await update.message.reply_text("📢 Reklama bo'limi:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

# ... (Рекламаға қатысты толық диалогтар осында жазылады)


# --- VIP ЖӘНЕ SUPPORT БӨЛІМІ ---
async def vip_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    vip_desc = database.get_setting('vip_description')
    full_vip_info = (vip_desc or "VIP a'zolik haqida ma'lumot kiritilmagan.") + \
                    "\n\n👑 VIP A'zolik afzalliklari:\n" \
                    "1. VIP a'zolar uchun yaratilgan maxsus komandalarga kirish.\n" \
                    "2. Ular uchun maxsus reaksiya beriladi.\n" \
                    "3. 1 oy hech qanday kanalga obuna bo'lmasdan anime tomosha qilish.\n" \
                    "4. Yangi anime yuklanganda birinchi sizga jo'natiladi."
    await update.message.reply_text(full_vip_info)

async def to_support_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = "Agar jiddiy savol yoki yordam kerak bo'lsa-gina yozing.\nQanday yordam kerakligini yozing:"
    await update.message.reply_text(text, reply_markup=get_back_keyboard())
    return WAITING_SUPPORT_MESSAGE

async def support_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_info = f"Foydalanuvchi: {update.effective_user.mention_html()} (ID: {update.effective_user.id})"
    for admin_id in ADMIN_IDS:
        await context.bot.send_message(admin_id, f"🆘 Yordam so'rovi (Support)!\n\n{user_info}\n\nMurojaat: {update.message.text}", parse_mode=ParseMode.HTML)
    
    response = "✅ Xabaringiz yuborildi.\n⚠️ Eslatma: Agar xabaringiz jiddiy bo'lmasa, botdan chetlatilishingiz mumkin."
    await update.message.reply_text(response, reply_markup=get_main_menu_keyboard())
    return ConversationHandler.END


# --- БАРЛЫҚ ХЕНДЛЕРЛЕРДІ ТІРКЕЙТІН ФУНКЦИЯ ---
def register_user_handlers(application: Application):
    """Барлық User Panel хендлерлерін application-ға тіркейді."""
    
    # Conversation Handlers
    anime_search_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📝 Nomi orqali izlash$"), search_by_name_start),
            MessageHandler(filters.Regex("^🔢 Kod orqali izlash$"), search_by_code_start),
            MessageHandler(filters.Regex("^🧑‍💻 Admin orqali izlash$"), search_via_admin_start),
        ],
        states={
            SEARCH_BY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_by_name_receive)],
            SEARCH_BY_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_by_code_receive)],
            SEARCH_VIA_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_via_admin_receive)],
        },
        fallbacks=[MessageHandler(filters.Regex("^⬅️ Orqaga$"), back_to_main_menu)],
    )

    support_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📞 Support$"), to_support_menu)],
        states={WAITING_SUPPORT_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, support_receive)]},
        fallbacks=[MessageHandler(filters.Regex("^⬅️ Orqaga$"), back_to_main_menu)],
    )
    
    # ... (Басқа Conversation Handler-лер осында қосылады)

    # Негізгі командалар
    application.add_handler(CommandHandler("start", start))
    
    # Диалогтар
    application.add_handler(anime_search_conv)
    application.add_handler(support_conv)

    # Қарапайым батырмалар
    application.add_handler(MessageHandler(filters.Regex("^🎬 Anime Izlash$"), to_anime_search_menu))
    application.add_handler(MessageHandler(filters.Regex("^📢 Reklama$"), to_reklama_menu))
    application.add_handler(MessageHandler(filters.Regex("^👑 VIP$"), vip_info))
    application.add_handler(MessageHandler(filters.Regex("^📚 Barcha animelar$"), all_animes))
    application.add_handler(MessageHandler(filters.Regex("^🏆 Ko'p ko'rilgan 20 anime$"), top_animes))
    application.add_handler(MessageHandler(filters.Regex("^⬅️ Orqaga$"), back_to_main_menu))
    
    logger.info("User panel handler-lari muvaffaqiyatli o'rnatildi.")
