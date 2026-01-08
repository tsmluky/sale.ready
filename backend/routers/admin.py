from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional, Any

from database import SessionLocal
from models_db import User, Signal, AdminAuditLog
from dependencies import require_owner
from pydantic import BaseModel

router = APIRouter(tags=["admin"], dependencies=[Depends(require_owner)])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Helpers ---
def log_admin_action(
    db: Session, admin_id: int, action: str, target_id: str, details: str
):
    audit = AdminAuditLog(
        admin_id=admin_id, action=action, target_id=target_id, details=details
    )
    db.add(audit)
    db.commit()


# --- Schemas ---
class UserPlanUpdate(BaseModel):
    plan: str  # FREE, PRO, OWNER


class SignalUpdate(BaseModel):
    is_hidden: bool


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int


# --- Endpoints ---


@router.get("/stats")
async def get_admin_stats(db: Session = Depends(get_db)):
    """KPIs for Admin Dashboard."""
    from datetime import datetime, timedelta
    
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)

    total_users = db.query(func.count(User.id)).scalar()
    users_24h = db.query(func.count(User.id)).filter(User.created_at >= last_24h).scalar()

    active_pro = (
        db.query(func.count(User.id)).filter(User.plan.like("%PRO%")).scalar()
    )  # PRO or OWNER likely

    hidden_signals = (
        db.query(func.count(Signal.id)).filter(Signal.is_hidden == 1).scalar()
    )
    total_signals = db.query(func.count(Signal.id)).scalar()
    signals_24h = db.query(func.count(Signal.id)).filter(Signal.timestamp >= last_24h).scalar()

    # --- MRR Calculation (Estimated) ---
    # Prices updated per user request (Jan 2026)
    PRICE_TRADER = 49
    PRICE_PRO = 149

    count_trader = db.query(func.count(User.id)).filter(User.plan == "TRADER").scalar() or 0
    count_pro = db.query(func.count(User.id)).filter(User.plan == "PRO").scalar() or 0
    
    # MRR = (Trader * 50) + (Pro * 150)
    mrr_est = (count_trader * PRICE_TRADER) + (count_pro * PRICE_PRO)

    return {
        "total_users": total_users,
        "users_24h": users_24h,
        "active_plans": active_pro,
        "hidden_signals": hidden_signals,
        "total_signals": total_signals,
        "signals_24h": signals_24h,
        "system_status": "ONLINE (Scheduler Active)", # Placeholder until health check integration
        "mrr": mrr_est,
        "last_updated": now.isoformat()
    }


@router.get("/users")
async def list_users(
    page: int = 1,
    size: int = 20,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    offset = (page - 1) * size
    query = db.query(User)

    if q:
        query = query.filter(User.email.contains(q))

    total = query.count()
    users = query.order_by(desc(User.created_at)).offset(offset).limit(size).all()

    return {
        "items": [
            {
                "id": u.id,
                "email": u.email,
                "role": u.role,
                "plan": u.plan,
                "created_at": u.created_at,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "size": size,
    }


@router.patch("/users/{user_id}/plan")
async def update_user_plan(
    user_id: int,
    update: UserPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_plan = user.plan
    user.plan = update.plan.upper()
    db.commit()

    log_admin_action(
        db,
        current_user.id,
        "UPDATE_PLAN",
        str(user_id),
        f"Changed plan from {old_plan} to {user.plan}",
    )

    return {"status": "success", "new_plan": user.plan}


@router.get("/signals")
async def list_signals(
    page: int = 1,
    size: int = 50,
    token: Optional[str] = None,
    mode: Optional[str] = None,
    show_hidden: bool = True,
    db: Session = Depends(get_db),
):
    offset = (page - 1) * size
    query = db.query(Signal)

    if token:
        query = query.filter(Signal.token == token.upper())
    if mode:
        query = query.filter(Signal.mode == mode.upper())
    if not show_hidden:
        query = query.filter(Signal.is_hidden == 0)

    total = query.count()
    signals = query.order_by(desc(Signal.timestamp)).offset(offset).limit(size).all()

    # Simple serialization
    return {"items": signals, "total": total, "page": page, "size": size}


@router.patch("/signals/{signal_id}")
async def toggle_signal_visibility(
    signal_id: int,
    update: SignalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    sig = db.query(Signal).filter(Signal.id == signal_id).first()
    if not sig:
        raise HTTPException(status_code=404, detail="Signal not found")

    sig.is_hidden = 1 if update.is_hidden else 0
    db.commit()

    action = "HIDE_SIGNAL" if update.is_hidden else "UNHIDE_SIGNAL"
    log_admin_action(
        db, current_user.id, action, str(signal_id), f"Set is_hidden to {sig.is_hidden}"
    )

    return {"status": "success", "is_hidden": sig.is_hidden}


@router.get("/audit")
async def get_audit_logs(page: int = 1, size: int = 50, db: Session = Depends(get_db)):
    offset = (page - 1) * size
    query = db.query(AdminAuditLog)
    total = query.count()
    logs = (
        query.order_by(desc(AdminAuditLog.timestamp)).offset(offset).limit(size).all()
    )

    return {"items": logs, "total": total, "page": page, "size": size}
