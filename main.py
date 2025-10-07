# main.py
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from telegram.constants import ParseMode

# --- 1. BOT KONFIGURATSIYASI (СІЗДІҢ НҰСҚАУЫҢЫЗ БОЙЫНША) ---
# .env файлының орнына, барлық баптаулар осында жазылады.
# VPS-те іске қоспас бұрын, осы жерді өзгертіңіз.
BOT_TOKEN = "8302815646:AAF8Rs82T7i3NvvamzaEdtqA5uEZHTU9dJk"  # Өз токеніңізді қойыңыз
SUPER_ADMINS = [7483732504]  # Өз Telegram ID-іңізді жазыңыз
VIP_GREETING_STICKER_ID = "CAACAgIAAxkBAAEj03Zl-YcxA0gVGt0p-5g0b5GJdF8pAwACeAcAAlw_CQc2Wd5PZXzm1zQE"
ADMIN_IDS = SUPER_ADMINS

# Логгингті баптау
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Басқа модульдерді импорттау ---
from database import init_db
from keep_alive import keep_alive
# Төмендегі екі файл келесі қадамдарда жасалады
# from handlers.user_handlers import register_user_handlers
# from handlers.admin_handlers import register_admin_handlers


# --- 2. БАТЫРМАЛАР (KEYBOARDS) ---
# Бұл бөлімде боттың барлық батырмалары жасалады

# --- User Panel батырмалары ---
def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Негізгі меню батырмалары."""
    keyboard = [
        [KeyboardButton("🎬 Anime Izlash"), KeyboardButton("📢 Reklama")],
        [KeyboardButton("👑 VIP"), KeyboardButton("📞 Support")]
    ]
    # Админдерге арнайы батырма қосу (бұл функция әлі жасалмайды)
    # if get_user_role(user_id) == 'admin':
    #     keyboard.append([KeyboardButton("👮 Admin Panelga o'tish")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_anime_search_keyboard() -> ReplyKeyboardMarkup:
    """Аниме іздеу менюінің батырмалары."""
    keyboard = [
        [KeyboardButton("📝 Nomi orquali izlash"), KeyboardButton("🔢 Kod orquali izlash")],
        [KeyboardButton("📚 Barcha animelar"), KeyboardButton("🏆 Ko'p ko'rilgan 20 anime")],
        [KeyboardButton("🧑‍💻 Admin orquali izlash")],
        [KeyboardButton("⬅️ Orqaga")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
def get_back_keyboard() -> ReplyKeyboardMarkup:
    """Тек "Артқа" батырмасы бар меню."""
    return ReplyKeyboardMarkup([[KeyboardButton("⬅️ Orqaga")]], resize_keyboard=True)

# --- Admin Panel батырмалары ---
def get_admin_main_keyboard() -> ReplyKeyboardMarkup:
    """Негізгі админ панелінің батырмалары."""
    keyboard = [
        [KeyboardButton("🎬 Anime Panel"), KeyboardButton("⚙️ Sozlamalar Panel")],
        [KeyboardButton("📬 Habar Yuborish"), KeyboardButton("👮 Admin Boshqarish")],
        [KeyboardButton("🗄️ Bazani Olish"), KeyboardButton("📤 Baza Yuklash")],
        [KeyboardButton("👤 User Panelga o'tish")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# --- 3. НЕГІЗГІ ФУНКЦИЯ (main) ---
# Ботты іске қосатын және барлық бөліктерді біріктіретін функция

def main() -> None:
    """Ботты іске қосады және барлық хендлерлерді тіркейді."""
    
    logger.info("Botni ishga tushirish boshlandi...")

    # 1. Деректер базасын дайындау
    # init_db функциясына SUPER_ADMINS тізімін береміз, себебі конфигурация осы файлда
    init_db(SUPER_ADMINS)

    # 2. Application-ды құру
    application = Application.builder().token(BOT_TOKEN).build()

    # 3. Хендлерлерді тіркеу
    # Бұл функциялар келесі қадамдарда жасалатын user_handlers.py және admin_handlers.py
    # файлдарынан келеді.
    
    # register_user_handlers(application)
    # register_admin_handlers(application)

    # 4. Веб-серверді іске қосу (VPS-те тұрақты жұмыс істеу үшін)
    keep_alive()
    
    # 5. Ботты іске қосу
    logger.info("Bot muvaffaqiyatli ishga tushdi va so'rovlarni qabul qilishni boshladi.")
    application.run_polling()

if __name__ == "__main__":
    main()

