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
                    "user_id": c.user_id, # [FIX] Isolation: Pass owner ID
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
    Scheduler de Estrategias (Modo Marketplace - Parallelized).

    Ejecuta las 'Personas' definidas en DB usando ThreadPool
    para evitar bloqueos cuando hay muchos tokens.
    """

    def __init__(self, loop_interval: int = 60):
        self.loop_interval = loop_interval
        self.registry = get_registry()

        print("=" * 60)
        print("= TraderCopilot - Marketplace Scheduler (Parallel DB Powered)")
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
        self.lock_ttl = 300  # 5 mins (Safe buffer > loop_interval)
        self.lock_name = "global_scheduler_lock"

        # Deduplication Cache for Notifications
        self.dedupe_cache = {}

        # Coherence Guard (Global Trend State)
        # Key: "Token" -> Value: { 'direction': 'long', 'ts': datetime, 'conf': 0.8 }

        # Used to reject conflicting signals (Long -> Short) if they happen too fast (Chop protection)
        self.token_coherence = {}
        
        # [NEW] Executor for Parallel Execution
        # We limit to 5 workers to prevent DB connection exhaustion if pooling set to 20
        self.max_workers = 5

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
        
    def _execute_strategy_task(self, persona):
        """
        Worker function to execute a single strategy instance.
        Returns generated signals or empty list.
        Safe for threading (no shared state modification here).
        """
        strategy_id = persona["strategy_id"]
        strategy = self.registry.get(strategy_id)

        if not strategy:
            # print(f"  ⚠️  Strategy class '{strategy_id}' not found!")
            return []

        try:
            # print(f"   [Worker] Running {persona['name']}...")
            # Each strategy instance inside generate_signals acts locally
            signals = strategy.generate_signals(
                tokens=persona["tokens"], timeframe=persona["timeframe"]
            )
            return signals
        except Exception as e:
            print(f"  ❌ Error executing {persona['name']} in worker: {e}")
            return []

    def run(self):
        """Loop principal."""
        import concurrent.futures
        
        iteration = 0
        try:
            while True:
                # 0. Gestion de Lock
                db = SessionLocal()
                try:
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
                now = datetime.utcnow()
                ba_time = now - timedelta(hours=3)
                print(f"\n[{ba_time.strftime('%H:%M:%S')}] Iteration #{iteration}")

                # 1. Obtener Personas Activas (DB)
                personas = get_active_strategies_from_db()
                print(f"  ℹ️  Active Personas: {len(personas)}")
                
                # 2. Parallel Execution
                all_signals_map = {} # {persona_id: [signals]}
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    # Submit all tasks
                    future_to_persona = {
                        executor.submit(self._execute_strategy_task, p): p 
                        for p in personas
                    }
                    
                    for future in concurrent.futures.as_completed(future_to_persona):
                        p = future_to_persona[future]
                        try:
                            signals = future.result()
                            if signals:
                                all_signals_map[p["id"]] = signals
                        except Exception as exc:
                            print(f"  ❌ {p['name']} generated an exception: {exc}")

                # 3. Sequential Processing (Dedupe, Notify, DB Log)
                # Ensure shared state is updated safely in Main Thread
                for p in personas:
                    p_id = p["id"]
                    signals = all_signals_map.get(p_id, [])
                    
                    # Update heartbeat for stats potentially
                    self.last_run[p_id] = now
                    
                    if not signals:
                        continue
                        
                    for sig in signals:
                        # 1. Deduplication (Optimized)
                        # REMOVED: Inefficient DB query per signal.
                        # We rely on 'log_signal' triggering IntegrityError via UniqueConstraint/IdempotencyKey.
                        # This avoids opening N connections per cycle.

                        # 2. In-Memory Deduplication
                        ts_key = f"{p_id}_{sig.token}_{sig.direction}_{sig.timestamp}"
                        last_ts = self.processed_signals.get(ts_key)
                        if last_ts and sig.timestamp <= last_ts:
                            continue

                        # 3. Same-Side Spam check
                        direction_key = f"{p_id}_{sig.token}"
                        last_dir = self.last_signal_direction.get(direction_key)
                        if last_dir == sig.direction:
                            if last_ts and (sig.timestamp - last_ts).total_seconds() < 60:
                                continue

                        # 4. Global Coherence
                        coherence_key = sig.token
                        last_state = self.token_coherence.get(coherence_key)
                        now_utc = datetime.utcnow()

                        if last_state:
                            last_global_dir = last_state["direction"]
                            last_global_ts = last_state["ts"]
                            if last_global_dir != sig.direction:
                                if (now_utc - last_global_ts) < timedelta(minutes=30):
                                    continue

                        # Updates Shared State
                        self.token_coherence[coherence_key] = {"direction": sig.direction, "ts": now_utc}
                        # Process Signal
                        self.process_single_signal(sig, p)

                # 4. Evaluador PnL
                try:
                    eval_db = SessionLocal()
                    try:
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

    def process_single_signal(self, sig, p):
        """
        Public method for testing.
        Handles Canonical Dedupe log -> If inserted -> Notify.
        """
        # Metadata
        sig.source = f"Marketplace:{p['id']}"
        sig.strategy_id = p['id']
        sig.is_saved = 1
        sig.user_id = p.get("user_id")

        now = datetime.utcnow()

        # Log DB (Canonical Dedupe)
        try:
            inserted = log_signal(sig)
            if inserted:
                print(f"  ✅ Logged Signal: {sig.token} {sig.direction} ({p['name']})")
            else:
                # Duplicate ignored
                return 
        except Exception as e:
            print(f"    ❌ Failed to log signal: {e}")
            return

        # Notification (Only if inserted)
        dedupe_key = f"{p['id']}_{sig.token}_{sig.direction}"
        last_notif = self.dedupe_cache.get(dedupe_key)
        if last_notif and (now - last_notif < timedelta(minutes=45)):
            return

        self.dedupe_cache[dedupe_key] = now

        try:
            icon = "🟢" if sig.direction == "long" else "🔴"
            msg = (
                f"{icon} {sig.direction.upper()}: {sig.token} / USDT\n\n"
                f"Entry: {sig.entry}\n"
                f"Target: {sig.tp}\n"
                f"Stop:   {sig.sl}\n\n"
                f"⚡ Strategy: {p['name']} ({p['timeframe']})"
            )
            chat_id = p.get("telegram_chat_id")
            if chat_id:
                send_telegram(msg, chat_id=chat_id)
        except Exception as notif_err:
            print(f"    ⚠️ Notification failed: {notif_err}")


# Expose instance for imports
scheduler_instance = StrategyScheduler(loop_interval=60)

if __name__ == "__main__":
    scheduler_instance.run()

