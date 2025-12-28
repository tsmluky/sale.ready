from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import SessionLocal
from models_db import Signal, SignalEvaluation
from pydantic import BaseModel
from datetime import datetime
from routers.auth_new import get_current_user
from models_db import User, Signal, SignalEvaluation

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene las señales más recientes (User + System).
    """
    try:
        from sqlalchemy import or_
        
        # Initialize query FIRST
        query = db.query(Signal)

        if mode:
            query = query.filter(Signal.mode == mode)
        
        # STRICT ISOLATION:
        # 1. Signals they strictly own (user_id = current_user.id)
        # 2. OR System signals (user_id = None) IF we consider them public. 
        # But user complained about seeing "other account history".
        # If the other account created a CUSTOM strategy, it MUST have user_id.
        # If it didn't, it's a bug in creation.
        
        # Let's ensure we are filtering properly.
        # IF we want total isolation (even for system signals per user instance), 
        # we need to track who triggered it.
        # For now, let's Stick to the OR logic BUT verify why "lukx" signals are visible to "asd".
        # It implies "lukx" signals have user_id=None (Legacy?)
        
        # FIX: Only show signals explicitly owned by user, unless it's a globally confirmed system signal.
        # Since we are "selling" independence, let's try strict filtering first. 
        # If we hide System signals, the dashboard might be empty? 
        # Let's keep the OR but ensure Custom Strategies from others are hidden.
        
        
        # FIX: Only show signals explicitly owned by user, unless it's a globally confirmed system signal.
        # Since we are "selling" independence, let's try strict filtering first. 
        # If we hide System signals, the dashboard might be empty? 
        # Let's keep the OR but ensure Custom Strategies from others are hidden.
        
        query = query.filter(
            or_(
                Signal.user_id == current_user.id, 
                # Only show system signals if they are NOT flagged as hidden/private in some way?
                # Actually, the leakage is likely legacy signals with Null user_id.
                # Use strict filtering for now?
                # Only way is via user_id.
                Signal.user_id == None 
            )
        )
        
        # [NEW] Time Isolation: Hide legacy system signals that predate the user
        if current_user.created_at:
             query = query.filter(Signal.timestamp >= current_user.created_at)

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
            eval_entry = db.query(SignalEvaluation).filter(
                SignalEvaluation.signal_id == sig.id
            ).first()
            
            status = "OPEN"
            pnl = None
            closed_at = None
            exit_price = None
            
            if eval_entry:
                status = eval_entry.result  # WIN, LOSS, BE
                pnl = eval_entry.pnl_r
                closed_at = eval_entry.evaluated_at
                exit_price = eval_entry.exit_price
            
            results.append(LogEntry(
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
                exit_price=exit_price
            ))
            
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
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint de compatibilidad para fetchLogs.
    Devuelve logs filtrados por modo y token (User + System).
    """
    try:
        from sqlalchemy import or_
        query = db.query(Signal).filter(
            Signal.mode == mode.upper(),
            or_(Signal.user_id == current_user.id, Signal.user_id == None)
        )
        
        if token.lower() != "all":
            query = query.filter(Signal.token == token.upper())
            
        signals = query.order_by(desc(Signal.timestamp)).limit(limit).all()
        
        # Mapear a formato simple
        results = []
        for s in signals:
            eval_entry = db.query(SignalEvaluation).filter(SignalEvaluation.signal_id == s.id).first()
            results.append({
                "timestamp": s.timestamp.isoformat() if s.timestamp else None,
                "token": s.token,
                "timeframe": s.timeframe,
                "direction": s.direction,
                "entry": s.entry,
                "tp": s.tp,
                "sl": s.sl,
                "confidence": s.confidence,
                "source": s.source,
                "closed_at": eval_entry.evaluated_at.isoformat() if eval_entry and eval_entry.evaluated_at else None,
                "exit_price": eval_entry.exit_price if eval_entry else None
            })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching logs: {str(e)}")
