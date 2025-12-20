from routers.analysis import router as analysis_router
import sys
import os
import asyncio
import csv
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, BackgroundTasks, WebSocket, WebSocketDisconnect, Response
from dotenv import load_dotenv

# ==== 1. ConfiguraciÃ³n de entorno (Deterministic Loading) ====
# CRITICAL: This must happen BEFORE any other module import that uses env vars (like database.py)
import sys
import os
# Trigger Deployment

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
from core.config import load_env_if_needed
load_env_if_needed()
from routers.auth import router as auth_router
# Startup Banner (Single Source of Truth Check)
db_url = os.getenv("DATABASE_URL", "sqlite:///./dev_local.db")
db_dialect = db_url.split(":")[0]
if "postgres" in db_url:
    masked_url = db_url.split("@")[-1] if "@" in db_url else "redacted_host"
else:
    masked_url = db_url.replace("sqlite:///", "")

print(f"==================================================")
print(f" TRADERCOPILOT BACKEND v2.0.1 (Sale-Ready + Fix)")
print(f"==================================================")
print(f" [BOOT] DB_DIALECT: {db_dialect}")
print(f" [BOOT] DB_URL_MASKED: {masked_url}")
print(f"==================================================")

# ==== 2. Imports locales (safe to import now) ====
from sqlalchemy import text
from indicators.market import get_market_data  # Capa Quant
from models import LiteReq, LiteSignal, ProReq, AdvisorReq  # Modelos oficiales LITE/PRO
from pydantic import BaseModel

# === 2b. Imports del Signal Hub unificado ===
from core.schemas import Signal
from core.signal_logger import log_signal, signal_from_dict

# === 2c. RAG Context ===
from rag_context import build_token_context

# ==== 3. FastAPI App ====

# FIX: Windows + Async PG functionality requires SelectorEventLoopPolicy
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from core.limiter import limiter
from slowapi.middleware import SlowAPIMiddleware

# === App Initialization ===
app = FastAPI(title="TraderCopilot Backend", version="2.0.0")



async def _unhandled_exception_handler(request: Request, exc: Exception):
    # No filtra detalles sensibles; respuesta estable para producciÃ³n
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=500, content={"code": "INTERNAL_ERROR", "detail": "Internal Server Error"})

app.add_exception_handler(Exception, _unhandled_exception_handler)# Rate Limiter
app.state.limiter = limiter
from fastapi.responses import JSONResponse
from starlette.requests import Request
from slowapi.errors import RateLimitExceeded

def _rate_limit_exceeded_handler_fixed(request, exc):
    return JSONResponse(
        status_code=429,
        content={"code": "RATE_LIMITED", "detail": "Too many requests. Please retry later."}
    )

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler_fixed)
app.add_middleware(SlowAPIMiddleware) # Must be added after other middlewares if order matters, but here is fine.

# Payload Size Limit Middleware (64KB)
@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    if request.method == "POST":
        content_length = request.headers.get("content-length")
        if content_length:
             if int(content_length) > 64 * 1024:
                 return Response("Payload too large", status_code=413)
    return await call_next(request)

# === CORS (Refactored: Single Source of Truth) ===
# Logic moved to lines 133+
# origins = [...] (Removed duplicate block) 


@app.get("/health")
def health_check():
    """Liveness probe: App is running."""
    return {"status": "ok", "version": "2.0.3", "pydantic_fix": "V2"}

@app.get("/ready")
def ready_check():
    """Readiness probe: DB is accessible."""
    try:
        from database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            return {"status": "ready", "db": "connected"}
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database not ready: {e}")

# === Middleware ===
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    import time
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Simple Request Logging
    # print(f"[REQ] {request.method} {request.url.path} - {process_time:.4f}s")
    return response

# === CORS Configuration ===
# Production: Use ALLOWED_ORIGINS env var. Dev: Default to * if not set.
env_allowed = os.getenv("ALLOWED_ORIGINS", "")
if env_allowed:
    origins = env_allowed.split(",")
    print(f"[CORS] âœ… Restricted Origins: {origins}")
else:
    # Dev / MVP Fallback
    origins = ["*"]
    print(f"[CORS] âš ï¸  WARNING: ALLOWED_ORIGINS not set. Defaulting to [*].")

print(f"[CORS] Final Allowed Origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==== DB Init ====
from database import engine, Base
from models_db import Signal as SignalDB, SignalEvaluation, User, StrategyConfig, PushSubscription  # Import models to register them

@app.on_event("startup")
async def startup():
    # DiagnÃ³stico de DB
    db_url = os.getenv("DATABASE_URL", "")
    if (not db_url) or (":memory:" in db_url):
        print("[WARNING] Using SQLite (In-Memory). Data WILL BE LOST on restart.")
    elif "sqlite" in db_url:
        print("[INFO] Using SQLite (File). Data is persistent locally.")
    else:
        print("[INFO] Using PostgreSQL (Persistent).")

    masked = db_url.split("@")[-1] if ("@" in db_url) else "sqlite://..."
    print(f"[DB] Connection URL: {masked}")

    import anyio

    # Crear tablas (DB SYNC) sin bloquear el event loop
    await anyio.to_thread.run_sync(lambda: Base.metadata.create_all(bind=engine))

    # Hotfix Postgres & Migrations
    try:
        from sqlalchemy import text
        with engine.begin() as conn:
            # 1. Expand rationale logic
            if "postgresql" in str(engine.url):
                try:
                     conn.execute(text("ALTER TABLE signals ALTER COLUMN rationale TYPE TEXT;"))
                except:
                     pass

            print("🔧 [DB MIGRATION] Update StrategyConfig/User schemas...")
            # 2. Add telegram_chat_id
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN telegram_chat_id VARCHAR;"))
            except:
                pass
            
            # 3. Migrate StrategyConfig
            try:
                conn.execute(text("ALTER TABLE strategy_configs ADD COLUMN persona_id VARCHAR;"))
                conn.execute(text("ALTER TABLE strategy_configs ADD COLUMN user_id INTEGER;"))
                conn.execute(text("ALTER TABLE strategy_configs ADD COLUMN is_public INTEGER DEFAULT 0;"))
                conn.execute(text("ALTER TABLE strategy_configs ADD COLUMN color VARCHAR DEFAULT 'indigo';"))
                conn.execute(text("ALTER TABLE strategy_configs ADD COLUMN icon VARCHAR DEFAULT 'Cpu';"))
                conn.execute(text("ALTER TABLE strategy_configs ADD COLUMN expected_roi VARCHAR;"))
            except:
                pass
        
        # 4. SEED DATA
        from marketplace_config import SYSTEM_PERSONAS
        from models_db import StrategyConfig
        import json
        from database import SessionLocal
        
        db = SessionLocal()
        try:
            print("🌱 [SEED] Verify Personas in DB...")
            # A. Migrate Custom JSON if DB empty (of custom strategies)
            user_strat_count = db.query(StrategyConfig).filter(StrategyConfig.user_id != None).count()
            if user_strat_count == 0:
                 from marketplace_config import load_user_strategies
                 user_jsons = load_user_strategies()
                 if user_jsons:
                     print(f"  ➡️  Migrating {len(user_jsons)} user strategies to DB...")
                     for p in user_jsons:
                         desc = p.get("description", "")
                         db_obj = StrategyConfig(
                             persona_id=p["id"],
                             strategy_id=p["strategy_id"],
                             name=p["name"],
                             timeframes=json.dumps([p["timeframe"]]),
                             tokens=json.dumps([p["symbol"]]),
                             description=desc,
                             risk_profile=p.get("risk_level", "medium"),
                             expected_roi=p.get("expected_roi", "N/A"),
                             color=p.get("color", "indigo"),
                             is_public=0,
                             user_id=1, 
                             enabled=1 if p.get("is_active") else 0
                         )
                         exists = db.query(StrategyConfig).filter(StrategyConfig.persona_id == p["id"]).first()
                         if not exists:
                             db.add(db_obj)
                     db.commit()
            
            # B. Sync System Personas
            for sp in SYSTEM_PERSONAS:
                db_p = db.query(StrategyConfig).filter(StrategyConfig.persona_id == sp["id"]).first()
                if not db_p:
                    db_p = StrategyConfig(
                        persona_id=sp["id"],
                        strategy_id=sp["strategy_id"],
                        name=sp["name"],
                        description=sp["description"],
                        timeframes=json.dumps([sp["timeframe"]]),
                        tokens=json.dumps([sp["symbol"]]),
                        risk_profile=sp["risk_level"],
                        expected_roi=sp["expected_roi"],
                        color=sp["color"],
                        is_public=1,
                        user_id=None,
                        enabled=1
                    )
                    db.add(db_p)
                else:
                    db_p.description = sp["description"]
                    db_p.expected_roi = sp["expected_roi"]
                    db_p.is_public = 1
                    db_p.user_id = None # Ensure system ownership
            db.commit()
            print("✅ [DB] Schema & Seeds synced.")
        except Exception as e:
            print(f"❌ [DB] Seed Error: {e}")
            db.rollback()
        finally:
            db.close()

    except Exception as e:
        print(f"⚠️ [DB] Schema update skipped: {e}")

    # Background evaluator (best-effort)
    try:
        from evaluated_logger import evaluate_all_tokens

        async def run_evaluator_loop():
            print("[BACKGROUND] Starting Automatic Signal Evaluator...")
            while True:
                try:
                    await asyncio.sleep(300)
                    from fastapi.concurrency import run_in_threadpool
                    tokens_count, new_evals = await run_in_threadpool(evaluate_all_tokens)
                    if new_evals > 0:
                        print(f"[BACKGROUND] Evaluated {new_evals} signals across {tokens_count} tokens.")
                except Exception as e:
                    print(f"[BACKGROUND] Evaluator loop error: {e}")
                    await asyncio.sleep(60)

        asyncio.create_task(run_evaluator_loop())
    except Exception as e:
        print(f"[BACKGROUND] Evaluator not started: {e}")


# ==== 12. Endpoint Notify (Telegram) ====

class TelegramMsg(BaseModel):
    text: str

@app.post("/notify/telegram")
async def notify_telegram(msg: TelegramMsg, db: Session = Depends(get_db)):
    """
    Envia una notificacion a Telegram.
    Ahora soporta envio real si el usuario tiene telegram_chat_id configurado.
    (Por ahora usa un dummy ID o el del .env si es prueba global)
    """
    from services.telegram_bot import bot
    # TODO: Get current user or context. For now, try env var OR explicit ID
    # If msg source provides ID, use it.
    
    # Fallback to ENV var for generic tests
    import os
    target_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if target_id:
        success = await bot.send_message(target_id, msg.text)
        return {"status": "ok", "sent": success}
    else:
        print(f"[TELEGRAM] No CHAT_ID configured. Msg: {msg.text}")
        return {"status": "skipped", "detail": "No Chat ID configured in .env"}

# ==== 9. Stats & Metrics para Dashboard ====


def _parse_iso_ts(value: Optional[str]):
    """
    Intenta parsear timestamps en varios formatos.
    Devuelve datetime con tz UTC o None si no se puede.
    """
    if not value:
        return None

    v = value.strip()
    if not v:
        return None

    # ISO con Z
    try:
        if v.endswith("Z"):
            v = v.replace("Z", "+00:00")
        dt = datetime.fromisoformat(v)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        pass

    # Formatos alternativos
    for fmt in ("%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S"):
        try:
            dt = datetime.strptime(v, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except Exception:
            continue

    return None


def compute_stats_summary() -> Dict[str, Any]:
    """
    Calcula mÃ©tricas agregadas desde la base de datos.
    Fallback a CSV si la DB falla.
    """
    try:
        from typing import Dict, Any
        from sqlalchemy import func
        from models_db import Signal, SignalEvaluation
        from database import SessionLocal
        
        db = SessionLocal()
        try:
            day_ago = datetime.utcnow() - timedelta(hours=24)
            
            # Filter out test sources
            test_sources = ['audit_script', 'verification']
            
            # Signals evaluated in last 24h (Real signals only)
            eval_24h_count = db.query(func.count(SignalEvaluation.id)).join(Signal).filter(
                SignalEvaluation.evaluated_at >= day_ago,
                Signal.source.notin_(test_sources)
            ).scalar() or 0
            
            # Total evaluations (Real only)
            total_eval = db.query(func.count(SignalEvaluation.id)).join(Signal).filter(
                Signal.source.notin_(test_sources)
            ).scalar() or 0
            
            # Win/Loss counts in last 24h (Real only)
            tp_24h = db.query(func.count(SignalEvaluation.id)).join(Signal).filter(
                SignalEvaluation.evaluated_at >= day_ago,
                SignalEvaluation.result == 'WIN',
                Signal.source.notin_(test_sources)
            ).scalar() or 0
            
            sl_24h = db.query(func.count(SignalEvaluation.id)).join(Signal).filter(
                SignalEvaluation.evaluated_at >= day_ago,
                SignalEvaluation.result == 'LOSS',
                Signal.source.notin_(test_sources)
            ).scalar() or 0
            
            # LITE signals in last 24h (Real only)
            lite_24h = db.query(func.count(Signal.id)).filter(
                Signal.timestamp >= day_ago,
                Signal.mode == 'LITE',
                Signal.source.notin_(test_sources)
            ).scalar() or 0
            
            # Calculate win rate
            decided = tp_24h + sl_24h
            win_rate_24h = tp_24h / decided if decided > 0 else None
            
            # Open signals (LITE signals not yet evaluated)
            open_signals_est = max(lite_24h - eval_24h_count, 0)
            
            # [NEW] Calculate PnL (7d) (Real only)
            week_ago = datetime.utcnow() - timedelta(days=7)
            pnl_7d_total = db.query(func.sum(SignalEvaluation.pnl_r)).join(Signal).filter(
                SignalEvaluation.evaluated_at >= week_ago,
                Signal.source.notin_(test_sources)
            ).scalar() or 0.0

            # [NEW] Active Agents Count (Requires StrategyConfig check)
            # Assuming marketplace_config.py loads into StrategyConfig or we just count enabled strategies via API
            # For now, we return 0 here and let frontend fetch /strategies to count enabled ones.
            # actually better to let frontend count active agents from /strategies endpoint.
            
            return {
                "win_rate_24h": win_rate_24h,
                "signals_evaluated_24h": eval_24h_count,
                "signals_total_evaluated": total_eval,
                "signals_lite_24h": lite_24h,
                "open_signals": open_signals_est,
                "pnl_7d": round(pnl_7d_total, 2)
            }
        finally:
            db.close()
            
    except Exception as e:
        print(f"Database query failed, falling back to CSV: {e}")
        # Fallback to CSV-based computation
        return compute_stats_summary_from_csv()


def compute_stats_summary_from_csv() -> Dict[str, Any]:
    """
    Fallback: Calcula mÃ©tricas desde archivos CSV (legacy).
    """
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(hours=24)

    # --- Evaluated: backend/logs/EVALUATED/{token}.evaluated.csv ---
    evaluated_dir = os.path.join(LOGS_DIR, "EVALUATED")
    total_eval = 0
    eval_24h = 0
    tp_24h = 0
    sl_24h = 0
    
    # Needs LOGS_DIR which is not imported but assumed.
    # In main.py usually LOGS_DIR is defined or imported, checking imports.
    # Actually it's not imported in the original file I viewed? 
    # It must be defined somewhere or this will crash. 
    # I saw references in compute_stats_summary_from_csv but didn't see LOGS_DIR definition.
    # It might be in core.config or similar.
    # Wait, I copied the function content from previous view.
    # Let's assume it's there or I add it if missing.
    # Looking at imports: `from core.config import load_env_if_needed`
    # Let's define it to be safe.
    LOGS_DIR = os.path.join(current_dir, "logs")

    if os.path.isdir(evaluated_dir):
        for name in os.listdir(evaluated_dir):
            lower = name.lower()
            if not (lower.endswith(".csv") or lower.endswith(".evaluated.csv")):
                continue

            path = os.path.join(evaluated_dir, name)
            try:
                with open(path, newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        total_eval += 1
                        ts = _parse_iso_ts(
                            row.get("evaluated_at") or row.get("signal_ts")
                        )
                        if ts and ts >= day_ago:
                            eval_24h += 1
                            result = (row.get("result") or "").strip()
                            if result == "hit-tp":
                                tp_24h += 1
                            elif result == "hit-sl":
                                sl_24h += 1
            except Exception:
                # No queremos que un CSV roto tumbe todo el endpoint
                continue

    # --- LITE: backend/logs/LITE/{token}.csv ---
    lite_dir = os.path.join(LOGS_DIR, "LITE")
    lite_24h = 0

    if os.path.isdir(lite_dir):
        for name in os.listdir(lite_dir):
            if not name.lower().endswith(".csv"):
                continue

            path = os.path.join(lite_dir, name)
            try:
                with open(path, newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        ts = _parse_iso_ts(row.get("timestamp"))
                        if ts and ts >= day_ago:
                            lite_24h += 1
            except Exception:
                continue

    decided = tp_24h + sl_24h
    win_rate_24h = tp_24h / decided if decided > 0 else None

    # SeÃ±ales LITE en las Ãºltimas 24h que aÃºn no tienen evaluaciÃ³n
    open_signals_est = max(lite_24h - eval_24h, 0)

    return {
        "win_rate_24h": win_rate_24h,  # 0.0â€“1.0 o null
        "signals_evaluated_24h": eval_24h,
        "signals_total_evaluated": total_eval,
        "signals_lite_24h": lite_24h,
        "open_signals": open_signals_est,
    }


@app.get("/stats/summary")
def stats_summary():
    """
    MÃ©tricas agregadas simples para el dashboard de TraderCopilot.
    """
    try:
        return compute_stats_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==== 11. Fallback global ====

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Manejo genÃ©rico de errores inesperados."""
    if isinstance(exc, HTTPException):
        # Dejamos que FastAPI maneje HTTPException como siempre
        raise exc

    return {
        "error": str(exc),
        "message": "Unexpected server error."
    }










# ==== 13. Endpoint Strategy Management (Toggle) ====

@app.patch("/strategies/marketplace/{id}/toggle")
def toggle_strategy_active(id: str):
    """
    Toggles the is_active state of a strategy persona.
    Supports both Custom (user_strategies.json) and System (system_overrides.json) personas.
    """
    try:
        # Import config helpers locally to avoid circulars if any
        from marketplace_config import (
            load_user_strategies, save_user_strategies,
            load_system_overrides, save_system_overrides,
            SYSTEM_PERSONAS, refresh_personas
        )

        target_id = id
        
        # 1. Check if it's a User Strategy
        user_strategies = load_user_strategies()
        found_in_user = False
        
        for p in user_strategies:
            if p["id"] == target_id:
                # Toggle
                current = p.get("is_active", True)
                p["is_active"] = not current
                found_in_user = True
                save_user_strategies(user_strategies)
                break
        
        if found_in_user:
            refresh_personas()
            return {"status": "ok", "message": f"Strategy {target_id} toggled."}

        # 2. Check if it's a System Strategy
        is_system = any(p["id"] == target_id for p in SYSTEM_PERSONAS)
        
        if is_system:
            overrides = load_system_overrides()
            # If not in overrides, assume active (default for system is True)
            # Find default first to be sure
            default_state = True
            for sp in SYSTEM_PERSONAS:
                if sp["id"] == target_id:
                    default_state = sp.get("is_active", True)
                    break
            
            # Determine current state
            current_override = overrides.get(target_id, {}).get("is_active")
            current_state = current_override if current_override is not None else default_state
            
            # Toggle
            new_state = not current_state
            
            # Save override
            if target_id not in overrides:
                overrides[target_id] = {}
            overrides[target_id]["is_active"] = new_state
            
            save_system_overrides(overrides)
            refresh_personas()
            return {"status": "ok", "message": f"System Strategy {target_id} toggled to {new_state}."}

        raise HTTPException(status_code=404, detail="Strategy not found")
        
    except Exception as e:
        print(f"Error toggling strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==== 10. System Tools ====

@app.get("/system/config")
def system_config():
    """
    Public system configuration.
    """
    return {
        "status": "active",
        "maintenance_mode": False,
        "version": "2.0.3",
        "features": {
            "signup": False, # Disabled for public
            "beta": True
        }
    }

@app.post("/system/reset")
async def factory_reset(request: Request):
    """
    FACTORY RESET PROTECCION CIVIL
    Borra TODAS las seÃ±ales y datos de la base de datos.
    Se usa para demos limpias o reiniciar el entorno.
    """
    try:
        from database import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as session:
            # 1. Truncate Dependent Tables First (Foreign Key Constraints)
            await session.execute(text("DELETE FROM signal_evaluations"))
            
            # 2. Truncate Signals Table
            await session.execute(text("DELETE FROM signals"))
            
            await session.commit()
            
        print("[SYSTEM] âš ï¸  FACTORY RESET EXECUTED. DB CLEARED.")
        return {"status": "ok", "message": "Database cleared successfully. System ready for new deployment."}
            
    except Exception as e:
        print(f"[SYSTEM] Reset Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

# ==== 11.1 Endpoint ADVISOR CHAT (Unified Router Mount) ====
# Double-mount technique: Official + Legacy (Hidden)
from routers.advisor import router as advisor_router
from routers.analysis import router as analysis_router
from routers.strategies import router as strategies_router
from routers.admin import router as admin_router

from routers.logs import router as logs_router
from routers.backtest import router as backtest_router  # Fix 404 logic

from routers.market import router as market_router

app.include_router(advisor_router, prefix="/advisor", tags=["Advisor"])
app.include_router(advisor_router, prefix="/analyze/advisor", include_in_schema=False)
app.include_router(analysis_router, prefix="/analyze", tags=["Analysis"])
app.include_router(strategies_router, prefix="/strategies", tags=["Strategies"])
app.include_router(backtest_router) # Fix Strategy Lab 404
app.include_router(logs_router, prefix="/logs", tags=["Logs"])
app.include_router(market_router, prefix="/market", tags=["Market"])
app.include_router(auth_router, tags=["Auth"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
# app.include_router(auth_router, prefix="/auth", tags=["Auth"]) # DOUBLE PREFIX AVOIDANCE
