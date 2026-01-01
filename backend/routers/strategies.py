# backend/routers/strategies.py
"""
End-to-End Strategy Management via PostgreSQL.
Single Source of Truth: 'strategy_configs' table.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import re

from database import SessionLocal
from models_db import StrategyConfig, User, Signal, SignalEvaluation
from strategies.registry import get_registry
from core.signal_logger import log_signal
from pydantic import BaseModel
from routers.auth_new import get_current_user
from dependencies import require_plan, require_pro

# === Dependency ===
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(tags=["strategies"])

# === Models ===

class StrategyCreate(BaseModel):
    name: str # e.g. "My Custom Strat"
    symbol: str # e.g. "BTC"
    timeframe: str # e.g. "1h"
    strategy_id: str # e.g. "donchian_v2" (Logic)
    description: str
    risk_level: str
    expected_roi: str
    win_rate: str
    frequency: str

class PersonaResponse(BaseModel):
    id: str
    name: str
    symbol: str
    timeframe: str
    strategy_id: str
    description: str
    risk_level: str
    expected_roi: str
    win_rate: str
    frequency: str
    color: str
    is_active: bool
    is_custom: bool
    is_public: bool
    icon: str

# === Endpoints ===

@router.get("/marketplace", response_model=List[Dict[str, Any]])
async def get_marketplace(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna todas las estrategias visualizables (Personas).
    Combina:
    1. Estrategias PÃºblicas (Sistema)
    2. Estrategias Privadas del Usuario (si estÃ¡ logueado - TODO)
    """
    # For now, return ALL Public + ALL Private (Admin view) or just Public?
    # Let's fetch all Public + User's own.
    # Since we might not have user context if public page...
    # Filter: System Strategies (user_id is None) OR User's own strategies
    # Need to handle case where current_user might be implicit if we want public access, 
    # but for consistent dashboard, we likely have a user.
    # To be safe, we'll fetch all public (system) + private if user matches.
    
    from sqlalchemy import or_
    
    query = db.query(StrategyConfig).filter(
        or_(
            StrategyConfig.user_id == None,  # System/Public
            StrategyConfig.user_id == current_user.id  # User's own
        )
    )
    
    configs = query.all()
    
    personas = []
    for c in configs:
        # Determine strict "is_custom" bool based on user_id presence
        is_custom = c.user_id is not None
        
        # Parse JSON lists safely
        try:
            tokens = json.loads(c.tokens)[0] if c.tokens else "Unknown"
        except:
            tokens = c.tokens
            
        try:
            tf = json.loads(c.timeframes)[0] if c.timeframes else "Unknown"
        except:
            tf = c.timeframes
            
        # Stats Real (if signals exist)
        # Fix: Calculate Win Rate dynamically to ensure accuracy
        target_source = f"Marketplace:{c.persona_id}"
        real_wr = 0.0
        try:
            # Count evaluated wins
            wins = db.query(SignalEvaluation).join(Signal).filter(
                Signal.source == target_source,
                SignalEvaluation.result == 'WIN'
            ).count()
            
            # Count total evaluations
            total_evals = db.query(SignalEvaluation).join(Signal).filter(
                Signal.source == target_source
            ).count()
            
            if total_evals > 0:
                real_wr = (wins / total_evals) * 100
                
            # Valid commit happens outside loop if we want, or transient update
            c.win_rate = real_wr
            c.total_signals = total_evals
        except Exception as e:
            print(f"[STATS] Error calculating stats for {c.persona_id}: {e}")
            real_wr = c.win_rate or 0.0
        

        # Frequency (Static if in config, else inferred)
        freq_label = "Medium"
        if c.interval_seconds < 900: freq_label = "High"
        elif c.interval_seconds > 14400: freq_label = "Low"
        
        if c.config_json:
            try:
                import json
                conf = json.loads(c.config_json)
                if "frequency" in conf:
                    freq_label = conf["frequency"]
            except:
                pass

        personas.append({
            "id": c.persona_id,
            "name": c.name,
            "symbol": tokens,
            "timeframe": tf,
            "strategy_id": c.strategy_id,
            "description": c.description,
            "risk_level": c.risk_profile,
            "expected_roi": c.expected_roi or "N/A",
            "win_rate": f"{int(real_wr)}%", # Calculated Live
            "frequency": freq_label,
            "color": c.color,
            "is_active": c.enabled == 1,
            "is_custom": is_custom,
            "is_public": c.is_public == 1,
            "icon": c.icon
        })
        
    return personas


@router.post("/marketplace/create")
async def create_persona(
    config: StrategyCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_plan("TRADER"))
):
    """Crea una nueva estrategia personalizada en DB."""
    
    # 1. Generate ID
    safe_name = re.sub(r'[^a-z0-9]+', '_', config.name.lower()).strip('_')
    new_id = f"{safe_name}_{config.symbol.lower()}"
    
    # Check duplication
    exists = db.query(StrategyConfig).filter(StrategyConfig.persona_id == new_id).first()
    if exists:
        import random
        new_id = f"{new_id}_{random.randint(1000,9999)}"
        
    # 2. Create DB Entry
    new_strat = StrategyConfig(
        persona_id=new_id,
        strategy_id=config.strategy_id,
        name=config.name,
        description=config.description,
        tokens=json.dumps([config.symbol]),
        timeframes=json.dumps([config.timeframe]),
        risk_profile=config.risk_level,
        expected_roi=config.expected_roi,
        # Default user settings
        color="indigo",
        is_public=0,
        user_id=current_user.id,
        enabled=1,
        total_signals=0,
        win_rate=0.0
    )
    
    db.add(new_strat)
    db.commit()
    db.refresh(new_strat)
    
    return {"status": "ok", "id": new_id, "msg": "Strategy created successfully"}


@router.patch("/marketplace/{persona_id}/toggle")
async def toggle_strategy(
    persona_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Activa/Desactiva una estrategia."""
    strat = db.query(StrategyConfig).filter(StrategyConfig.persona_id == persona_id).first()
    if not strat:
        raise HTTPException(status_code=404, detail="Strategy not found")
        
    # Security Check: Owner or Admin
    if strat.user_id != current_user.id and current_user.role != "admin":
         # Allow users to toggle System strategies in this Single-Tenant / Sale-Ready version.
         # We assume the main user has full control.
         if strat.user_id is None:
             pass # Allow
         else:
             raise HTTPException(status_code=403, detail="Not authorized to toggle this strategy")

    # Toggle (0 -> 1, 1 -> 0)
    strat.enabled = 0 if strat.enabled == 1 else 1
    db.commit()
    
    return {"status": "ok", "enabled": strat.enabled == 1}


@router.delete("/marketplace/{persona_id}")
async def delete_persona(
    persona_id: str, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Elimina una estrategia (Solo si eres el dueÃ±o)."""
    strat = db.query(StrategyConfig).filter(StrategyConfig.persona_id == persona_id).first()
    if not strat:
        raise HTTPException(status_code=404, detail="Strategy not found")
        
    # Check ownership (unless admin)
    if strat.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this strategy")
        
    # Prevent deleting System strategies (user_id is Null)
    if strat.user_id is None and current_user.role != "admin":
         raise HTTPException(status_code=403, detail="Cannot delete System strategies")

    # --- CASCADE DELETE SIGNALS & EVALUATIONS ---
    # Delete signals generated by this specific persona instance
    target_source = f"Marketplace:{persona_id}"
    
    # First delete evaluations linked to these signals
    # We do a subquery deletion or fetch-then-delete. 
    # For SQLite compatibility/simplicity:
    signals_to_delete = db.query(Signal.id).filter(Signal.source == target_source).all()
    sig_ids = [s[0] for s in signals_to_delete]
    
    deleted_evals = 0
    if sig_ids:
        deleted_evals = db.query(SignalEvaluation).filter(SignalEvaluation.signal_id.in_(sig_ids)).delete(synchronize_session=False)

    deleted_signals = db.query(Signal).filter(Signal.source == target_source).delete(synchronize_session=False)
    
    # Also delete any signals that might have been attributed directly to the strategy_id 
    # IF this is a custom strategy and we want to be aggressive about cleanup.
    # However, 'target_source' is the strict link for persona execution.
    
    print(f"🗑️ Deleting Persona {persona_id}: Metadata + {deleted_signals} Signals + {deleted_evals} Evaluations.")

    db.delete(strat)
    db.commit()
    return {"status": "ok", "msg": f"Strategy deleted. Cleared {deleted_signals} signals."}


@router.get("/marketplace/{persona_id}/history")
async def get_persona_history(persona_id: str, db: Session = Depends(get_db)):
    """Historial de seÃ±ales para una Persona."""
    
    # 1. Resolve strategy to ensure it exists
    # strat = db.query(StrategyConfig).filter(StrategyConfig.persona_id == persona_id).first()
    # if not strat: raise 404... (Optional, strictness)
    
    target_source = f"Marketplace:{persona_id}"
    
    signals = db.query(Signal).filter(
        Signal.source == target_source
    ).order_by(Signal.timestamp.desc()).limit(100).all()
    
    history = []
    for sig in signals:
        eval_data = None
        if sig.evaluation:
            eval_data = {
                "result": sig.evaluation.result,
                "pnl_r": sig.evaluation.pnl_r,
                "exit_price": sig.evaluation.exit_price,
                "closed_at": sig.evaluation.evaluated_at
            }
            
        history.append({
            "id": sig.id,
            "timestamp": sig.timestamp,
            "token": sig.token,
            "direction": sig.direction,
            "entry": sig.entry,
            "tp": sig.tp,
            "sl": sig.sl,
            "mode": sig.mode,
            "confidence": sig.confidence,
            "rationale": sig.rationale,
            "result": eval_data
        })
        
    return history


# === Registry & Metadata (Legacy/Internal) ===

@router.get("/", include_in_schema=False)
async def list_strategies_internal(db: Session = Depends(get_db)):
    """Legacy endpoint, redirected to marketplace logic."""
    return await get_marketplace(db)


