import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Bot Token from environment
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Global app instance for shutdown
telegram_app = None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        "**Hello Trader!**\n\n"
        "I am your TraderCopilot assistant.\n\n"
        "**Setup Instructions:**\n"
        "1. Copy your Chat ID using `/myid`\n"
        "2. Paste it in your TraderCopilot Settings\n\n"
        "Use `/help` for more info.",
        parse_mode='Markdown'
    )

async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /myid command - Returns the user's chat ID"""
    chat_id = update.effective_chat.id
    username = update.effective_user.username or "Trader"
    
    # Monospace for easy copying
    response = (
        f"**Your Chat ID**\n"
        f"`{chat_id}`\n\n"
        f"Copy this number and paste it into the **Telegram Chat ID** field in your Settings."
    )
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def start_telegram_bot():
    """Start the bot in non-blocking mode"""
    global telegram_app
    
    if not BOT_TOKEN:
        print("[TELEGRAM BOT] No Token found. Bot waiting...")
        return

    print("[TELEGRAM BOT] Initializing Bot...")
    
    # Build Application
    telegram_app = Application.builder().token(BOT_TOKEN).build()
    
    # Register Handlers
    telegram_app.add_handler(CommandHandler("start", start_command))
    telegram_app.add_handler(CommandHandler("myid", myid_command))
    telegram_app.add_handler(CommandHandler("help", start_command))

    # Initialize and Start
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    
    print(f"[TELEGRAM BOT] Bot is listening (Username: @{telegram_app.bot.username})")

async def stop_telegram_bot():
    """Stop the bot cleanly"""
    global telegram_app
    if telegram_app:
        print("[TELEGRAM BOT] Stopping Bot...")
        await telegram_app.updater.stop()
        await telegram_app.stop()
        await telegram_app.shutdown()
        print("[TELEGRAM BOT] Bot Stopped.")

if __name__ == "__main__":
    # Standalone testing
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(start_telegram_bot())
        loop.run_forever()
    except KeyboardInterrupt:
        pass
