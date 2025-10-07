# config.py
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
SUPER_ADMINS_STR = os.getenv("SUPER_ADMINS", "")
SUPER_ADMINS = [int(admin_id.strip()) for admin_id in SUPER_ADMINS_STR.split(',') if admin_id]
VIP_STICKER_ID = os.getenv("VIP_STICKER_ID")
ADMIN_IDS = SUPER_ADMINS # Хабарлама жіберу үшін
