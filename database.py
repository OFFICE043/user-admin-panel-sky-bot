# database.py
import psycopg2
import logging
from contextlib import contextmanager
# config-тан импорт алып тасталды, себебі баптаулар осы файлда

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
        # DB_SETTINGS сөздігін қолданып қосылу
        conn = psycopg2.connect(**DB_SETTINGS)
        yield conn
    except psycopg2.OperationalError as e:
        logger.error(f"Ma'lumotlar bazasiga ulanishda xatolik yuz berdi: {e}")
        raise
    finally:
        if conn:
            conn.close()

def init_db():
    """Негізгі кестелерді жасайды."""
    create_tables_sql = """
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
        role VARCHAR(20) NOT NULL DEFAULT 'user',
        username VARCHAR(255),
        first_name VARCHAR(255)
    );
    CREATE TABLE IF NOT EXISTS animes (
        id SERIAL PRIMARY KEY,
        code VARCHAR(50) UNIQUE NOT NULL,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        views BIGINT DEFAULT 0
    );
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(create_tables_sql)
                conn.commit()
        logger.info("Barcha jadvallar muvaffaqiyatli yaratildi/tekshirildi.")
    except Exception as e:
        logger.error(f"Jadvallarni yaratishda xatolik: {e}")

# ... (Қалған барлық функциялар өзгеріссіз қалады)
