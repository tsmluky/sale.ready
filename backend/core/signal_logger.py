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


def log_signal(signal: Signal) -> None:
    """
    Guarda una señal en el CSV adecuado según modo/token Y en la base de datos.

    Args:
        signal: Instancia del modelo Signal unificado

    Comportamiento:
    - CSV: logs/{MODE}/{token}.csv (token en minúsculas)
    - DB: tabla Signal con todos los campos del modelo
    
    Notas:
    - El campo 'extra' (dict libre) se convierte a string JSON para CSV
    - El modo EVALUATED tiene fichero especial: {token}.evaluated.csv
      (pero se recomienda usar evaluated_logger.py para ese caso específico)
    """
    
    mode = signal.mode.upper()
    token_lower = signal.token.lower()

    # === 1. Persistir en CSV (legacy/backup) ===
    _write_to_csv(signal, mode, token_lower)

    # === 2. Persistir en base de datos ===
    _write_to_db(signal, mode)


def _write_to_csv(signal: Signal, mode: str, token_lower: str) -> None:
    """
    Escritura exclusiva de CSV para una señal.
    
    Estructura de directorios:
    - logs/LITE/{token}.csv
    - logs/PRO/{token}.csv
    - logs/ADVISOR/{token}.csv
    - logs/EVALUATED/{token}.evaluated.csv (si mode == EVALUATED)
    - logs/CUSTOM/{token}.csv (para futuras estrategias de trading_lab)
    """
    mode_dir = LOGS_DIR / mode
    mode_dir.mkdir(parents=True, exist_ok=True)

    # Nombre del fichero según modo
    if mode == "EVALUATED":
        filename = f"{token_lower}.evaluated.csv"
    else:
        filename = f"{token_lower}.csv"

    filepath = mode_dir / filename
    file_exists = filepath.exists()

    # Convertir Signal a dict para CSV (solo campos básicos, no 'extra')
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
        print(f"[CSV] ✅ Señal guardada: {filepath}")
    except Exception as e:
        print(f"[CSV] ❌ Error escribiendo CSV en {filepath}: {e}")
        # No relanzamos para que el flujo continúe si al menos DB funciona


def _write_to_db(signal: Signal, mode: str) -> None:
    """
    Escritura exclusiva de DB para una señal.
    
    Guarda en la tabla Signal usando el ORM de SQLAlchemy.
    Si falla, no interrumpe el flujo (ya se guardó en CSV).
    """
    try:
        from database import SessionLocal
        from models_db import Signal as SignalDB # Explicit import from backend package
        from sqlalchemy.exc import IntegrityError

        # Compute Idempotency Key
        ts_iso = signal.timestamp.isoformat()
        idem_key = f"{signal.strategy_id}|{signal.token.upper()}|{signal.timeframe}|{ts_iso}|{signal.user_id}|{signal.mode}"

        # Preparar datos para el modelo DB
        db_signal = SignalDB(
            timestamp=signal.timestamp,
            token=signal.token.upper(),
            timeframe=signal.timeframe,
            direction=signal.direction,
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
            user_id=signal.user_id
        )

        db = SessionLocal()
        try:
            db.add(db_signal)
            db.commit()
            ts_str = signal.timestamp.replace(microsecond=0).isoformat() + "Z"
            print(f"[DB] ✅ Señal guardada en DB: {mode} - {signal.token} - {ts_str}")
            
            # --- NOTIFICACIÓN PUSH ---
            try:
                from notify import send_push_notification
                title = f"New Signal: {signal.direction.upper()} {signal.token}"
                body = f"Entry: {signal.entry} | TP: {signal.tp} | SL: {signal.sl}\nStrategy: {signal.strategy_id or 'Unknown'}"
                res = send_push_notification(title, body, data={"token": signal.token, "type": "signal"})
                if res.get("success", 0) > 0:
                    print(f"[PUSH] 🔔 Notificación enviada a {res['success']} dispositivos.")
                elif res.get("failed", 0) > 0:
                    print(f"[PUSH] ⚠️ Fallo al enviar notificaciones ({res['failed']} fallidos).")
            except Exception as push_err:
                print(f"[PUSH] ❌ Error enviando push: {push_err}")
            # -------------------------

        except IntegrityError:
            db.rollback()
            print(f"[DB] ℹ️ Signal ignored (Duplicate Idempotency Key): {idem_key}")

        except Exception as db_err:
            print(f"[DB] ❌ Error CRÍTICO al guardar en DB: {db_err}")
            db.rollback()
            # No relanzamos para que al menos CSV esté persistido
        finally:
            db.close()

    except ImportError as imp_err:
        print(f"[DB] ⚠️  No se pudo importar database/models_db: {imp_err}")
    except Exception as e:
        print(f"[DB] ⚠️  Error inesperado en _write_to_db: {e}")
        import traceback
        traceback.print_exc()


# === Funciones auxiliares para migración/transición ===

def signal_from_dict(data: Dict[str, Any], mode: str, strategy_id: str) -> Signal:
    """
    Helper para crear una instancia Signal desde un diccionario legacy.
    
    Útil para refactorizar código existente que usa dicts en vez de Signal.
    
    Args:
        data: Diccionario con campos de señal
        mode: Modo del análisis (LITE, PRO, ADVISOR, etc.)
        strategy_id: ID de la estrategia generadora
        
    Returns:
        Instancia de Signal lista para usar con log_signal()
    """
    # Parse timestamp si viene como string
    ts = data.get("timestamp")
    if isinstance(ts, str):
        try:
            timestamp = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except:
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
        confidence=float(data["confidence"]) if data.get("confidence") is not None else None,
        rationale=data.get("rationale"),
        source=data.get("source", "UNKNOWN"),
        extra=data.get("extra"),
    )
