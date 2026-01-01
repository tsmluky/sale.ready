import os
import httpx

class TelegramBot:
    """
    Simple wrapper for Telegram Bot API.
    """
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    async def send_message(self, chat_id: str, text: str) -> bool:
        """
        Sends a text message to a specific chat_id.
        """
        if not self.token:
            print("[TELEGRAM] ⚠️ No Bot Token configured.")
            return False
            
        if not chat_id:
            print("[TELEGRAM] ⚠️ No Chat ID provided.")
            return False

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, timeout=10.0)
                
            if resp.status_code == 200:
                print(f"[TELEGRAM] ✅ Saved to {chat_id}: {text[:20]}...")
                return True
            else:
                print(f"[TELEGRAM] ❌ Error {resp.status_code}: {resp.text}")
                return False
        except Exception as e:
            print(f"[TELEGRAM] ❌ Exception: {e}")
            return False

# Singleton instance
bot = TelegramBot()
