# keep_alive.py
from flask import Flask
from threading import Thread

# Flask қосымшасын құру
app = Flask('')

@app.route('/')
def home():
    """Веб-сервердің басты беті. Боттың жұмыс істеп тұрғанын білдіреді."""
    return "Bot is alive and running!"

def run():
    """Веб-серверді іске қосатын функция."""
    # 0.0.0.0 хосты сервердің кез келген IP адресінен сұраныстарды қабылдауға мүмкіндік береді.
    # port=8080 - VPS-терде жиі қолданылатын стандартты порт.
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """Веб-серверді негізгі ботқа кедергі келтірмей, бөлек процесте іске қосады."""
    server_thread = Thread(target=run)
    server_thread.start()
    print("Keep-alive server ishga tushdi.")
