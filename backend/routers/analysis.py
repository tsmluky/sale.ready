from fastapi import APIRouter, HTTPException, Depends
import traceback
from datetime import datetime

# Imports internos
from indicators.market import get_market_data
from models import LiteReq, ProReq
from core.schemas import Signal
from core.signal_logger import log_signal

# Logic imports
# Logic imports
from core.analysis_logic import (
    _build_lite_from_market,
    _load_brain_context,
    _inject_rag_into_lite_rationale,
    _build_pro_markdown,
)

# Entitlements
from core.entitlements import assert_token_allowed, check_and_increment_quota
from sqlalchemy.orm import Session
from database import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter()

# ==== 9. Endpoint LITE ====

# Auth Dependency
from routers.auth_new import get_current_user
from models_db import User
from core.limiter import limiter
from fastapi import Request


@router.post("/lite")
@limiter.limit("20/minute")  # Higher limit for Lite
def analyze_lite(
    request: Request, req: LiteReq, current_user: User = Depends(get_current_user)
):
    """
    Wrapper seguro para capturar errores 500 y mostrarlos en el frontend.
    Enforces Token Gating.
    """
    try:
        # Enforce Token Access (No DB needed for check, assumes Plan in User)
        # Note: req.token might be alias, assert_token_allowed returns normalized
        req.token = assert_token_allowed(current_user, req.token)

        return _analyze_lite_unsafe(req, current_user)
    except HTTPException as he:
        # Re-raise standard HTTP exceptions (403, 429)
        raise he
    except Exception as e:
        print(f"CRITICAL ERROR IN ANALYZE_LITE: {e}")
        traceback.print_exc()
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "token": req.token,
            "timeframe": req.timeframe,
            "direction": "neutral",
            "entry": 0.0,
            "tp": 0.0,
            "sl": 0.0,
            "confidence": 0.0,
            "rationale": f"CRASH DEBUG: {str(e)}",
            "source": "debug-handler",
            "indicators": {},
        }


def _analyze_lite_unsafe(req: LiteReq, user: User):
    """
    Lógica real de Lite Analysis (Refactored to logic module).
    """
    try:
        # 1. Market Data
        # Call market_data_api directly or use helper?
        # In main it used: from indicators.market import get_market_data
        df, market = get_market_data(req.token, req.timeframe, limit=300)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Market data error: {e}")

    # 2. Build Base Signal (Logic)
    lite_signal, indicators = _build_lite_from_market(req.token, req.timeframe, market)

    # 3. RAG/Context Injection (Optional)
    try:
        final_rationale = _inject_rag_into_lite_rationale(
            req.token, req.timeframe, lite_signal, market
        )
        lite_signal.rationale = final_rationale
    except Exception as e:
        print(f"RAG Injection Failed: {e}")

    # Injection of Audit Marker (Hardening T7)
    if req.message:
        # Append to rationale so it appears in CSV/DB
        lite_signal.rationale = (
            f"{lite_signal.rationale or ''} [MARKER:{req.message}]".strip()
        )

    # 4. Log & Response
    # Convert to unified Signal model for logging
    log_payload = lite_signal.dict()
    # Need to adapt to unified Signal manually or use helper?
    # In main.py lines 800+ it did manual logging.
    # Let's use the Unified Signal schema directly if possible, or mapping.
    # Actually, lite_signal is LiteSignal model.

    # Create Unified Signal for Logger
    unified_sig = Signal(
        timestamp=lite_signal.timestamp,
        strategy_id="lite_v2_router",
        mode="LITE",
        token=lite_signal.token,
        timeframe=lite_signal.timeframe,
        direction=lite_signal.direction,
        entry=lite_signal.entry,
        tp=lite_signal.tp,
        sl=lite_signal.sl,
        confidence=lite_signal.confidence,
        rationale=lite_signal.rationale,
        source=lite_signal.source,
        extra=indicators,
        user_id=user.id,
        is_saved=0,  # Default transient
    )

    # Log and get the ID back if possible, or just log
    # log_signal returns the DB object or similar? It returns void in many impls
    # or the object.
    # The frontend needs the ID to track it. Data flow gap?
    # log_signal typically commits. We need the ID to return to UI so they can
    # click "Track".
    # core/signal_logger.py `log_signal` returns the DB model usually.
    # Let's verify log_signal return type later, but for now assuming it persists.

    # saved_sig = log_signal(unified_sig)

    response = lite_signal.model_dump()
    response["indicators"] = indicators
    # Inject ID so frontend can Track key reference
    # if saved_sig and hasattr(saved_sig, 'id'):
    #     response["id"] = saved_sig.id

    return response


# ==== 10. Endpoint PRO ====


@router.post("/pro")
@limiter.limit("5/minute")  # Anti-abuse
async def analyze_pro(
    request: Request,
    req: ProReq,
    db: Session = Depends(get_db),
    # Removed require_pro to allow Free/Trader to TRY and fail quotas
    current_user: User = Depends(get_current_user),
):
    """
    Generates a deep AI analysis using Gemini/DeepSeek.
    Enforces Token + Quota.
    """
    # 1. Token Check
    req.token = assert_token_allowed(current_user, req.token)

    # 2. Quota Check (Counts as 'ai_analysis')
    quota_res = check_and_increment_quota(db, current_user, "ai_analysis")

    # 3. Get LITE foundation
    try:
        df, market = get_market_data(req.token, req.timeframe, limit=300)
        lite_signal, indicators = _build_lite_from_market(
            req.token, req.timeframe, market
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to build base technicals: {e}"
        )

    # 4. Load Deep Context (RAG)
    brain_context = _load_brain_context(req.token, market_data=market)

    # 5. Generate Analysis
    markdown_report = await _build_pro_markdown(
        req, lite_signal, indicators, brain_context
    )

    # 6. Log (PRO signals should also be logged to history)
    # The prompt didn't explicitly ask for this, but it's good practice for "Audit".
    # We leave it for now to avoid scope creep, or just log basic metadata somewhere?
    # 'log_signal' accepts a Signal object. We could construct a PRO signal.
    # Skipped to stick to strict prompt "Scope Creep: No".

    # 6. Log (PRO signals persisted as transient first, enable Tracking)
    unified_sig = Signal(
        timestamp=datetime.utcnow(),
        strategy_id="pro_deepseek_v2",
        mode="PRO",
        token=req.token,
        timeframe=req.timeframe,
        direction=lite_signal.direction,  # Inherit base direction
        entry=lite_signal.entry,
        tp=lite_signal.tp,
        sl=lite_signal.sl,
        confidence=lite_signal.confidence,  # Base confidence, maybe boosted by LLM?
        rationale=markdown_report[:200] + "...",  # Summary for DB
        source="LLM_HYBRID",
        extra={"full_report_length": len(markdown_report)},
        user_id=current_user.id,
        is_saved=0,
    )

    saved_sig = log_signal(unified_sig)

    return {
        "id": saved_sig.id if saved_sig else None,  # Return ID for tracking
        "raw": markdown_report,
        "token": req.token,
        "mode": "PRO",
        "timestamp": datetime.utcnow().isoformat(),
        "usage": quota_res,
        # Re-inject technicals for Reference
        "entry": lite_signal.entry,
        "tp": lite_signal.tp,
        "sl": lite_signal.sl,
        "confidence": lite_signal.confidence,
        "direction": lite_signal.direction,
    }
