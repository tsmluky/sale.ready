import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Token from your .env
TOKEN = "8166954117:AAGsD50-gS3uK-dcC1oAzu7CfstNh1_J_U0"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Received /start from {update.effective_user.first_name}")
    await update.message.reply_text("DEBUG: I am alive!")

async def main():
    print(f"Testing Token: {TOKEN[:5]}...")
    try:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        
        print("Initializing...")
        await app.initialize()
        
        # Verify Identity
        me = await app.bot.get_me()
        print(f"\n✅ LOGGED IN AS: @{me.username} ({me.first_name})")
        print(f"👉 Please ensure you are messaging @{me.username} on Telegram!\n")
        
        print("Cleaning up old webhooks...")
        await app.bot.delete_webhook(drop_pending_updates=True)
        
        print("Starting...")
        await app.start()
        print("Polling (Press Ctrl+C to stop)...")
        await app.updater.start_polling()
        
        # Keep alive
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped")
