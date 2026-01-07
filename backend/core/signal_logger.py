# backend/core/signal_logger.py
"""
Unified Signal Logger for TraderCopilot Signal Hub.

Este módulo centraliza TODA la escritura de señales (CSV + DB),
independientemente de su origen (LITE, PRO, ADVISOR, CUSTOM, etc.).

Responsabilidad única: recibir una instancia de Signal y persistirla
en el formato adecuado para logs CSV y base de datos.
"""

from __future__ import annotations
import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from .schemas import Signal


# === Configuración de rutas ===
BACKEND_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BACKEND_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Headers estándar de CSV (compatibles con el schema Signal)
CSV_HEADERS = [
    "timestamp",
    "token",
    "timeframe",
    "direction",
    "entry",
    "tp",
    "sl",
    "confidence",
    "rationale",
    "source",
]


def log_signal(signal: Signal) -> bool:
    """
    Guarda una señal en DB (Canonical) y si tiene éxito, en CSV.

    Args:
        signal: Instancia del modelo Signal unificado

    Returns:
        bool: True si se insertó correctamente (Nueva señal).
              False si fue duplicada (dedupe) o error.
    """

    mode = signal.mode.upper()
    
    # === 1. Persistir en DB (CANONICAL SOURCE OF TRUTH) ===
    # Si falla dedupe aquí, abortamos todo lo demás.
    inserted = _write_to_db(signal, mode)
    
    if not inserted:
        return False

    # === 2. Persistir en CSV (Solo si DB aceptó) ===
    token_lower = signal.token.lower()
    _write_to_csv(signal, mode, token_lower)
    
    # === 3. Push Notification (Mobile) ===
    # Solo si es nueva.
    _send_push_notification(signal)
    
    return True


def _snap_to_grid(dt: datetime, tf_str: str) -> datetime:
    """
    Normaliza el timestamp al inicio de la vela correspondiente.
    Soporta formatos: 5m, 15m, 30m, 1h, 4h, 1d.
    """
    dt = dt.replace(second=0, microsecond=0)
    
    match = re.match(r"(\d+)([mhd])", tf_str)
    if not match:
        return dt # Fallback: return truncated seconds
        
    val = int(match.group(1))
    unit = match.group(2)
    
    if unit == 'm':
        # Minute snapping
        minute = (dt.minute // val) * val
        return dt.replace(minute=minute)
    elif unit == 'h':
        # Hour snapping (assumes val divides 24 or starts at 00:00)
        total_hours = dt.hour
        snapped_hours = (total_hours // val) * val
        return dt.replace(hour=snapped_hours, minute=0)
    elif unit == 'd':
        # Day snapping
        return dt.replace(hour=0, minute=0)
        
    return dt


def _write_to_db(signal: Signal, mode: str) -> bool:
    """
    Escritura exclusiva de DB para una señal.
    Retorna True si insertó, False si duplicado/error.
    """
    try:
        from database import SessionLocal
        from models_db import Signal as SignalDB  # Explicit import from backend package
        from sqlalchemy.exc import IntegrityError 

        # 1. Normalize Timestamp (Canonical)
        ts_normalized = _snap_to_grid(signal.timestamp, signal.timeframe)
        ts_iso = ts_normalized.isoformat()
        
        # 2. Compute Idempotency Key
        # Includes DIRECTION to allow hedging (Long+Short in same candle if logic permits)
        idem_key = (
            f"{signal.strategy_id}|{signal.token.upper()}|{signal.timeframe}|"
            f"{ts_iso}|{signal.direction.lower()}|{signal.user_id}|{signal.mode}"
        )

        # 3. Preparar datos para el modelo DB
        db_signal = SignalDB(
            timestamp=ts_normalized, # STORE NORMALIZED TS
            token=signal.token.upper(),
            timeframe=signal.timeframe,
            direction=signal.direction.lower(), # Normalize direction
            entry=signal.entry,
            tp=signal.tp if signal.tp else 0.0,
            sl=signal.sl if signal.sl else 0.0,
            confidence=signal.confidence if signal.confidence is not None else 0.0,
            rationale=signal.rationale if signal.rationale else "",
            source=signal.source,
            mode=mode,
            raw_response=str(signal.extra) if signal.extra else None,
            strategy_id=signal.strategy_id,
            idempotency_key=idem_key,
            user_id=signal.user_id,
            # is_saved default=0 (set by scheduler logic if needed, signal obj might not have it)
            # Actually scheduler sets dynamic attr, here we rely on defaults or pass it?
            # Signal schema doesn't have is_saved. It's an extra DB column.
            # We can leave default or add if passed in kwargs if we modify callers.
            # For now, default 0 is safe, scheduler updates it later? 
            # Wait, scheduler sets `sig.is_saved = 1` just before calling log_signal.
            # But `Signal` Pydantic model doesn't have `is_saved`.
            # We should check if `signal` object has `is_saved` attribute dynamically set by scheduler.
        )
        
        # Check dynamic attr from scheduler
        if hasattr(signal, "is_saved"):
            db_signal.is_saved = getattr(signal, "is_saved")

        db = SessionLocal()
        try:
            db.add(db_signal)
            db.commit()
            print(f"[DB] ✅ INSERT: {signal.token} {signal.direction} @ {ts_normalized}")
            return True

        except IntegrityError:
            db.rollback()
            # Silent Duplicate Skip
            # print(f"[DB] ℹ️ Duplicate ignored: {idem_key}") 
            return False

        except Exception as db_err:
            print(f"[DB] ❌ Error Insert: {db_err}")
            db.rollback()
            return False
        finally:
            db.close()

    except ImportError as imp_err:
        print(f"[DB] ⚠️  Import Error: {imp_err}")
        return False
    except Exception as e:
        print(f"[DB] ⚠️  Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def _write_to_csv(signal: Signal, mode: str, token_lower: str) -> None:
    """
    Escritura CSV (Solo si DB tuvo éxito).
    """
    mode_dir = LOGS_DIR / mode
    mode_dir.mkdir(parents=True, exist_ok=True)

    if mode == "EVALUATED":
        filename = f"{token_lower}.evaluated.csv"
    else:
        filename = f"{token_lower}.csv"

    filepath = mode_dir / filename
    file_exists = filepath.exists()

    # Convertir Signal a dict para CSV
    # NOTE: Use original timestamp for display, or normalized?
    # User asked for canonical. But CSV is log. Let's use signal.timestamp (the input).
    ts_str = signal.timestamp.replace(microsecond=0).isoformat() + "Z"
    
    row_data = {
        "timestamp": ts_str,
        "token": signal.token.upper(),
        "timeframe": signal.timeframe,
        "direction": signal.direction,
        "entry": signal.entry,
        "tp": signal.tp if signal.tp else "",
        "sl": signal.sl if signal.sl else "",
        "confidence": signal.confidence if signal.confidence is not None else "",
        "rationale": signal.rationale if signal.rationale else "",
        "source": signal.source,
    }

    try:
        with open(filepath, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row_data)
        # print(f"[CSV] ✅ Saved: {filepath}")
    except Exception as e:
        print(f"[CSV] ❌ Error: {e}")


def _send_push_notification(signal: Signal):
    """Encapsulated Push Logic."""
    try:
        from notify import send_push_notification

        title = f"New Signal: {signal.direction.upper()} {signal.token}"
        body = (
            f"Entry: {signal.entry} | TP: {signal.tp} | SL: {signal.sl}\n"
            f"Strategy: {signal.strategy_id or 'Unknown'}"
        )
        res = send_push_notification(
            title, body, data={"token": signal.token, "type": "signal"}
        )
        if res.get("success", 0) > 0:
            print(f"[PUSH] 🔔 Sent ({res['success']} devices).")
        # Fail silently if 0
    except Exception as push_err:
        print(f"[PUSH] ❌ Error: {push_err}")


def signal_from_dict(data: Dict[str, Any], mode: str, strategy_id: str) -> Signal:
    """Helper legacy."""
    ts = data.get("timestamp")
    if isinstance(ts, str):
        try:
            timestamp = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            timestamp = datetime.utcnow()
    elif isinstance(ts, datetime):
        timestamp = ts
    else:
        timestamp = datetime.utcnow()

    return Signal(
        timestamp=timestamp,
        strategy_id=strategy_id,
        mode=mode.upper(),
        token=data.get("token", "UNKNOWN").upper(),
        timeframe=data.get("timeframe", "30m"),
        direction=data.get("direction", "neutral"),
        entry=float(data.get("entry", 0)),
        tp=float(data["tp"]) if data.get("tp") else None,
        sl=float(data["sl"]) if data.get("sl") else None,
        confidence=(
            float(data["confidence"]) if data.get("confidence") is not None else None
        ),
        rationale=data.get("rationale"),
        source=data.get("source", "UNKNOWN"),
        extra=data.get("extra"),
    )
