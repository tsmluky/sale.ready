import os
import sys
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Cargar entorno desde backend/
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
load_dotenv(os.path.join(current_dir, ".env"))

TOKEN = os.getenv("TRADERCOPILOT_BOT_TOKEN")
API_URL = "http://localhost:8000"

if not TOKEN:
    print("❌ ERROR: No se encontró TRADERCOPILOT_BOT_TOKEN en .env")
    sys.exit(1)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *TraderCopilot Online*\n\nComandos:\n/lite <token> <tf>\nEj: `/lite eth 1h`",
        parse_mode=ParseMode.MARKDOWN,
    )


async def analyze_lite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # 1. Parsear argumentos (ej: /lite eth 1h)
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "⚠️ Uso: `/lite <token> <timeframe>`\nEj: `/lite eth 1h`",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        token = args[0].lower()
        tf = args[1].lower()

        await update.message.reply_text(f"⏳ Analizando {token.upper()} ({tf})...")

        # 2. Llamar a TU Backend Local (FastAPI)
        payload = {"token": token, "timeframe": tf}
        try:
            response = requests.post(
                f"{API_URL}/analyze/lite", json=payload, timeout=10
            )
        except requests.exceptions.ConnectionError:
            await update.message.reply_text(
                "❌ Error: El Backend no está corriendo. "
                "Ejecuta 'python backend/main.py'."
            )
            return

        if response.status_code != 200:
            await update.message.reply_text(f"❌ Error en backend: {response.text}")
            return

        data = response.json()

        # 3. Formatear Respuesta (Estilo SignalCard)
        signal = data.get("direction", "NEUTRAL")
        # Emojis según señal
        emoji = "⚪"
        if "LONG" in signal.upper():
            emoji = "🟢"
        if "SHORT" in signal.upper():
            emoji = "🔴"

        # Formato seguro
        msg = f"""
{emoji} **SIGNAL: {signal}**
**{data["token"].upper()}** | {data["timeframe"]}

💰 **Precio:** ${data["entry"]}
🎯 **TP:** {data["tp"]}
🛑 **SL:** {data["sl"]}
📊 **Confianza:** {data["confidence"]}

🧠 **Razón:**
_{data["rationale"]}_

⚙️ *RSI: {data["indicators"]["rsi"]} | Trend: {data["indicators"]["trend"]}*
        """

        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await update.message.reply_text(f"💥 Error crítico: {str(e)}")
        print(f"ERROR: {e}")


if __name__ == "__main__":
    print("🚀 Bot escuchando... (Pulsa Ctrl+C para salir)")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("lite", analyze_lite))

    app.run_polling()
