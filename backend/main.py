import sys
import traceback
import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Request, Depends
from sqlalchemy.orm import Session
from database import get_db
import fastapi

# ==== 1. ConfiguraciÃ³n de entorno (Deterministic Loading) ====
# CRITICAL: This must happen BEFORE any other module import that uses env vars (like database.py)
# Trigger Deployment

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from core.config import load_env_if_needed  # noqa: E402

load_env_if_needed()

from routers.analysis import router as analysis_router  # noqa: E402
from routers.auth_new import router as auth_router  # noqa: E402

# Startup Banner (Single Source of Truth Check)
db_url = os.getenv("DATABASE_URL", "sqlite:///./dev_local.db")
db_dialect = db_url.split(":")[0]
if "postgres" in db_url:
    masked_url = db_url.split("@")[-1] if "@" in db_url else "redacted_host"
else:
    masked_url = db_url.replace("sqlite:///", "")

print("==================================================")
print(" TRADERCOPILOT BACKEND v2.0.1 (Sale-Ready + Fix)")
print("==================================================")
print(f" [BOOT] DB_DIALECT: {db_dialect}")
print(f" [BOOT] DB_URL_MASKED: {masked_url}")
print("==================================================")

# ==== 2. Imports locales (safe to import now) ====
from pydantic import BaseModel  # noqa: E402

from fastapi.responses import JSONResponse  # noqa: E402

# === 2c. RAG Context ===

# ==== 3. FastAPI App ====

# FIX: Windows + Async PG functionality requires SelectorEventLoopPolicy
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from core.limiter import limiter  # noqa: E402

# === App Initialization ===
print(f"[BOOT] CWD: {os.getcwd()}")
print(f"[BOOT] sys.path: {sys.path}")
try:
    os.makedirs("logs", exist_ok=True)
    print("[BOOT] 'logs' directory verified.")
except Exception as e:
    print(f"[BOOT] Warning: Could not create 'logs' dir: {e}")

app = FastAPI(title="TraderCopilot Backend", version="2.0.0")


# --- EMERGENCY ENDPOINT (TEMPORARY) ---
@app.get("/debug/force-reset")
def force_reset_password(email: str, new_pass: str, db: Session = Depends(get_db)):
    """
    Emergency tool to fix 'UnknownHashError' in Prod.
    Usage: /debug/force-reset?email=admin@tradercopilot.app&new_pass=123456
    """
    from core.security import get_password_hash
    from models_db import User
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"error": "User not found"}
    
    print(f"[DEBUG] Resetting password for {email}...")
    user.hashed_password = get_password_hash(new_pass)
    db.commit()
    return {"status": "success", "message": f"Password updated for {email}"}
# --- END EMERGENCY ---


@app.get("/")
def root_check():
    """Root endpoint for instant health check."""
    return {"status": "online", "service": "TraderCopilot Backend"}


# --- Telegram Bot Lifecycle ---
from telegram_listener import start_telegram_bot, stop_telegram_bot  # noqa: E402


@app.on_event("startup")
async def startup_event():
    # Start Telegram Bot in background (Conditional)
    run_bot = os.getenv("RUN_TELEGRAM_BOT", "false").lower() in ["true", "1", "yes"]
    if run_bot:
        asyncio.create_task(start_telegram_bot())
    else:
        print("ℹ️ [STARTUP] Telegram Bot skipped (RUN_TELEGRAM_BOT not set).")

    # Start Self-Health Check (Debug 502)
    async def self_health_check_loop():
        await asyncio.sleep(10)  # Wait for server to bind
        print("[HEALTH CHECK] Starting internal connectivity test...")
        import httpx

        port = os.getenv("PORT", "8080")
        url = f"http://127.0.0.1:{port}/"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                print(
                    f"[HEALTH CHECK] Internal Ping {url} -> Status: {resp.status_code}"
                )
                if resp.status_code == 200:
                    print(
                        "[HEALTH CHECK] ✅ SUCCESS: App is listening and reachable internally."
                    )
                else:
                    print(
                        f"[HEALTH CHECK] ⚠️ WARNING: App responded with {resp.status_code}."
                    )
        except Exception as e:
            print(f"[HEALTH CHECK] ❌ FAILURE: Could not connect internally: {e}")

    asyncio.create_task(self_health_check_loop())


@app.on_event("shutdown")
async def shutdown_event():
    # Stop Telegram Bot
    await stop_telegram_bot()


from fastapi.middleware.trustedhost import TrustedHostMiddleware  # noqa: E402
from fastapi.exceptions import RequestValidationError  # noqa: E402

# === Security: Trusted Host ===
allowed_hosts = os.getenv("ALLOWED_HOSTS", "*").split(",")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)


# === Security: Exception Handlers (No Stack Traces) ===
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the full error internally, but show generic message externally
    print(f"[CRITICAL ERROR] {request.method} {request.url}: {exc}")
    traceback.print_exc()  # Still print to logs for debugging

    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_SERVER_ERROR",
            "detail": "An unexpected error occurred. Please contact support.",
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422, content={"code": "VALIDATION_ERROR", "detail": str(exc)}
    )


# Rate Limiter Handler
app.state.limiter = limiter
from slowapi.errors import RateLimitExceeded  # noqa: E402


@app.exception_handler(RateLimitExceeded)
def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "code": "RATE_LIMIT_EXCEEDED",
            "detail": "Too many requests. Please try again later.",
        },
    )


# === Security: Payload Size Limit (256KB) ===
@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    # Allow higher limit for explicit upload endpoints if needed (e.g. /upload)
    MAX_BODY_SIZE = 256 * 1024  # 256KB

    if request.method == "POST":
        content_length = request.headers.get("content-length")
        if content_length:
            if int(content_length) > MAX_BODY_SIZE:
                return JSONResponse(
                    status_code=413,
                    content={
                        "code": "PAYLOAD_TOO_LARGE",
                        "detail": "Request body exceeds 256KB limit.",
                    },
                )
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
print(f"[DEBUG CORS] env_allowed raw: '{env_allowed}'")

# Start with robust defaults for all local dev scenarios
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "https://saleready.up.railway.app",
    "https://saleready-production.up.railway.app",
    "https://www.tradercopilot.app",
    "https://tradercopilot.app",
]


if env_allowed:
    extra_origins = [o.strip() for o in env_allowed.split(",") if o.strip()]
    origins.extend(extra_origins)
    print(f"[CORS] ➕ Extended Origins with env: {extra_origins}")

# Remove duplicates
origins = list(set(origins))
print(f"[CORS] ✅ Final Allowed Origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app|https://.*\.railway\.app|https://(.*\.)?tradercopilot\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==== DB Init ====
from database import engine, Base, get_db  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402
from models_db import User  # Import models to register them  # noqa: E402


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

    # [HARDENING] Gate Runtime DDL
    # Only run create_all if explicitly allowed or using SQLite (local dev convenience).
    allow_create = os.getenv("ALLOW_CREATE_ALL", "false").lower() in ["true", "1", "yes"]
    is_sqlite = "sqlite" in str(engine.url)
    
    if allow_create or is_sqlite:
         # Crear tablas (DB SYNC) sin bloquear el event loop
         await anyio.to_thread.run_sync(lambda: Base.metadata.create_all(bind=engine))
    else:
         print("[STARTUP] 🔒 DB Schema creation skipped (Production Mode). Use alembic or scripts.")

    # Import SessionLocal early to avoid UnboundLocalError
    # from database import SessionLocal

    # [HARDENING] DDL & Seeding moved to scripts/apply_patches.py
    # This ensures fast, safe startup without race conditions on DB schema.
    
    # Background Evaluator (Conditional)
    run_evaluator = os.getenv("RUN_EVALUATOR", "false").lower() in ["true", "1", "yes"]
    
    if run_evaluator:
        try:
            from evaluated_logger import evaluate_all_tokens

            async def run_evaluator_loop():
                print("[BACKGROUND] Starting Automatic Signal Evaluator...")
                while True:
                    try:
                        await asyncio.sleep(300)
                        from fastapi.concurrency import run_in_threadpool

                        tokens_count, new_evals = await run_in_threadpool(
                            evaluate_all_tokens
                        )
                        if new_evals > 0:
                            print(
                                f"[BACKGROUND] Evaluated {new_evals} signals across {tokens_count} tokens."
                            )
                    except Exception as e:
                        print(f"[BACKGROUND] Evaluator loop error: {e}")
                        await asyncio.sleep(60)

            asyncio.create_task(run_evaluator_loop())
        except Exception as e:
            print(f"[BACKGROUND] Evaluator not started: {e}")
    else:
         print("ℹ️ [STARTUP] Evaluator skipped (RUN_EVALUATOR not set).")


# ==== 12. Endpoint Notify (Telegram) ====


class TelegramMsg(BaseModel):
    text: str
    chat_id: Optional[str] = None


@app.post("/notify/telegram")
async def notify_telegram(
    msg: TelegramMsg,
    db: Session = fastapi.Depends(get_db),
    # Could add current_user here if we want to auto-fetch from DB,
    # but explicit chat_id in body is better for "Test Ping".
):
    """
    Envia una notificacion a Telegram.
    Soporta envio dinamico si se provee chat_id, o fallback a env var.
    """
    from services.telegram_bot import bot as sender_bot

    target_id = msg.chat_id

    # Fallback to ENV var
    if not target_id:
        import os

        target_id = os.getenv("TELEGRAM_CHAT_ID")

    if target_id:
        success = await sender_bot.send_message(target_id, msg.text)
        if success:
            return {"status": "ok", "sent": True, "target": target_id}
        else:
            return {"status": "error", "detail": "Telegram API failed (check logs)"}
    else:
        print(f"[TELEGRAM] No CHAT_ID configured. Msg: {msg.text}")
        return {
            "status": "skipped",
            "detail": "No Chat ID provided or configured in .env",
        }


# ==== 9. Stats & Metrics para Dashboard ====
# Moved to routers/stats.py
from routers.stats import router as stats_router  # noqa: E402

app.include_router(stats_router, prefix="/stats", tags=["Stats"])


# Update import slightly up top if needed, but get_current_user is likely imported.
# Checking imports... "from routers.auth_new import get_current_user" is needed if not present.
# It is imported in logs.py, but maybe not main.py?
# main.py has `from routers.auth_new import router as auth_router`.
# `from routers.auth_new import get_current_user` might need to be added or check if available.


def compute_stats_summary(user: Optional[User] = None) -> Dict[str, Any]:
    """
    Calcula métricas agregadas desde la base de datos (Scoped by User).
    Fallback a CSV si la DB falla.
    """
    try:
        from sqlalchemy import func, or_
        from models_db import Signal, SignalEvaluation
        from database import SessionLocal

        db = SessionLocal()
        try:
            day_ago = datetime.utcnow() - timedelta(hours=24)
            week_ago = datetime.utcnow() - timedelta(days=7)

            # Filter out test sources
            test_sources = ["audit_script", "verification"]

            # START QUERY BUILDER
            # Base filters for ALL stats
            def apply_filters(q):
                q = q.filter(Signal.source.notin_(test_sources))

                # Exclude trivial/system scalps from Main Stats to align with Dashboard Feed
                # Use LIKE to catch variants like 'lite-rule@v2', 'lite-rule-test', etc.
                q = q.filter(Signal.source.notlike("lite-rule%"))

                if user:
                    # 1. Time Isolation: Only signals created AFTER user joined
                    # (This fixes the "Old Data for New User" bug)
                    if user.created_at:
                        # Ensure created_at is aware or handled
                        # Assuming Signal.timestamp is the key
                        q = q.filter(Signal.timestamp >= user.created_at)

                    # 2. Ownership Isolation
                    # Show User Signals OR System Signals (user_id=None)
                    q = q.filter(or_(Signal.user_id == user.id, Signal.user_id.is_(None)))

                # REQ: Only show TRACKED (Saved) signals in Stats/Dashboard
                q = q.filter(Signal.is_saved == 1)

                return q

            # --- 1. Evaluated in last 24h ---
            q_eval_24 = db.query(func.count(SignalEvaluation.id)).join(Signal)
            q_eval_24 = apply_filters(q_eval_24)
            eval_24h_count = (
                q_eval_24.filter(SignalEvaluation.evaluated_at >= day_ago).scalar() or 0
            )

            # --- 2. Total Evaluations ---
            q_total = db.query(func.count(SignalEvaluation.id)).join(Signal)
            q_total = apply_filters(q_total)
            total_eval = q_total.scalar() or 0

            # --- 3. Wins (Last 24h) ---
            q_wins = db.query(func.count(SignalEvaluation.id)).join(Signal)
            q_wins = apply_filters(q_wins)
            wins_all = (
                q_wins.filter(
                    SignalEvaluation.evaluated_at >= day_ago,
                    SignalEvaluation.result == "WIN",
                ).scalar()
                or 0
            )

            # --- 4. Evals (Last 24h) for Win Rate ---
            q_evals_24_all = db.query(func.count(SignalEvaluation.id)).join(Signal)
            q_evals_24_all = apply_filters(q_evals_24_all)
            evals_all = (
                q_evals_24_all.filter(SignalEvaluation.evaluated_at >= day_ago).scalar()
                or 0
            )

            if evals_all > 0:
                win_rate_24h = (wins_all / evals_all) * 100
            else:
                win_rate_24h = 0

            # --- 5. LITE Signals (24h) (TRACKED ONLY) ---
            q_lite = db.query(func.count(Signal.id))
            q_lite = apply_filters(q_lite)
            # Note: apply_filters enforces is_saved=1
            lite_24h = (
                q_lite.filter(
                    Signal.timestamp >= day_ago, Signal.mode == "LITE"
                ).scalar()
                or 0
            )

            # --- 6. PnL (7d) ---
            q_pnl = db.query(func.sum(SignalEvaluation.pnl_r)).join(Signal)
            q_pnl = apply_filters(q_pnl)
            pnl_7d_total = (
                q_pnl.filter(SignalEvaluation.evaluated_at >= week_ago).scalar() or 0.0
            )

            # Open signals (Estimate) - Using strictly tracked signals
            # Since lite_24h applies is_saved=1, this will only count tracked signals.
            open_signals_est = max(lite_24h - eval_24h_count, 0)

            return {
                "win_rate_24h": round(win_rate_24h, 1),
                "signals_evaluated_24h": eval_24h_count,
                "signals_total_evaluated": total_eval,
                "signals_lite_24h": lite_24h,
                "open_signals": open_signals_est,
                "pnl_7d": round(pnl_7d_total, 2),
            }
        finally:
            db.close()

    except Exception as e:
        print(f"DATABASE ERROR IN STATS: {e}")
        # import traceback
        # traceback.print_exc()

        # Fallback to empty stats to avoid showing confusing CSV data
        return {
            "win_rate_24h": 0,
            "signals_evaluated_24h": 0,
            "signals_total_evaluated": 0,
            "signals_lite_24h": 0,
            "open_signals": 0,
            "pnl_7d": 0.0,
        }


from fastapi import Depends  # noqa: E402
from routers.auth_new import get_current_user  # noqa: E402
from models_db import User  # noqa: E402


@app.get("/stats/summary")
def stats_summary(current_user: User = Depends(get_current_user)):
    """
    Métricas agregadas para el Dashboard (User Scoped).
    """
    try:
        return compute_stats_summary(user=current_user)
    except Exception as e:
        print(f"[STATS] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==== 11. Fallback global ====

# (Removed duplicate global_exception_handler to avoid redefinition error.
# The primary handler is defined at the top of the file.)


# ==== 13. Endpoint Strategy Management (Toggle) ====

# [SECURED] Factory reset and main-level toggle removed for Sale-Ready build.
# Use routers/strategies.py for authorized toggles.


# === Telegram Bot Webhook ===
@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """
    Telegram Webhook Handler.
    Processes /myid and /start commands.
    """
    try:
        data = await request.json()

        # Extract message data
        message = data.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        user = message.get("from", {})

        if not chat_id:
            return {"ok": True}

        # Handle /myid command
        if text.strip().lower() == "/myid":
            response = (
                f"🆔 **Your Telegram Details**\n\n"
                f"**Chat ID:** `{chat_id}`\n"
                f"**User ID:** `{user.get('id', 'N/A')}`\n"
                f"**Username:** @{user.get('username', 'N/A')}\n"
                f"**Name:** {user.get('first_name', '')} {user.get('last_name', '')}\n\n"
                f"Copy your Chat ID and paste it in TraderCopilot Settings to enable notifications!"
            )

            # Send response via Telegram API
            import os
            import httpx

            bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
            if bot_token:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": response,
                    "parse_mode": "Markdown",
                }
                async with httpx.AsyncClient() as client:
                    await client.post(url, json=payload, timeout=10.0)

        # Handle /start command
        elif text.strip().lower() == "/start":
            response = (
                "Welcome to TraderCopilot Bot!\n\n"
                "Commands:\n"
                "/myid - Get your Chat ID\n"
                "/start - Show this help"
            )

            import os
            import httpx

            bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
            if bot_token:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {"chat_id": chat_id, "text": response}
                async with httpx.AsyncClient() as client:
                    await client.post(url, json=payload, timeout=10.0)

        return {"ok": True}

    except Exception as e:
        print(f"[TELEGRAM WEBHOOK] Error: {e}")
        return {"ok": False}


# ==== SCHEDULER AUTO-START ====
import threading  # noqa: E402
from scheduler import scheduler_instance  # noqa: E402
from strategies.registry import load_default_strategies  # noqa: E402


@app.on_event("startup")
def start_scheduler_thread():
    """
    Arranca el Scheduler en un hilo secundario (Daemon).
    Esto asegura que las estrategias se ejecuten automÃ¡ticamente
    sin bloquear el servidor principal y sin necesitar 'python scheduler.py'.
    """
    # 1. Load Strategies into Registry (Shared Memory)
    load_default_strategies()

    # 2. Launch Scheduler (Conditional)
    # [HARDENING] Prevent Duplicate Schedulers
    # Only run if RUN_SCHEDULER env var is "true" or "1".
    run_scheduler = os.getenv("RUN_SCHEDULER", "false").lower() in ["true", "1", "yes"]
    
    if run_scheduler:
        print("🚀 [STARTUP] Launching Strategy Scheduler Thread...")
        t = threading.Thread(target=scheduler_instance.run, daemon=True)
        t.start()
    else:
        print("ℹ️ [STARTUP] Scheduler skipped (RUN_SCHEDULER not set).")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

# ==== 11.1 Endpoint ADVISOR CHAT (Unified Router Mount) ====
# Double-mount technique: Official + Legacy (Hidden)
from routers.advisor import router as advisor_router  # noqa: E402
from routers.strategies import router as strategies_router  # noqa: E402
from routers.admin import router as admin_router  # noqa: E402

from routers.logs import router as logs_router  # noqa: E402
from routers.backtest import router as backtest_router  # Fix 404 logic  # noqa: E402
from routers.market import router as market_router  # noqa: E402

app.include_router(advisor_router, prefix="/advisor", tags=["Advisor"])
app.include_router(advisor_router, prefix="/analyze/advisor", include_in_schema=False)
app.include_router(analysis_router, prefix="/analyze", tags=["Analysis"])
app.include_router(strategies_router, prefix="/strategies", tags=["Strategies"])
app.include_router(backtest_router)  # Fix Strategy Lab 404
app.include_router(logs_router, prefix="/logs", tags=["Logs"])
app.include_router(market_router, prefix="/market", tags=["Market"])
app.include_router(auth_router, tags=["Auth"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
from routers.system import router as system_router  # noqa: E402

app.include_router(system_router, prefix="/system", tags=["System"])
# app.include_router(auth_router, prefix="/auth", tags=["Auth"]) # DOUBLE PREFIX AVOIDANCE
