# handlers/admin_handlers.py
import logging
import datetime
from telegram import Update
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
from keyboards import admin_keyboards, user_keyboards
from config import SUPER_ADMINS

# Логгерді орнату
logger = logging.getLogger(__name__)

# ConversationHandler күйлері
(
    # Anime Panel
    ANIME_UPLOAD_DATA, ANIME_EDIT_CODE, ANIME_EDIT_NEW_DATA, ANIME_DELETE_CODE,
    # Settings Panel
    VIP_DESC_EDIT, VIP_PRICE_EDIT, GIVE_VIP_DATA, REMOVE_VIP_ID,
    # Admin Management
    ADD_ADMIN_ID, REMOVE_ADMIN_ID,
    # Broadcast
    BROADCAST_MESSAGE,
) = range(12)


# --- КӨМЕКШІ ФУНКЦИЯЛАР ---

async def is_admin(user_id: int) -> bool:
    """Пайдаланушының админ екенін тексереді."""
    return database.get_user_role(user_id) == 'admin'

async def is_super_admin(user_id: int) -> bool:
    """Пайдаланушының супер-админ екенін тексереді."""
    return user_id in SUPER_ADMINS


# --- НЕГІЗГІ НАВИГАЦИЯ ---

async def to_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Негізгі админ панеліне оралу (диалогтар үшін де)."""
    if not await is_admin(update.effective_user.id): return ConversationHandler.END
    await update.message.reply_text("👮 Asosiy admin panelidasiz.", reply_markup=admin_keyboards.get_admin_main_keyboard())
    return ConversationHandler.END

async def switch_to_user_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id): return
    await update.message.reply_text(
        "👤 Siz hozir oddiy foydalanuvchi panelidasiz.\n"
        "Admin paneliga qaytish uchun /start buyrug'ini bosing.",
        reply_markup=user_keyboards.get_main_menu_keyboard()
    )


# --- ANIME PANEL БӨЛІМІ ---

async def to_anime_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id): return
    await update.message.reply_text("🎬 Anime Boshqaruv Paneli", reply_markup=admin_keyboards.get_anime_panel_keyboard())

# 1. Аниме жүктеу
async def anime_upload_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Anime yuklash uchun ma'lumotlarni bitta xabarda, probel bilan ajratib yozing:\n\n"
        "`kodi kanal_username post_id qismlar_soni anime_nomi`\n\n"
        "Masalan: `A001 @server 123 12 Naruto`",
        parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_keyboards.get_back_to_admin_panel_keyboard()
    )
    return ANIME_UPLOAD_DATA

async def anime_upload_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        data = update.message.text.split(maxsplit=4)
        code, channel, post_id, episodes, name = data
        success = database.add_anime(code, name, channel, int(post_id), int(episodes))
        if success:
            await update.message.reply_text(f"✅ '{name}' nomli anime muvaffaqiyatli qo'shildi!", reply_markup=admin_keyboards.get_anime_panel_keyboard())
        else:
            await update.message.reply_text("❌ Xatolik: Bunday kodli anime allaqachon mavjud! Boshqa kod kiriting.")
            return ANIME_UPLOAD_DATA
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Xatolik: Ma'lumotlar noto'g'ri formatda kiritildi.", reply_markup=admin_keyboards.get_anime_panel_keyboard())
        return ANIME_UPLOAD_DATA
    return await to_admin_panel(update, context)

# 2. Аниме тізімі
async def anime_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id): return
    animes = database.get_all_animes()
    if not animes:
        await update.message.reply_text("Hozircha animelar mavjud emas.")
        return
    text = "📚 Barcha animelar ro'yxati (kod - nom):\n\n"
    for i, anime in enumerate(animes, 1):
        text += f"{i}. `{anime[1]}` - {anime[2]}\n"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)

# 3. Аниме өшіру
async def anime_delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await anime_list(update, context)
    await update.message.reply_text("O'chirmoqchi bo'lgan anime kodini kiriting:", reply_markup=admin_keyboards.get_back_to_admin_panel_keyboard())
    return ANIME_DELETE_CODE

async def anime_delete_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    code_to_delete = update.message.text.upper()
    success = database.delete_anime(code_to_delete)
    if success:
        await update.message.reply_text(f"✅ `{code_to_delete}` kodli anime muvaffaqiyatli o'chirildi.")
    else:
        await update.message.reply_text(f"❌ `{code_to_delete}` kodli anime topilmadi.")
    return await to_admin_panel(update, context)


# --- SOZLAMALAR PANEL БӨЛІМІ ---

async def to_settings_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id): return
    await update.message.reply_text("⚙️ Sozlamalar Boshqaruv Paneli", reply_markup=admin_keyboards.get_settings_panel_keyboard())

# 1. VIP сипаттамасын өзгерту
async def vip_desc_edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    current_desc = database.get_setting('vip_description')
    await update.message.reply_text(
        f"Hozirgi VIP tavsifi:\n\n{current_desc}\n\nIltimos, yangi tavsif matnini yuboring:",
        reply_markup=admin_keyboards.get_back_to_admin_panel_keyboard()
    )
    return VIP_DESC_EDIT

async def vip_desc_edit_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    new_desc = update.message.text
    database.set_setting('vip_description', new_desc)
    await update.message.reply_text("✅ VIP tavsifi muvaffaqiyatli yangilandi.")
    return await to_admin_panel(update, context)

# 2. VIP беру
async def give_vip_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "VIP status bermoqchi bo'lgan foydalanuvchi ID sini va kunlar sonini probel bilan ajratib yozing.\n\n"
        "Masalan: `123456789 30` (30 kunga VIP berish)",
        parse_mode=ParseMode.MARKDOWN_V2, reply_markup=admin_keyboards.get_back_to_admin_panel_keyboard()
    )
    return GIVE_VIP_DATA

async def give_vip_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        user_id_str, days_str = update.message.text.split()
        user_id = int(user_id_str)
        days = int(days_str)
        success = database.set_user_role(user_id, 'vip', days)
        if success:
            await update.message.reply_text(f"✅ Foydalanuvchi {user_id} ga {days} kunga VIP status berildi.")
            # Пайдаланушыға хабар жіберу
            await context.bot.send_message(user_id, f"Tabriklaymiz! Sizga {days} kunlik VIP status berildi!")
        else:
            await update.message.reply_text("❌ Foydalanuvchiga VIP berishda xatolik yuz berdi.")
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Ma'lumotlar noto'g'ri formatda kiritildi. Qayta urinib ko'ring.")
        return GIVE_VIP_DATA
    return await to_admin_panel(update, context)


# --- ADMIN BOSHQARISH БӨЛІМІ ---

async def to_admin_management_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_super_admin(update.effective_user.id):
        await update.message.reply_text("Bu bo'lim faqat Bosh Adminlar uchun.")
        return
    await update.message.reply_text("👮 Adminlarni Boshqarish", reply_markup=admin_keyboards.get_admin_manage_keyboard())

# ... (Админ қосу, өшіру функциялары) ...


# --- BROADCAST (ХАБАР ЖІБЕРУ) БӨЛІМІ ---

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await is_admin(update.effective_user.id): return ConversationHandler.END
    await update.message.reply_text(
        "Barcha foydalanuvchilarga yuborish uchun xabarni (matn, rasm, video va hokazo) yuboring:",
        reply_markup=admin_keyboards.get_back_to_admin_panel_keyboard()
    )
    return BROADCAST_MESSAGE

async def broadcast_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_ids = database.get_all_user_ids()
    message_to_send = update.message
    
    await update.message.reply_text(f"Xabar yuborish boshlandi... Jami: {len(user_ids)} foydalanuvchi.")
    
    sent_count = 0
    failed_count = 0
    for user_id in user_ids:
        try:
            await context.bot.copy_message(chat_id=user_id, from_chat_id=message_to_send.chat_id, message_id=message_to_send.message_id)
            sent_count += 1
        except Exception as e:
            failed_count += 1
            logger.error(f"Foydalanuvchi {user_id} ga xabar yuborib bo'lmadi: {e}")

    await update.message.reply_text(f"✅ Xabar yuborish yakunlandi.\nMuvaffaqiyatli: {sent_count}\nXatolik: {failed_count}")
    return await to_admin_panel(update, context)


# --- БАРЛЫҚ ADMIN ХЕНДЛЕРЛЕРІН ТІРКЕЙТІН ФУНКЦИЯ ---

def register_admin_handlers(application: Application):
    """Барлық Admin Panel хендлерлерін application-ға тіркейді."""
    
    # Conversation Handlers
    anime_upload_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🎬 Anime Yuklash$"), anime_upload_start)],
        states={ANIME_UPLOAD_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, anime_upload_receive)]},
        fallbacks=[MessageHandler(filters.Regex("^⬅️ Orqaga \(Admin Panel\)$"), to_admin_panel)]
    )
    anime_delete_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^❌ Kodni o'chirish$"), anime_delete_start)],
        states={ANIME_DELETE_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, anime_delete_receive)]},
        fallbacks=[MessageHandler(filters.Regex("^⬅️ Orqaga \(Admin Panel\)$"), to_admin_panel)]
    )
    vip_desc_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📝 VIP Tavsifini Tahrirlash$"), vip_desc_edit_start)],
        states={VIP_DESC_EDIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, vip_desc_edit_receive)]},
        fallbacks=[MessageHandler(filters.Regex("^⬅️ Orqaga \(Admin Panel\)$"), to_admin_panel)]
    )
    give_vip_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ Foydalanuvchiga VIP Berish$"), give_vip_start)],
        states={GIVE_VIP_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, give_vip_receive)]},
        fallbacks=[MessageHandler(filters.Regex("^⬅️ Orqaga \(Admin Panel\)$"), to_admin_panel)]
    )
    broadcast_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📬 Habar Yuborish$"), broadcast_start)],
        states={BROADCAST_MESSAGE: [MessageHandler(filters.ALL & ~filters.COMMAND, broadcast_receive)]},
        fallbacks=[MessageHandler(filters.Regex("^⬅️ Orqaga \(Admin Panel\)$"), to_admin_panel)]
    )

    admin_handlers = [
        anime_upload_conv,
        anime_delete_conv,
        vip_desc_conv,
        give_vip_conv,
        broadcast_conv,
        MessageHandler(filters.Regex("^🎬 Anime Panel$"), to_anime_panel),
        MessageHandler(filters.Regex("^⚙️ Sozlamalar Panel$"), to_settings_panel),
        MessageHandler(filters.Regex("^📚 Kodlar Ro'yxati$"), anime_list),
        MessageHandler(filters.Regex("^👮 Admin Boshqarish$"), to_admin_management_menu),
        MessageHandler(filters.Regex("^👤 User Panelga o'tish$"), switch_to_user_panel),
        MessageHandler(filters.Regex("^⬅️ Orqaga \(Admin Panel\)$"), to_admin_panel),
    ]

    # Барлық админ хендлерлерін тек админдерге ғана жұмыс істейтіндей етіп тіркеу
    for handler in admin_handlers:
        application.add_handler(handler)

    logger.info("Admin panel handler-lari muvaffaqiyatli o'rnatildi.")

