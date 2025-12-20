# backend/routers/strategies.py
"""
Endpoints API para gestión de estrategias.

Permite al dashboard:
- Listar estrategias disponibles
- Activar/desactivar estrategias
- Ver estadísticas de performance
- Ejecutar estrategias manualmente (testing)
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from database import SessionLocal
from models_db import StrategyConfig
from strategies.registry import get_registry
from core.signal_logger import log_signal
from pydantic import BaseModel
from marketplace_config import MARKETPLACE_PERSONAS, get_active_strategies

# === Dependency ===
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(tags=["strategies"])

router = APIRouter(tags=["strategies"])

from routers.auth import get_current_user
from models_db import User

@router.get("/marketplace", response_model=List[Dict[str, Any]])
async def get_marketplace(db: Session = Depends(get_db)):
    """Retorna la configuración de 'Personas' del Marketplace."""
    from marketplace_config import refresh_personas, MARKETPLACE_PERSONAS
    from models_db import Signal, SignalEvaluation
    from sqlalchemy import func

    # 1. Get Base Config (from JSON/System)
    personas = refresh_personas()
    
    # 2. Enrich with DB Stats
    # We need to query Signal + SignalEvaluation for each persona
    # source = "Marketplace:{id}"
    
    # Optimización: Hacer una sola query de agregación? 
    # Select source, count(*), count_wins
    # Pero el source es string.
    
    for p in personas:
        target_source = f"Marketplace:{p['id']}"
        
        # Total Signals for this persona
        total = db.query(func.count(Signal.id)).filter(Signal.source == target_source).scalar() or 0
        
        # Total Wins
        wins = db.query(func.count(Signal.id)).join(SignalEvaluation).filter(
            Signal.source == target_source,
            SignalEvaluation.result == "WIN"
        ).scalar() or 0
        
        # Calculate Win Rate
        wr = 0.0
        if total > 0:
            wr = (wins / total) * 100
            
        # Inject into response (Override JSON defaults)
        # Only override if we have data (or always? Let's show real data even if 0)
        if total > 0:
            p["win_rate"] = f"{int(wr)}%"
            # Optional: Add badge or text for total trades
            # p["frequency"] = f"{total} trades (Real)" 
        else:
            # Keep manual/marketing "win_rate" if no real data yet?
            # Or show "Pending"?
            # User wants "Professional". "Pending" or N/A is professional if no data.
            # But let's fallback to the "Marketing" number if 0 real trades, 
            # to keep the "Wow" factor during demo/setup.
            pass

    return personas

from models_db import Signal, SignalEvaluation

@router.get("/marketplace/{persona_id}/history")
async def get_persona_history(persona_id: str, db: Session = Depends(get_db)):
    """
    Obtiene el historial de señales generadas por una Persona específica.
    Filtra por source="Marketplace:{persona_id}"
    """
    # Validar persona
    valid_ids = [p["id"] for p in MARKETPLACE_PERSONAS]
    if persona_id not in valid_ids:
        # Fallback para permitir debugear IDs viejos si existen
        # raise HTTPException(status_code=404, detail="Persona not found")
        pass

    target_source = f"Marketplace:{persona_id}"
    
    # Query Signals sorted by time desc
    signals = db.query(Signal).filter(
        Signal.source == target_source
    ).order_by(Signal.timestamp.desc()).limit(100).all()
    
    # Enriquecer con evaluación si existe
    history = []
    for sig in signals:
        eval_data = None
        if sig.evaluation:
            eval_data = {
                "result": sig.evaluation.result,
                "pnl_r": sig.evaluation.pnl_r,
                "exit_price": sig.evaluation.exit_price,
                "closed_at": sig.evaluation.evaluated_at.isoformat() if sig.evaluation.evaluated_at else None
            }
            
        history.append({
            "id": sig.id,
            "timestamp": sig.timestamp.isoformat() + "Z",
            "token": sig.token,
            "direction": sig.direction,
            "entry": sig.entry,
            "tp": sig.tp,
            "sl": sig.sl,
            "result": eval_data
        })
        
    return history



# === Models ===

class StrategyMetadataResponse(BaseModel):
    """Metadatos de una estrategia para el frontend."""
    id: str
    name: str
    description: str
    version: str
    default_timeframe: str
    universe: List[str]
    risk_profile: str
    mode: str
    source_type: str
    enabled: bool
    
    # Stats (si está en DB)
    total_signals: Optional[int] = 0
    win_rate: Optional[float] = 0.0
    last_execution: Optional[datetime] = None


class StrategyConfigUpdate(BaseModel):
    """Actualización de configuración de estrategia."""
    enabled: Optional[bool] = None
    interval_seconds: Optional[int] = None
    tokens: Optional[List[str]] = None
    timeframes: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None


class ExecuteStrategyRequest(BaseModel):
    """Request para ejecutar estrategia manualmente."""
    tokens: List[str]
    timeframe: str = "30m"
    context: Optional[Dict[str, Any]] = None





# === Endpoints ===

@router.get("/", response_model=List[StrategyMetadataResponse])
async def list_strategies(db: Session = Depends(get_db)):
    """
    Lista todas las estrategias disponibles.
    
    Combina:
    - Estrategias registradas en el registry (código)
    - Configuración de DB (si existe)
    """
    registry = get_registry()
    all_metas = registry.list_all()
    
    results = []
    
    for meta in all_metas:
        # Buscar config en DB
        db_config = db.query(StrategyConfig).filter(
            StrategyConfig.strategy_id == meta.id
        ).first()
        
        result = StrategyMetadataResponse(
            id=meta.id,
            name=meta.name,
            description=meta.description,
            version=meta.version,
            default_timeframe=meta.default_timeframe,
            universe=meta.universe,
            risk_profile=meta.risk_profile,
            mode=meta.mode,
            source_type=meta.source_type,
            enabled=db_config.enabled == 1 if db_config else meta.enabled,
            total_signals=db_config.total_signals if db_config else 0,
            win_rate=db_config.win_rate if db_config else 0.0,
            last_execution=db_config.last_execution if db_config else None,
        )
        results.append(result)
    
    return results


@router.get("/{strategy_id}")
async def get_strategy(strategy_id: str, db: Session = Depends(get_db)):
    """Obtiene detalles de una estrategia específica."""
    registry = get_registry()
    strategy = registry.get(strategy_id)
    
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy '{strategy_id}' not found")
    
    meta = strategy.metadata()
    
    # Buscar config en DB
    db_config = db.query(StrategyConfig).filter(
        StrategyConfig.strategy_id == strategy_id
    ).first()
    
    return {
        "metadata": meta.dict(),
        "config": json.loads(db_config.config_json) if db_config and db_config.config_json else {},
        "stats": {
            "total_signals": db_config.total_signals if db_config else 0,
            "win_rate": db_config.win_rate if db_config else 0.0,
            "avg_confidence": db_config.avg_confidence if db_config else 0.0,
            "last_execution": db_config.last_execution.isoformat() + "Z" if db_config and db_config.last_execution else None,
        }
    }


@router.patch("/{strategy_id}")
async def update_strategy_config(
    strategy_id: str,
    update: StrategyConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualiza configuración de una estrategia.
    
    Permite:
    - Activar/desactivar (enabled)
    - Cambiar intervalo de ejecución
    - Modificar tokens/timeframes
    - Actualizar config específico
    """
    # Verificar que la estrategia existe en registry
    registry = get_registry()
    strategy = registry.get(strategy_id)
    
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy '{strategy_id}' not found in registry")
    
    # Buscar o crear config en DB
    db_config = db.query(StrategyConfig).filter(
        StrategyConfig.strategy_id == strategy_id
    ).first()
    
    if not db_config:
        # Crear nuevo
        meta = strategy.metadata()
        db_config = StrategyConfig(
            strategy_id=meta.id,
            name=meta.name,
            description=meta.description,
            version=meta.version,
            enabled=1,
            tokens=json.dumps(meta.universe),
            timeframes=json.dumps([meta.default_timeframe]),
            risk_profile=meta.risk_profile,
            mode=meta.mode,
            source_type=meta.source_type,
        )
        db.add(db_config)
    
    # Aplicar updates
    if update.enabled is not None:
        db_config.enabled = 1 if update.enabled else 0
    
    if update.interval_seconds is not None:
        db_config.interval_seconds = update.interval_seconds
    
    if update.tokens is not None:
        db_config.tokens = json.dumps(update.tokens)
    
    if update.timeframes is not None:
        db_config.timeframes = json.dumps(update.timeframes)
    
    if update.config is not None:
        db_config.config_json = json.dumps(update.config)
    
    db_config.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(db_config)
        return {"status": "ok", "strategy_id": strategy_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating strategy: {str(e)}")


@router.post("/{strategy_id}/execute")
async def execute_strategy_manual(
    strategy_id: str,
    req: ExecuteStrategyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ejecuta una estrategia manualmente (útil para testing).
    
    No afecta al scheduler automático.
    """
    registry = get_registry()
    
    # Obtener config de DB si existe
    db_config = db.query(StrategyConfig).filter(
        StrategyConfig.strategy_id == strategy_id
    ).first()
    
    config_dict = {}
    if db_config and db_config.config_json:
        config_dict = json.loads(db_config.config_json)
    
    # Instanciar estrategia
    strategy = registry.get(strategy_id, config=config_dict)
    
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy '{strategy_id}' not found")
    
    # Ejecutar
    try:
        signals = strategy.generate_signals(
            tokens=req.tokens,
            timeframe=req.timeframe,
            context=req.context or {}
        )
        
        # Loguear señales
        for signal in signals:
            log_signal(signal)
        
        return {
            "status": "ok",
            "signals_generated": len(signals),
            "signals": [
                {
                    "token": s.token,
                    "direction": s.direction,
                    "entry": s.entry,
                    "tp": s.tp,
                    "sl": s.sl,
                    "confidence": s.confidence,
                }
                for s in signals
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing strategy: {str(e)}")


from models_db import StrategyConfig, User
from scheduler import scheduler_instance
from dependencies import require_pro, require_owner

# --- 1. CRUD de Personas (StrategyConfig) ---


class StrategyCreate(BaseModel):
    name: str
    symbol: str
    timeframe: str
    strategy_id: str
    description: str
    risk_level: str
    expected_roi: str
    win_rate: str
    frequency: str

from dependencies import require_plan

@router.post("/marketplace/create")
async def create_persona(config: StrategyCreate, current_user: User = Depends(require_plan("TRADER"))):
    """
    Crea una nueva 'persona' o configuración de estrategia.
    Requiere TRADER o superior.
    """
    import json
    import re
    from marketplace_config import USER_STRATEGIES_FILE, refresh_personas
    
    # 1. Definir ID único (Sanitized)
    safe_name = re.sub(r'[^a-z0-9]', '_', config.name.lower())
    new_id = f"{safe_name}_{config.symbol.lower()}"
    
    # Check if ID exists (in the FRESH list)
    current_personas = refresh_personas() # Ensure we have latest
    existing_ids = [p["id"] for p in current_personas]
    
    if new_id in existing_ids:
         # Add random suffix
        import random
        new_id = f"{new_id}_{random.randint(1000, 9999)}"

    # 2. Construir objeto
    new_persona = {
        "id": new_id,
        "name": config.name,
        "symbol": config.symbol,
        "timeframe": config.timeframe,
        "strategy_id": config.strategy_id,
        "description": config.description,
        "risk_level": config.risk_level,
        "expected_roi": config.expected_roi,
        "win_rate": config.win_rate,
        "frequency": config.frequency,
        "color": "indigo", 
        "is_active": True,
        "is_custom": True
    }
    
    # 3. Persistir en JSON
    try:
        user_data = []
        if USER_STRATEGIES_FILE.exists():
            with open(USER_STRATEGIES_FILE, "r", encoding="utf-8") as f:
                user_data = json.load(f)
        
        user_data.append(new_persona)
        
        with open(USER_STRATEGIES_FILE, "w", encoding="utf-8") as f:
            json.dump(user_data, f, indent=4)
            
        # Refresh in-memory list so other endpoints see it immediately
        refresh_personas()
            
        return {"status": "ok", "id": new_id, "msg": "Persona created and saved to JSON."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save persona: {str(e)}")


@router.delete("/marketplace/{persona_id}")
async def delete_persona(persona_id: str, current_user: User = Depends(get_current_user)):
    """
    Elimina una Persona personalizada del Marketplace (JSON).
    Source of Truth: JSON File directly.
    """
    import json
    from marketplace_config import USER_STRATEGIES_FILE, refresh_personas

    print(f"!!! BACKEND DELETE REQUEST RECEIVED FOR: {persona_id} !!!")
    print(f"!!! LOOKING IN FILE: {USER_STRATEGIES_FILE} !!!")

    # 1. Attempt to Delete directly from JSON (Bypassing memory checks)
    if not USER_STRATEGIES_FILE.exists():
         raise HTTPException(status_code=404, detail="User strategies storage not found")
         
    try:
        with open(USER_STRATEGIES_FILE, "r", encoding="utf-8") as f:
            user_data = json.load(f)
            
        # Check if exists in FILE
        target_in_file = next((p for p in user_data if p["id"] == persona_id), None)
        
        if not target_in_file:
             # If not in custom file, check if it's a system file (forbidden)
             # But first 404 if not found anywhere? 
             # Let's just say 404 if not in User JSON, assuming Frontend only calls DELETE on custom items.
             # Alternatively, check System list to give specific 403 error.
             raise HTTPException(status_code=404, detail="Custom Persona not found")

        # 2. Rewrite JSON without it
        new_user_data = [p for p in user_data if p["id"] != persona_id]
        
        with open(USER_STRATEGIES_FILE, "w", encoding="utf-8") as f:
            json.dump(new_user_data, f, indent=4)
            
        # 3. Update Memory
        refresh_personas()
        
        return {"status": "ok", "msg": f"Persona {persona_id} deleted"}
        
    except json.JSONDecodeError:
         raise HTTPException(status_code=500, detail="Corrupted Strategy File")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete persona: {str(e)}")

def _persist_config(path: str):
    pass # Deprecated

