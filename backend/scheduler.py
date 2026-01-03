# backend/scheduler.py
"""
Simple Strategy Scheduler (Marketplace Edition)

Script que ejecuta las "Personas" del Marketplace en loop constante.
NO requiere Docker ni cron, solo:
    python scheduler.py
"""

import sys
import time
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import uuid
from sqlalchemy.orm import Session


# Setup path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from database import SessionLocal  # noqa: E402
from strategies.registry import get_registry  # noqa: E402
from core.signal_evaluator import evaluate_pending_signals  # noqa: E402
from core.signal_logger import log_signal  # noqa: E402
from models_db import StrategyConfig, User  # noqa: E402
from notify import send_telegram  # noqa: E402
from data.supported_tokens import VALID_TOKENS_FULL  # noqa: E402

# Configuración de Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [SCHEDULER] - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def get_active_strategies_from_db():
    """
    Recupera las estrategias activas directamente de PostgreSQL (StrategyConfig).
    Retorna una lista de diccionarios compatibles con el formato esperado por el scheduler.
    """
    db = SessionLocal()
    try:
        # Join with User to get Telegram preferences
        results = (
            db.query(StrategyConfig, User.telegram_chat_id)
            .outerjoin(User, StrategyConfig.user_id == User.id)
            .filter(StrategyConfig.enabled == 1)
            .all()
        )

        strategies = []
        for c, chat_id in results:
            # Parse JSON fields safely
            try:
                tokens_list = json.loads(c.tokens) if c.tokens else []
            except Exception:
                tokens_list = []

            try:
                tf_list = json.loads(c.timeframes) if c.timeframes else []
            except Exception:
                tf_list = []

            # --- TOKEN LIST LOGIC ---
            # If the strategy is configured with "ALL" or "SCANNER" as the symbol,
            # or if the tokens list is empty, we treat it as a SCANNER strategy
            # that runs on the full list.

            primary_symbol = tokens_list[0] if tokens_list else "BTC"

            # Special 'Marker' logic for System Scanners
            if primary_symbol in ["ALL", "SCANNER", "*"]:
                logger.info(
                    f"  ✨ Detected Scanner Strategy: {c.name} -> Expanding to {len(VALID_TOKENS_FULL)} tokens"
                )
                target_tokens = VALID_TOKENS_FULL
            else:
                # Default: Use the specific tokens configured (or just the first one for now)
                # Ideally, we should iterate all tokens in tokens_list
                # For now, let's just make target_tokens a list
                target_tokens = tokens_list if tokens_list else ["BTC"]

            target_tf = tf_list[0] if tf_list else "1h"

            strategies.append(
                {
                    "id": c.persona_id,  # "trend_king_sol"
                    "strategy_id": c.strategy_id,  # "donchian_v2"
                    "tokens": target_tokens,  # Pass LIST of tokens
                    "timeframe": target_tf,
                    "name": c.name,
                    "telegram_chat_id": chat_id,
                }
            )

        return strategies
    except Exception as e:
        logger.error(f"Error fetching strategies from DB: {e}")
        return []
    finally:
        db.close()


class StrategyScheduler:
    """
    Scheduler de Estrategias (Modo Marketplace).

    Ejecuta las 'Personas' definidas en marketplace_config.py
    """

    def __init__(self, loop_interval: int = 60):
        self.loop_interval = loop_interval
        self.registry = get_registry()

        print("=" * 60)
        print("= TraderCopilot - Marketplace Scheduler (DB Powered)")
        print("=" * 60)

        # Registrar estrategias built-in
        print("\n [INFO] Registering strategies...")
        from strategies.example_rsi_macd import RSIMACDDivergenceStrategy
        from strategies.ma_cross import MACrossStrategy
        from strategies.DonchianBreakoutV2 import DonchianBreakoutV2 as DonchianStrategy
        from strategies.bb_mean_reversion import BBMeanReversionStrategy
        from strategies.rsi_divergence import RSIDivergenceStrategy
        from strategies.TrendFollowingNative import TrendFollowingNative
        from strategies.DonchianBreakoutV2 import DonchianBreakoutV2

        self.registry.register(RSIMACDDivergenceStrategy)
        self.registry.register(MACrossStrategy)
        self.registry.register(DonchianStrategy)
        self.registry.register(BBMeanReversionStrategy)
        self.registry.register(RSIDivergenceStrategy)
        self.registry.register(TrendFollowingNative)
        self.registry.register(DonchianBreakoutV2)
        print(" [INFO] Strategies registered")

        # State tracking for intervals
        self.last_run = {}  # {persona_id: timestamp}
        self.processed_signals = {}  # {signal_key: timestamp}
        self.last_signal_direction = {}  # {persona_id_token: direction} (For alternation enforcement)

        # Lock Config
        self.lock_id = str(uuid.uuid4())
        self.lock_ttl = 30  # seconds
        self.lock_name = "global_scheduler_lock"

        # Deduplication Cache for Notifications
        # Key: "Token_Direction_Timeframe" -> Value: timestamp
        self.dedupe_cache = {}

        # Coherence Guard (Global Trend State)
        # Key: "Token" -> Value: { 'direction': 'long', 'ts': datetime, 'conf': 0.8 }

        # Used to reject conflicting signals (Long -> Short) if they happen too fast (Chop protection)
        self.token_coherence = {}

    def acquire_lock(self, db: Session) -> bool:
        """Intenta adquirir o renovar el lock de base de datos."""
        from models_db import SchedulerLock

        now = datetime.utcnow()
        lock = (
            db.query(SchedulerLock)
            .filter(SchedulerLock.lock_name == self.lock_name)
            .first()
        )

        if not lock:
            # Create fresh lock
            try:
                lock = SchedulerLock(
                    lock_name=self.lock_name,
                    owner_id=self.lock_id,
                    expires_at=now + timedelta(seconds=self.lock_ttl),
                )
                db.add(lock)
                db.commit()
                print(f"🔒 Lock acquired (new): {self.lock_id}")
                return True
            except Exception:
                db.rollback()
                return False

        # Check if expired or mine
        if lock.expires_at < now or lock.owner_id == self.lock_id:
            lock.owner_id = self.lock_id
            lock.expires_at = now + timedelta(seconds=self.lock_ttl)
            db.commit()
            return True

        print(f"🔒 Lock held by other instance ({lock.owner_id}). Retrying...")
        return False

    def run(self):
        """Loop principal."""
        iteration = 0
        try:
            while True:
                # 0. Gestion de Lock
                # Cada iteración intentamos renovar. Si perdemos el lock, esperamos.
                db = SessionLocal()
                try:
                    # Ensure table exists? Assume migration did it.
                    # On SQLite simple check helps avoid initial crash if table missing
                    # but main.py should have created it.
                    if not self.acquire_lock(db):
                        print("⏳ Waiting for lock...")
                        time.sleep(10)
                        continue
                except Exception as e:
                    print(f"⚠️ Lock Error: {e}")
                    time.sleep(5)
                    continue
                finally:
                    db.close()

                iteration += 1
                # User requests Buenos Aires Time (UTC-3) for logs
                now = datetime.utcnow()
                ba_time = now - timedelta(hours=3)
                print(f"\n[{ba_time.strftime('%H:%M:%S')}] Iteration #{iteration}")

                # 1. Obtener Personas Activas (DB)
                personas = get_active_strategies_from_db()
                print(f"  ℹ️  Active Personas: {len(personas)}")

                # 2. Ejecutar cada Persona
                for persona in personas:
                    p_id = persona["id"]

                    # Rate Limit simple (ej: cada 5 mins para todos, o custom)
                    # Por ahora, usamos interval global de loop (60s)
                    # Si quisiéramos per-strategy intervals, checkeamos self.last_run[p_id]

                    print(
                        f"  🔄 Running Persona: {persona['name']} "
                        f"(Tokens: {len(persona['tokens'])} | TF: {persona['timeframe']})"
                    )

                    # Instanciar estrategia técnica
                    strategy_id = persona["strategy_id"]
                    strategy = self.registry.get(strategy_id)

                    if not strategy:
                        print(f"  ⚠️  Strategy class '{strategy_id}' not found!")
                        continue

                    try:
                        # Ejecutar con lista de tokens (Multitoken Support)
                        signals = strategy.generate_signals(
                            tokens=persona["tokens"], timeframe=persona["timeframe"]
                        )

                        count = 0
                        for sig in signals:
                            # 1. Deduplication (DB Strict Check)
                            # Check DB for EXACT signal (same timestamp)
                            # This prevents duplicates if scheduler restarts and the candle is still valid
                            dedupe_db = SessionLocal()
                            try:
                                from models_db import Signal as SignalModel
                                exists = dedupe_db.query(SignalModel).filter(
                                    SignalModel.strategy_id == p_id,
                                    SignalModel.token == sig.token,
                                    SignalModel.direction == sig.direction,
                                    SignalModel.timestamp == sig.timestamp, # [FIX] Strict timestamp match
                                    SignalModel.is_saved == 1
                                ).first()
                                
                                if exists:
                                    # print(f"    🔕 DB Dedupe: Skipping {sig.token} (already processed)")
                                    dedupe_db.close()
                                    continue
                            except Exception as e:
                                print(f"    ⚠️ DB Dedupe Error: {e}")
                            finally:
                                dedupe_db.close()

                            # 2. In-Memory Deduplication (Fast)
                            # Create a unique key for this exact signal instance
                            ts_key = f"{p_id}_{sig.token}_{sig.direction}_{sig.timestamp}"
                            
                            last_ts = self.processed_signals.get(ts_key)
                            if last_ts and sig.timestamp <= last_ts:
                                continue

                            # 3. Prevent same-side spam (Visual Clarity)
                            # Check the last direction for this specific persona/token combo
                            direction_key = f"{p_id}_{sig.token}"
                            last_dir = self.last_signal_direction.get(direction_key)
                            if last_dir == sig.direction:
                                # Only skip if timestamps are very close (e.g. same candle repaint)
                                if last_ts and (sig.timestamp - last_ts).total_seconds() < 60:
                                    continue

                            # ==== 4. Coherence Guard (Anti-Chop) ====
                            # Ensures we don't flip-flop direction too fast for the same token
                            coherence_key = sig.token
                            last_state = self.token_coherence.get(coherence_key)
                            
                            now_utc = datetime.utcnow() # Use local variable for consistency

                            if last_state:
                                last_global_dir = last_state["direction"]
                                last_global_ts = last_state["ts"]

                                # Conflict detected? (Opposite direction)
                                if last_global_dir != sig.direction:
                                    # If conflict happens within 30 minutes, likely noise. Suppress.
                                    if (now_utc - last_global_ts) < timedelta(minutes=30):
                                        continue




                            # Update Global Coherence State
                            self.token_coherence[coherence_key] = {
                                "direction": sig.direction,
                                "ts": now_utc,
                            }

                            self.processed_signals[ts_key] = sig.timestamp
                            self.last_signal_direction[direction_key] = sig.direction

                            # Enriquecer source con el ID de la persona
                            # Fix user confusion: Use the Human Readable Name? No, Marketplace:{ID}
                            # is safer for filtering.
                            sig.source = f"Marketplace:{p_id}"

                            # to the specific instance (1234), not the generic logic (ma_cross_v1).
                            # This allows separate history and purging for distinct personas using same logic.
                            sig.strategy_id = p_id
                            sig.is_saved = 1  # [FIX] Mark as permanent/official history

                            # [FIX] Persist Signal to DB/CSV
                            try:
                                log_signal(sig)
                            except Exception as e:
                                print(f"    ❌ Failed to log signal: {e}")

                            # Deduplication Logic (Notification Layer)
                            # Prevent spam if the same strategy sends same signal (even with new TS) within X mins
                            dedupe_key = f"{p_id}_{sig.token}_{sig.direction}"
                            last_notif = self.dedupe_cache.get(dedupe_key)

                            # Cooldown: 45 minutes (approx 1h candle)
                            if last_notif and (
                                now - last_notif < timedelta(minutes=45)
                            ):
                                # print(f"    🔕 Suppressing duplicate notification: {dedupe_key}")
                                continue

                            self.dedupe_cache[dedupe_key] = now

                            # ==== TELEGRAM NOTIFICATION ====
                            try:
                                icon = "🟢" if sig.direction == "long" else "🔴"
                                msg = (
                                    f"{icon} {sig.direction.upper()}: {sig.token} / USDT\n\n"
                                    f"Entry: {sig.entry}\n"
                                    f"Target: {sig.tp}\n"
                                    f"Stop:   {sig.sl}\n\n"
                                    f"⚡ Strategy: {persona['name']} ({persona['timeframe']})"
                                )
                                # Send to specific user (if configured) or system default (if None)
                                send_telegram(
                                    msg, chat_id=persona.get("telegram_chat_id")
                                )
                            except Exception as notif_err:
                                print(f"    ⚠️ Notification failed: {notif_err}")
                            except Exception as notif_err:
                                print(f"    ⚠️ Notification failed: {notif_err}")

                        if count == 0:
                            print("    (No new signals)")

                        self.last_run[p_id] = now

                    except Exception as e:
                        print(f"  ❌ Error executing {persona['name']}: {e}")

                # 3. Evaluador PnL (Critico para mostrar profit real)
                # print("  ⚖️  Evaluating Pending Signals...") # Less verbose
                try:
                    eval_db = SessionLocal()
                    try:
                        # Ensure we use a fresh session to avoid transaction issues
                        new_evals = evaluate_pending_signals(eval_db)
                        if new_evals > 0:
                            print(f"  ✅ Evaluated {new_evals} signals")
                    finally:
                        eval_db.close()

                except Exception as e:
                    print(f"  ❌ Eval Error: {e}")

                print(f"  😴 Sleeping {self.loop_interval}s...")
                time.sleep(self.loop_interval)

        except KeyboardInterrupt:
            print("\n🛑 Stopped.")


# Expose instance for imports
scheduler_instance = StrategyScheduler(loop_interval=60)

if __name__ == "__main__":
    scheduler_instance.run()
