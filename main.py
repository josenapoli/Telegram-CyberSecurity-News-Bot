import os
import time
import json
import re
import argparse
import requests
import feedparser
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
INTERVAL_MINUTES = int(os.getenv("POLLING_INTERVAL_MINUTES", "30"))

FEEDS_FILE = "feeds.json"
SENT_FILE = "sent_articles.json"

# Límite para evitar inundar el chat de Telegram en la primera ejecución o tras estar apagado
MAX_SEND_PER_FEED = 2

# Headers simulando un navegador real para evitar bloqueos 403 (ej. SecurityWeek)
HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def load_json_file(filepath, default_value):
    if not os.path.exists(filepath):
        return default_value
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error al leer {filepath}: {e}. Se usará el valor por defecto.")
        return default_value

def save_json_file(filepath, data):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error al guardar {filepath}: {e}")

def escape_html(text):
    if not text:
        return ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def clean_summary(summary_html, max_length=250):
    if not summary_html:
        return ""
    # Quitar etiquetas HTML
    clean_text = re.sub(r"<[^>]+>", "", summary_html)
    # Reemplazar múltiples espacios/saltos de línea
    clean_text = re.sub(r"\s+", " ", clean_text).strip()
    
    if len(clean_text) > max_length:
        clean_text = clean_text[:max_length] + "..."
    return clean_text

def send_telegram_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        # No imprimir la excepción completa: puede incluir la URL con el token del bot.
        print(f"Error al enviar mensaje a Telegram ({type(e).__name__}).")
        return False

def check_feeds():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Iniciando verificación de feeds...")
    
    feeds = load_json_file(FEEDS_FILE, [])
    sent_articles = set(load_json_file(SENT_FILE, []))
    
    if not feeds:
        print("No hay feeds configurados en feeds.json")
        return

    is_first_run = (len(sent_articles) == 0)
    if is_first_run:
        print("Primera ejecución detectada. Se enviarán un máximo de 2 noticias por feed para evitar inundar tu chat.")

    new_articles_sent = 0
    updated_sent_articles = set(sent_articles)

    for feed_url in feeds:
        print(f"Procesando feed: {feed_url}")
        try:
            # Obtener el XML del feed usando requests con headers reales
            response = requests.get(feed_url, headers=HTTP_HEADERS, timeout=15)
            response.raise_for_status()
            
            # Parsear el contenido obtenido
            parsed = feedparser.parse(response.content)
            feed_title = parsed.feed.get("title", "Noticias de Seguridad")
            
            # Identificar artículos nuevos
            new_entries = []
            for entry in parsed.entries:
                entry_id = entry.get("id", entry.get("link"))
                if not entry_id:
                    continue
                if entry_id not in sent_articles:
                    new_entries.append(entry)
            
            if not new_entries:
                continue

            # Invertimos para procesar en orden cronológico (los más antiguos primero)
            new_entries = new_entries[::-1]
            
            # Carga máxima por feed para evitar flood
            to_send = new_entries
            if len(new_entries) > MAX_SEND_PER_FEED:
                print(f"Detectados {len(new_entries)} artículos nuevos en '{feed_title}'. Se limitará el envío a los {MAX_SEND_PER_FEED} más recientes.")
                to_send = new_entries[-MAX_SEND_PER_FEED:]
                
            # Agregar todos a la lista de enviados para que no se vuelvan a evaluar
            for entry in new_entries:
                entry_id = entry.get("id", entry.get("link"))
                updated_sent_articles.add(entry_id)

            # Enviar los seleccionados
            for entry in to_send:
                title = entry.get("title", "Sin título")
                link = entry.get("link", "")
                summary = entry.get("summary", entry.get("description", ""))
                
                clean_title = escape_html(title)
                clean_feed_title = escape_html(feed_title)
                clean_desc = escape_html(clean_summary(summary))
                
                message = (
                    f"<b>📰 {clean_feed_title}</b>\n"
                    f"<a href=\"{link}\"><b>{clean_title}</b></a>\n\n"
                    f"{clean_desc}\n\n"
                    f"🔗 <a href=\"{link}\">Leer noticia completa</a>"
                )
                
                print(f"Enviando noticia a Telegram: {title}")
                if send_telegram_message(TOKEN, CHAT_ID, message):
                    new_articles_sent += 1
                    time.sleep(1) # Breve pausa entre mensajes
                
        except Exception as e:
            print(f"Error al procesar el feed {feed_url}: {e}")

    # Guardar estado final de artículos leídos
    if updated_sent_articles != sent_articles:
        save_json_file(SENT_FILE, list(updated_sent_articles))
        print(f"Ejecución terminada. Se enviaron {new_articles_sent} noticias nuevas.")
    else:
        print("Ejecución terminada. No hubo cambios.")

def main():
    parser = argparse.ArgumentParser(description="Bot de Telegram para novedades de Ciberseguridad.")
    parser.add_argument("--once", action="store_true", help="Ejecutar una sola vez y salir.")
    args = parser.parse_args()

    if not TOKEN or not CHAT_ID:
        print("ERROR: Asegúrate de configurar TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID en el archivo .env")
        return

    if args.once:
        check_feeds()
    else:
        print(f"Bot iniciado. Corriendo en bucle cada {INTERVAL_MINUTES} minutos...")
        while True:
            try:
                check_feeds()
            except Exception as e:
                print(f"Ocurrió un error inesperado: {e}")
            
            print(f"Esperando {INTERVAL_MINUTES} minutos para el siguiente escaneo...")
            time.sleep(INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    main()
