# Bot de Novedades de Ciberseguridad para Telegram

Este script recopila las últimas noticias de ciberseguridad desde diversos feeds RSS/Atom y las envía automáticamente a un chat de Telegram.

## 🚀 Requisitos

- Python 3.11 o superior.
- Una conexión a Internet.
- Un bot de Telegram creado a través de [@BotFather](https://t.me/BotFather).

## 🛠️ Instalación y Configuración

1. **Instalar dependencias**:
   Abre tu consola en este directorio y ejecuta:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar credenciales (.env)**:
   Crea un archivo `.env` en la raíz del proyecto. Este archivo está excluido por `.gitignore` y no debe subirse al repositorio:
   ```env
   TELEGRAM_BOT_TOKEN=tu_token_de_bot
   TELEGRAM_CHAT_ID=tu_chat_id
   POLLING_INTERVAL_MINUTES=30
   ```
   - `TELEGRAM_BOT_TOKEN`: Token de tu bot.
   - `TELEGRAM_CHAT_ID`: ID del chat, grupo o canal donde se enviarán los mensajes.
   - `POLLING_INTERVAL_MINUTES`: Cada cuántos minutos el bot revisará si hay nuevas noticias (por defecto, 30 minutos).

3. **Configurar Feeds (feeds.json)**:
   Puedes agregar o quitar URLs de fuentes de noticias editando el archivo `feeds.json`. Por defecto, hemos incluido:
   - The Hacker News
   - Krebs on Security
   - CISA Cybersecurity Advisories
   - Dark Reading

## ⚙️ Ejecución

### Opción A: Ejecución en bucle continuo (Ideal para dejarlo corriendo)
El script buscará noticias periódicamente según los minutos definidos en el archivo `.env`:
```bash
python main.py
```

### Opción B: Ejecución única (Ideal para tareas programadas / Cron)
El script revisará los feeds una sola vez, enviará las novedades y se cerrará. Puedes programarlo para que se ejecute cada cierto tiempo mediante el programador de tareas de tu sistema operativo (como *Windows Task Scheduler* o *cron* en Linux):
```bash
python main.py --once
```

---

*Nota: Las noticias ya enviadas se almacenan automáticamente en el archivo `sent_articles.json` para evitar que te lleguen alertas repetidas.*
