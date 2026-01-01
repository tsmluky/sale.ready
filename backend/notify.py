from __future__ import annotations
import os
import json
import requests
from pywebpush import webpush, WebPushException
from database import SessionLocal
from models_db import PushSubscription

def send_telegram(text: str, chat_id: str = None) -> dict:
    token = os.getenv("TRADERCOPILOT_BOT_TOKEN","").strip() or os.getenv("TELEGRAM_BOT_TOKEN","").strip()
    
    # Priority: Explicit Argument > Env Var
    target_id = chat_id if chat_id else os.getenv("TELEGRAM_CHAT_ID","").strip()
    
    if not token or not target_id:
        return {"ok": False, "error": "Missing bot token or chat id"}
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": target_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        r = requests.post(url, json=payload, timeout=8)
        ok = r.status_code == 200
        return {"ok": ok, "status": r.status_code, "data": r.json() if ok else r.text}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def send_push_notification(title: str, body: str, data: dict = None) -> dict:
    """
    Send Web Push notification to all subscribers.
    """
    private_key = os.getenv("VAPID_PRIVATE_KEY")
    if not private_key:
        return {"ok": False, "error": "Missing VAPID_PRIVATE_KEY"}

    # Claims for VAPID
    claims = {
        "sub": os.getenv("VAPID_MAIL", "mailto:admin@tradercopilot.com")
    }

    db = SessionLocal()
    subs = db.query(PushSubscription).all()
    
    results = {"success": 0, "failed": 0, "removed": 0}
    
    payload = json.dumps({
        "title": title,
        "body": body,
        "icon": "/icon-192.png",
        "data": data or {}
    })

    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {
                        "p256dh": sub.p256dh,
                        "auth": sub.auth
                    }
                },
                data=payload,
                vapid_private_key=private_key,
                vapid_claims=claims
            )
            results["success"] += 1
        except WebPushException as ex:
            # If 410 Gone, remove subscription
            if ex.response and ex.response.status_code == 410:
                db.delete(sub)
                results["removed"] += 1
            else:
                results["failed"] += 1
                print(f"WebPush Error: {ex}")
        except Exception as e:
            results["failed"] += 1
            print(f"General Push Error: {e}")
            
    db.commit()
    db.close()
    return results
