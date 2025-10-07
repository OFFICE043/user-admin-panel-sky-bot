# main.py
import logging
from telegram.ext import Application
from config import BOT_TOKEN
import database

# from handlers.user_handlers import register_user_handlers
# from handlers.admin_handlers import register_admin_handlers

def main() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    
    # Дерекқорды дайындау
    database.init_db()

    # Ботты құру
    application = Application.builder().token(BOT_TOKEN).build()

    # --- Хендлерлерді тіркеу (келесі қадамдарда іске асады) ---
    # register_user_handlers(application)
    # register_admin_handlers(application)

    # Ботты іске қосу
    logging.info("Bot ishga tushdi...")
    application.run_polling()

if __name__ == "__main__":
    main()
