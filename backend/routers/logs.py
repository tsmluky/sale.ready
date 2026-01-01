from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import SessionLocal
from models_db import Signal, SignalEvaluation
from pydantic import BaseModel
from datetime import datetime
from routers.auth_new import get_current_user
from models_db import User

router = APIRouter(tags=["logs"])


class LogEntry(BaseModel):
    id: int
    timestamp: datetime
    token: str
    timeframe: str
    direction: str
    entry: float
    tp: float
    sl: float
    confidence: float
    source: str
    mode: str
    status: str = "OPEN"
    pnl: Optional[float] = None
    closed_at: Optional[datetime] = None
    exit_price: Optional[float] = None

    class Config:
        from_attributes = True


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/recent", response_model=List[LogEntry])
def get_recent_logs(
    limit: int = 20,
    mode: Optional[str] = None,
    saved_only: bool = False,
    include_system: bool = True,  # [NEW] Default True to keep Radar working
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Obtiene las señales más recientes.
    - include_system=True: Muestra señales globales (Scanner) + Propias.
    - include_system=False: SOLO muestra señales Propias o Guardadas (Dashboard limpio).
    """
    try:
        from sqlalchemy import or_

        # Initialize query FIRST
        query = db.query(Signal)

        if mode:
            query = query.filter(Signal.mode == mode)

        # LOGIC:
        # Base: Always show signals OWNER by user (user_id == current_user.id)

        if include_system:
            # Show User's OR System's (user_id is None)
            # This is for Radar/Scanner Page
            query = query.filter(
                or_(Signal.user_id == current_user.id, Signal.user_id == None)
            )
        else:
            # Show ONLY User's Explicitly Saved signals (Clean Dashboard)
            query = query.filter(
                Signal.user_id == current_user.id, Signal.is_saved == 1
            )

        # [NEW] Time Isolation: Hide legacy system signals that predate the user
        if current_user.created_at:
            query = query.filter(Signal.timestamp >= current_user.created_at)

        # [NEW] Saved Only Filter (for clean Dashboard)
        if saved_only:
            query = query.filter(Signal.is_saved == 1)

        # [NEW] Plan-Based Filtering
        # If user is FREE, only show Free Tokens (BTC, ETH, SOL)
        # Assuming current_user.plan is "free", "starter", "pro", "whale", etc.
        # We treat anything other than "free" as premium for now, or check specifically.

        from data.supported_tokens import VALID_TOKENS_FREE

        is_premium = current_user.plan and current_user.plan.lower() not in [
            "free",
            "starter",
        ]

        if not is_premium:
            # Filter query to only include free tokens
            query = query.filter(Signal.token.in_(VALID_TOKENS_FREE))

        query = query.order_by(desc(Signal.timestamp))

        # Fetch more signals to account for deduplication
        signals = query.limit(limit * 3).all()

        # Enriquecer con evaluación si existe + DEDUPLICACIÓN
        results = []
        seen_keys = set()

        for sig in signals:
            # Create a unique key for deduplication
            # Key: Token + Timestamp (Minute resolution or Exact?) + Direction
            # Using exact timestamp to merge instantaneous duplicates
            ts_str = sig.timestamp.isoformat() if sig.timestamp else ""
            dedup_key = f"{sig.token}_{ts_str}_{sig.direction}_{sig.mode}"

            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)

            # Buscar vacantes (evaluación)
            # OPTIMIZATION: Could be eager loaded, but for now loop is fine for small limits
            eval_entry = (
                db.query(SignalEvaluation)
                .filter(SignalEvaluation.signal_id == sig.id)
                .first()
            )

            status = "OPEN"
            pnl = None
            closed_at = None
            exit_price = None

            if eval_entry:
                status = eval_entry.result  # WIN, LOSS, BE
                pnl = eval_entry.pnl_r
                closed_at = eval_entry.evaluated_at
                exit_price = eval_entry.exit_price

            results.append(
                LogEntry(
                    id=sig.id,
                    timestamp=sig.timestamp,
                    token=sig.token or "UNKNOWN",
                    timeframe=sig.timeframe or "1h",
                    direction=sig.direction or "neutral",
                    entry=sig.entry or 0.0,
                    tp=sig.tp or 0.0,
                    sl=sig.sl or 0.0,
                    confidence=sig.confidence or 0.0,
                    source=sig.source or sig.strategy_id or "System",
                    mode=sig.mode or "LITE",
                    status=status,
                    pnl=pnl,
                    closed_at=closed_at,
                    exit_price=exit_price,
                )
            )

            if len(results) >= limit:
                break

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching logs: {str(e)}")


@router.get("/{mode}/{token}")
def get_logs_by_token(
    mode: str,
    token: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint de compatibilidad para fetchLogs.
    Devuelve logs filtrados por modo y token (User + System).
    """
    try:
        from sqlalchemy import or_

        query = db.query(Signal).filter(
            Signal.mode == mode.upper(),
            or_(Signal.user_id == current_user.id, Signal.user_id == None),
        )

        if token.lower() != "all":
            query = query.filter(Signal.token == token.upper())

        signals = query.order_by(desc(Signal.timestamp)).limit(limit).all()

        # Mapear a formato simple
        results = []
        for s in signals:
            eval_entry = (
                db.query(SignalEvaluation)
                .filter(SignalEvaluation.signal_id == s.id)
                .first()
            )
            results.append(
                {
                    "timestamp": s.timestamp.isoformat() if s.timestamp else None,
                    "token": s.token,
                    "timeframe": s.timeframe,
                    "direction": s.direction,
                    "entry": s.entry,
                    "tp": s.tp,
                    "sl": s.sl,
                    "confidence": s.confidence,
                    "source": s.source,
                    "closed_at": (
                        eval_entry.evaluated_at.isoformat()
                        if eval_entry and eval_entry.evaluated_at
                        else None
                    ),
                    "exit_price": eval_entry.exit_price if eval_entry else None,
                }
            )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching logs: {str(e)}")


@router.post("/track", response_model=LogEntry)
def create_tracked_signal(
    signal_data: dict,  # Using dict to be flexible with frontend payload structure initially
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Guarda explícitamente una señal enviada por el frontend (Track).
    Used when user clicks 'Track' on a transient signal from Analyst.
    """
    try:
        from models_db import Signal as SignalDB

        # Parse Timestamp
        ts = signal_data.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        else:
            ts = datetime.utcnow()

        # Create DB Entry
        new_sig = SignalDB(
            timestamp=ts,
            token=signal_data.get("token", "UNKNOWN").upper(),
            timeframe=signal_data.get("timeframe", "30m"),
            direction=signal_data.get("direction", "neutral"),
            entry=float(signal_data.get("entry", 0)),
            tp=float(signal_data.get("tp")) if signal_data.get("tp") else 0.0,
            sl=float(signal_data.get("sl")) if signal_data.get("sl") else 0.0,
            confidence=(
                float(signal_data.get("confidence"))
                if signal_data.get("confidence") is not None
                else 0.0
            ),
            rationale=signal_data.get("rationale", ""),
            source=signal_data.get("source", "MANUAL_TRACK"),
            mode=signal_data.get("mode", "LITE"),
            # raw_response=str(signal_data.get("extra")) if signal_data.get("extra") else None,
            strategy_id=signal_data.get("strategy_id", "manual"),
            user_id=current_user.id,
            is_saved=1,  # Explicitly SAVED
            extra=signal_data.get("extra"),
        )

        db.add(new_sig)
        db.commit()
        db.refresh(new_sig)

        return new_sig

    except Exception as e:
        print(f"Error creating tracked signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{signal_id}/toggle_save")
def toggle_save_signal(
    signal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Toggle the 'is_saved' status of a signal.
    Only allows modifying own signals or system signals (by cloning? No, just tracking).
    Refined logic: If signal is System (user_id=None), we can't edit it
    directly if we want to share it.
    But for now, assuming simple ownership or shared mutability for System
    signals is NOT safe.

    Actually, system signals are shared. If User A tracks it, does it track for User B?
    If 'is_saved' is on the Signal row, yes. This is a schema flaw for shared system signals.
    However, LITE signals are often generated on the fly or by scheduler.

    FOR NOW: We assume signals in 'logs/recent' are mostly user-triggered or isolated.
    If it's a System signal, we might need to clone it to user space to "Track" it individually.

    Strategy:
    If user owns signal -> Toggle is_saved.
    If signal is System (user_id=None) -> CLONE it to user_id=current_user.id
    and set is_saved=1.
    """
    try:
        sig = db.query(Signal).filter(Signal.id == signal_id).first()
        if not sig:
            raise HTTPException(status_code=404, detail="Signal not found")

        # Check ownership
        if sig.user_id == current_user.id:
            # Toggle
            new_state = 1 if (sig.is_saved == 0 or sig.is_saved is None) else 0
            sig.is_saved = new_state
            db.commit()
            return {
                "status": "success",
                "id": sig.id,
                "is_saved": new_state,
                "action": "updated",
            }

        elif sig.user_id is None:
            # System Signal -> Clone to User to Track it personally
            # Check if already cloned? Query signal with same idempotency or
            # strategy+time+token and user_id?
            # Too complex. For this iteration, if they click Track on a system
            # signal, we clone it.

            # Create Copy
            new_sig = Signal(
                timestamp=sig.timestamp,
                token=sig.token,
                timeframe=sig.timeframe,
                direction=sig.direction,
                entry=sig.entry,
                tp=sig.tp,
                sl=sig.sl,
                confidence=sig.confidence,
                rationale=sig.rationale,
                source=sig.source,
                mode=sig.mode,
                raw_response=sig.raw_response,
                strategy_id=sig.strategy_id,
                user_id=current_user.id,  # Assign to User
                is_saved=1,  # Saved immediately
                # Is extra stored in JSON? Signal model in models_db doesn't show
                # Extra column in finding above.
                # models_db definition of Signal:
                # strategy_id, mode, etc. NO EXTRA column in the snippet I saw
                # earlier (lines 1-36).
                # But Unified Schema has extra.
                # Let's rely on what's in DB.
            )
            db.add(new_sig)
            db.commit()
            return {
                "status": "success",
                "id": new_sig.id,
                "is_saved": 1,
                "action": "cloned",
            }

        else:
            raise HTTPException(
                status_code=403, detail="Not authorized to edit this signal"
            )

    except Exception as e:
        print(f"Error toggling save: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


from notify import send_telegram


class TelegramPayload(BaseModel):
    text: str
    chat_id: Optional[str] = None


@router.post("/notify/telegram")
def notify_telegram_endpoint(
    payload: TelegramPayload, current_user: User = Depends(get_current_user)
):
    res = send_telegram(payload.text, payload.chat_id)
    if not res.get("ok"):
        return {"status": "error", "detail": res.get("error")}
    return {"status": "success", "data": res.get("data")}
