# database.py
import psycopg2
import logging
from contextlib import contextmanager
import datetime

# --- Дерекқор баптаулары (Сіздің нұсқауыңыз бойынша) ---
DB_SETTINGS = {
    "host": "localhost",
    "database": "db_anifinx",
    "user": "postgres",
    "password": "postgres"
}

# Логгерді орнату
logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    """PostgreSQL-мен қауіпсіз байланыс орнату үшін контекст менеджері."""
    conn = None
    try:
        conn = psycopg2.connect(**DB_SETTINGS)
        logger.info("Ma'lumotlar bazasiga muvaffaqiyatli ulanildi.")
        yield conn
    except psycopg2.OperationalError as e:
        logger.error(f"Ma'lumotlar bazasiga ulanishda xatolik yuz berdi: {e}")
        raise
    finally:
        if conn:
            conn.close()
            logger.info("Ma'lumotlar bazasi bilan aloqa uzildi.")

def init_db(super_admins: list):
    """
    Бот іске қосылғанда барлық кестелерді жасайды немесе тексереді.
    Супер-админдер тізімін config-тан алады.
    """
    create_tables_sql = """
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
        role VARCHAR(20) NOT NULL DEFAULT 'user', -- 'user', 'vip', 'admin'
        username VARCHAR(255),
        first_name VARCHAR(255),
        balance BIGINT DEFAULT 0,
        vip_expires_at TIMESTAMP WITH TIME ZONE,
        join_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS animes (
        id SERIAL PRIMARY KEY,
        code VARCHAR(50) UNIQUE NOT NULL,
        name VARCHAR(255) NOT NULL,
        source_channel VARCHAR(255) NOT NULL,
        start_post_id INTEGER NOT NULL,
        total_episodes INTEGER NOT NULL,
        views BIGINT DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS settings (
        key VARCHAR(255) PRIMARY KEY,
        value TEXT
    );
    CREATE TABLE IF NOT EXISTS forced_subscriptions (
        channel_id BIGINT PRIMARY KEY,
        channel_url TEXT NOT NULL,
        expire_timestamp REAL, -- null болса, шексіз
        join_limit INTEGER, -- null болса, шексіз
        current_joins INTEGER DEFAULT 0,
        is_active BOOLEAN DEFAULT TRUE
    );
    CREATE TABLE IF NOT EXISTS posting_channels (
        id SERIAL PRIMARY KEY,
        channel_id BIGINT UNIQUE NOT NULL,
        channel_url TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS custom_commands (
        id SERIAL PRIMARY KEY,
        command_name VARCHAR(255) UNIQUE NOT NULL,
        command_type VARCHAR(50) NOT NULL, -- 'tugmali', 'yozuvli'
        location VARCHAR(50) NOT NULL, -- 'user_panel', 'admin_panel'
        action_text TEXT NOT NULL
    );
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(create_tables_sql)
                # Бастапқы баптауларды енгізу (егер жоқ болса)
                initial_settings = {
                    'vip_description': "👑 VIP a'zolik haqida ma'lumot shu yerda bo'ladi.",
                    'vip_price_1_month': '30000',
                    'maintenance_mode': 'off'
                }
                for key, value in initial_settings.items():
                    cur.execute(
                        "INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO NOTHING",
                        (key, value)
                    )
                
                # Супер-админдерді базаға қосу/жаңарту
                for admin_id in super_admins:
                    cur.execute(
                        """
                        INSERT INTO users (user_id, role) VALUES (%s, 'admin')
                        ON CONFLICT (user_id) DO UPDATE SET role = 'admin';
                        """,
                        (admin_id,)
                    )
                conn.commit()
        logger.info("Barcha jadvallar muvaffaqiyatli yaratildi/tekshirildi.")
    except Exception as e:
        logger.error(f"Jadvallarni yaratishda xatolik: {e}")

# --- Пайдаланушылармен жұмыс істеу ---
def add_or_update_user(user_id: int, username: str, first_name: str):
    sql = "INSERT INTO users (user_id, username, first_name) VALUES (%s, %s, %s) ON CONFLICT (user_id) DO UPDATE SET username = EXCLUDED.username, first_name = EXCLUDED.first_name;"
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id, username, first_name))
                conn.commit()
    except Exception as e:
        logger.error(f"Foydalanuvchi {user_id} ni qo'shishda/yangilashda xatolik: {e}")

def get_user_role(user_id: int) -> str:
    # VIP мерзімі өтіп кеткендерді тексеру
    check_vip_sql = "UPDATE users SET role = 'user' WHERE user_id = %s AND role = 'vip' AND vip_expires_at < NOW();"
    select_sql = "SELECT role FROM users WHERE user_id = %s"
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(check_vip_sql, (user_id,))
                cur.execute(select_sql, (user_id,))
                result = cur.fetchone()
                conn.commit()
                return result[0] if result else 'user'
    except Exception as e:
        logger.error(f"Foydalanuvchi {user_id} rolini olishda xatolik: {e}")
        return 'user'

def set_user_role(user_id: int, role: str, days: int = None):
    expires_at = None
    if role == 'vip' and days:
        expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days)
    
    sql = "UPDATE users SET role = %s, vip_expires_at = %s WHERE user_id = %s;"
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO users (user_id) VALUES (%s) ON CONFLICT DO NOTHING;", (user_id,))
                cur.execute(sql, (role, expires_at, user_id))
                conn.commit()
        return True
    except Exception as e:
        logger.error(f"Foydalanuvchi {user_id} rolini o'zgartirishda xatolik: {e}")
        return False

def get_all_user_ids():
    """Барлық пайдаланушылардың ID-ларын қайтарады (хабар жіберу үшін)."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM users;")
            return [row[0] for row in cur.fetchall()]

# --- Анимемен жұмыс істеу ---
def add_anime(code, name, source_channel, start_post_id, total_episodes):
    sql = "INSERT INTO animes (code, name, source_channel, start_post_id, total_episodes) VALUES (%s, %s, %s, %s, %s)"
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (code.upper(), name, source_channel, start_post_id, total_episodes))
                conn.commit()
        return True
    except psycopg2.errors.UniqueViolation:
        logger.warning(f"'{code}' kodli anime allaqachon mavjud.")
        return False
    except Exception as e:
        logger.error(f"Anime qo'shishda xatolik: {e}")
        return False

def get_all_animes():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, code, name FROM animes ORDER BY name;")
            return cur.fetchall()

def delete_anime(code: str):
    sql = "DELETE FROM animes WHERE code = %s;"
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (code.upper(),))
                conn.commit()
                # affected_rows > 0 болса, сәтті өшірілді
                return cur.rowcount > 0
    except Exception as e:
        logger.error(f"'{code}' kodli animeni o'chirishda xatolik: {e}")
        return False

# --- Баптаулармен жұмыс істеу ---
def get_setting(key: str) -> str:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT value FROM settings WHERE key = %s", (key,))
            result = cur.fetchone()
            return result[0] if result else None

def set_setting(key: str, value: str):
    sql = "INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;"
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (key, value))
                conn.commit()
        return True
    except Exception as e:
        logger.error(f"'{key}' sozlamasini o'rnatishda xatolik: {e}")
        return False
