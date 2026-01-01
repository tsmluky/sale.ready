
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import SessionLocal
from models_db import PushSubscription

router = APIRouter(tags=["notifications"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class PushKeys(BaseModel):
    p256dh: str
    auth: str

class SubscriptionRequest(BaseModel):
    endpoint: str
    keys: PushKeys

@router.post("/subscribe")
def subscribe_push(sub: SubscriptionRequest, db: Session = Depends(get_db)):
    """
    Register a new Web Push subscription.
    """
    # Check if exists
    existing = db.query(PushSubscription).filter(PushSubscription.endpoint == sub.endpoint).first()
    if existing:
        # Update keys just in case
        existing.p256dh = sub.keys.p256dh
        existing.auth = sub.keys.auth
        db.commit()
        return {"status": "updated"}
    
    new_sub = PushSubscription(
        endpoint=sub.endpoint,
        p256dh=sub.keys.p256dh,
        auth=sub.keys.auth
    )
    db.add(new_sub)
    db.commit()
    return {"status": "subscribed"}

@router.post("/test")
def test_notification():
    """
    Send a test notification to all subscribers.
    """
    from notify import send_push_notification
    res = send_push_notification(
        title="Test Notification",
        body="This is a test from TraderCopilot!",
        data={"url": "/strategies"}
    )
    return res
