# main.py
import logging
from telegram.ext import Application
import database
from keep_alive import keep_alive

# --- 1. BOT KONFIGURATSIYASI (БАРЛЫҚ БАПТАУЛАР ОСЫ ЖЕРДЕ) ---
# .env және config.py файлдарының орнына
BOT_TOKEN = "8010754306:AAGdFobrMQB9nMy4d1-A-4ybGEzjNBknmuk"  # Өз токеніңізді қойыңыз
SUPER_ADMINS = [7483732504]  # Өз Telegram ID-іңізді жазыңыз
VIP_GREETING_STICKER_ID = "CAACAgIAAxkBAAEj03Zl-YcxA0gVGtоp-5g0b5GJdF8pAwACeAcAAlw_CQc2Wd5PZXzm1zQE"
ADMIN_IDS = SUPER_ADMINS

# --- Хендлерлерді импорттау ---
# Бұл файлдар келесі қадамдарда жасалады
# from handlers.user_handlers import register_user_handlers
# from handlers.admin_handlers import register_admin_handlers

def main() -> None:
    """Ботты іске қосатын негізгі функция"""
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
    
    # Дерекқорды дайындау
    # Баптауларды осы файлдан тікелей алады
    database.init_db(SUPER_ADMINS, DATABASE_URL)

    # Бот экземплярын құру
    application = Application.builder().token(BOT_TOKEN).build()

    # Пайдаланушы хендлерлерін тіркеу (келесіде қосылады)
    # register_user_handlers(application)
    
    # Әкімші хендлерлерін тіркеу (келесіде қосылады)
    # register_admin_handlers(application)

    # Веб-серверді іске қосу
    keep_alive()

    # Ботты іске қосу
    logging.info("Bot ishga tushdi...")
    application.run_polling()

if __name__ == "__main__":
    main()

