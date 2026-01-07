import sys
import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

# Ensure backend modules are importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.signal_logger import log_signal, LOGS_DIR, _snap_to_grid
from core.schemas import Signal
from models_db import Signal as SignalDB, Base
# from database import engine as real_engine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# === FIXTURES ===

@pytest.fixture(scope="function")
def db_session():
    """
    Isolated SQLite DB for testing. 
    Replaces the real database engine for the duration of the test.
    """
    test_db_url = "sqlite:///./test_tc.db"
    test_engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # Create Tables
    Base.metadata.create_all(bind=test_engine)
    
    db = TestingSessionLocal()
    
    # Patch main session dependency
    with patch("database.SessionLocal", side_effect=lambda: TestingSessionLocal()):
        yield db
    
    db.close()
    test_engine.dispose() # Release file lock
    
    # Teardown
    if os.path.exists("./test_tc.db"):
        try:
            os.remove("./test_tc.db")
        except PermissionError:
            pass
    if os.path.exists("./test_tc.db-journal"):
        try:
            os.remove("./test_tc.db-journal")
        except PermissionError:
            pass

@pytest.fixture(scope="function")
def clean_logs():
    """Ensure logs directory is clean for specific test token."""
    token = "TEST_TOKEN"
    modes = ["TEST"]
    for m in modes:
        p = LOGS_DIR / m / f"{token.lower()}.csv"
        if p.exists():
            try:
                p.unlink()
            except PermissionError:
                pass 
    yield
    # Cleanup after
    for m in modes:
        p = LOGS_DIR / m / f"{token.lower()}.csv"
        if p.exists():
            try:
                p.unlink()
            except PermissionError:
                pass

# === TESTS ===

def test_snap_to_grid_timeframes():
    """
    Validates correctness of timestamp snapping.
    """
    base_ts = datetime(2025, 1, 1, 14, 23, 45)
    
    # 15m -> 14:15:00
    assert _snap_to_grid(base_ts, "15m") == datetime(2025, 1, 1, 14, 15, 0)
    # 1h -> 14:00:00
    assert _snap_to_grid(base_ts, "1h") == datetime(2025, 1, 1, 14, 0, 0)
    # 4h -> 12:00:00
    assert _snap_to_grid(base_ts, "4h") == datetime(2025, 1, 1, 12, 0, 0)
    # 1d -> 00:00:00
    assert _snap_to_grid(base_ts, "1d") == datetime(2025, 1, 1, 0, 0, 0)

def test_signal_dedupe_timestamp_variance(db_session, clean_logs):
    """
    Validation:
    1. Insert at 14:23:45 -> Snap to 14:00 -> SUCCESS.
    2. Insert at 14:59:59 -> Snap to 14:00 -> REJECTED (Duplicate Idempotency Key).
    """
    ts1 = datetime(2025, 1, 1, 14, 23, 45)
    ts2 = datetime(2025, 1, 1, 14, 59, 59)
    
    sig1 = Signal(
        timestamp=ts1, token="VAR_TOKEN", direction="long", entry=100.0, timeframe="1h",
        strategy_id="strat", mode="TEST", source="src", user_id=1
    )
    
    sig2 = sig1.model_copy()
    sig2.timestamp = ts2
    
    with patch("core.signal_logger._send_push_notification"):
        # 1. First Insert (14:23)
        assert log_signal(sig1) is True
        
        # 2. Second Insert (14:59) - Should be duplicate due to snap_to_grid(1h)
        assert log_signal(sig2) is False
        
        # Verify DB Count
        rows = db_session.query(SignalDB).filter(SignalDB.token == "VAR_TOKEN").all()
        assert len(rows) == 1
        assert rows[0].timestamp == datetime(2025, 1, 1, 14, 0, 0)


def test_signal_dedupe_db_first_and_no_csv_sideeffects(db_session, clean_logs):
    """
    Ensures duplicate insertion does NOT trigger CSV write or push.
    """
    ts = datetime(2025, 1, 1, 14, 23, 45) # Scnaps to 14:00
    
    sig = Signal(
        timestamp=ts, token="TEST_TOKEN", direction="long", entry=100.0, timeframe="1h",
        strategy_id="test_strat", mode="TEST", source="unit_test", user_id=1
    )
    
    with patch("core.signal_logger._send_push_notification") as mock_push:
        # 1. First Insert
        assert log_signal(sig) is True
        
        csv_path = LOGS_DIR / "TEST" / "test_token.csv"
        assert csv_path.exists()
        with open(csv_path) as f:
            assert len(f.readlines()) == 2 # Header + 1 row
        mock_push.assert_called_once()
        
        # 2. Second Insert (Same TS)
        mock_push.reset_mock()
        assert log_signal(sig) is False
        
        # Verify CSV unchanged
        with open(csv_path) as f:
            assert len(f.readlines()) == 2
        mock_push.assert_not_called()


def test_idempotency_key_includes_direction(db_session):
    """
    Verifies that LONG and SHORT signals in the same candle do NOT collide.
    """
    ts = datetime(2025, 1, 1, 14, 23, 45)
    sig_long = Signal(
        timestamp=ts, token="HEDGE_TOKEN", direction="long", entry=100.0,
        timeframe="1h", strategy_id="hedge", mode="TEST", source="src", user_id=1
    )
    sig_short = sig_long.model_copy()
    sig_short.direction = "short"
    
    assert log_signal(sig_long) is True
    assert log_signal(sig_short) is True # Should succeed
    
    rows = db_session.query(SignalDB).filter(SignalDB.token == "HEDGE_TOKEN").all()
    assert len(rows) == 2


def test_scheduler_process_signal_no_notify(db_session):
    """
    Uses the real StrategyScheduler.process_single_signal method (refactored).
    Verifies that if log_signal returns False, send_telegram is NOT called.
    """
    from scheduler import StrategyScheduler
    
    # Mock Notification dependencies
    with patch("scheduler.send_telegram") as mock_telegram, \
         patch("core.signal_logger._write_to_csv"), \
         patch("core.signal_logger._send_push_notification"):
             
        # Create minimal scheduler instance (no loops)
        # Suppress prints in init or mocked logger if needed, but logging is usually fine
        with patch("builtins.print"): 
            scheduler = StrategyScheduler(loop_interval=1)
        
        # Reset cache
        scheduler.dedupe_cache = {}
        
        ts = datetime(2025, 1, 1, 10, 30, 0)
        persona = {
            "id": "p1", "strategy_id": "s1", "name": "Persona1", 
            "timeframe": "1h", "telegram_chat_id": 12345, "user_id": 1
        }
        
        sig = Signal(
            timestamp=ts, token="SCHED_TEST", direction="long", entry=1.0, timeframe="1h",
            strategy_id="s1", mode="TEST", source="src", user_id=1
        )
        
        # 1. First Call -> True -> Notify
        scheduler.process_single_signal(sig, persona)
        mock_telegram.assert_called_once()
        print("\n   [Test] First call triggered notification (Correct)")
        
        # 2. Second Call (Duplicate) -> False -> No Notify
        mock_telegram.reset_mock()
        scheduler.process_single_signal(sig, persona)
        mock_telegram.assert_not_called()
        print("   [Test] Second call ignored (Correct)")


def test_concurrency_dedupe(db_session):
    """
    Stress Test: 5 Threads trying to insert the same candle (different seconds).
    Expected: Only 1 success, 4 failures.
    """
    import concurrent.futures
    
    # 12:00:00 base. All vars will be 12:00:xx, snapping to 12:00:00 (1h)
    ts_base = datetime(2025, 1, 1, 12, 0, 0)
    
    def worker_insert(i):
        # Each worker tries a different second
        ts = ts_base + timedelta(seconds=i*10)
        sig = Signal(
            timestamp=ts, token="RACE_TOKEN", direction="long", entry=10.0, timeframe="1h",
            strategy_id="conc_strat", mode="TEST", source="thread", user_id=1
        )
        # Suppress prints
        with patch("builtins.print"): 
             return log_signal(sig)

    results = []
    # Using real log_signal with mocked push to avoid noise
    with patch("core.signal_logger._send_push_notification"), \
         patch("core.signal_logger._write_to_csv"): # Mock CSV to avoid file lock issues in threads
         
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker_insert, i) for i in range(5)]
            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())
    
    success_count = sum(1 for r in results if r is True)
    fail_count = sum(1 for r in results if r is False)
    
    print(f"\n   [Concurrency] Success: {success_count}, Failed: {fail_count}")
    
    assert success_count == 1
    assert fail_count == 4
    
    # Verify strict DB count
    cnt = db_session.query(SignalDB).filter(SignalDB.token == "RACE_TOKEN").count()
    assert cnt == 1

@pytest.mark.pg
def test_postgres_integration_concurrency():
    """
    Real Integration Test with Postgres.
    Requires running Postgres instance.
    """
    # Attempt connection or skip
    pg_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/trader_copilot_test")
    
    try:
        engine = create_engine(pg_url)
        with engine.connect() as _:
            pass
    except Exception:
        pytest.skip(f"Postgres not available at {pg_url}")
        
    TestingSessionPG = sessionmaker(bind=engine)
    
    # Clean table
    # WARNING: This truncates the test table given in URL.
    try:
        fake_sess = TestingSessionPG()
        fake_sess.execute("TRUNCATE TABLE signals RESTART IDENTITY CASCADE;")
        fake_sess.commit()
    except Exception:
        # Fallback if truncate fails (e.g. permissions)
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
    finally:
        fake_sess.close()
        
    # Patch SessionLocal to use PG
    with patch("database.SessionLocal", side_effect=lambda: TestingSessionPG()):
        
        # Reuse Concurrency Logic
        import concurrent.futures
        ts_base = datetime(2025, 2, 1, 12, 0, 0) # Future date
        
        def worker_insert(i):
            ts = ts_base + timedelta(seconds=i*5)
            # Use 'long' for all to trigger Idempotency collision on same timeframe (1h)
            sig = Signal(
                timestamp=ts, token="PG_RACE_TOKEN", direction="long", entry=50000.0, timeframe="1h",
                strategy_id="pg_strat", mode="TEST", source="thread_pg", user_id=1
            )
            with patch("builtins.print"):
                return log_signal(sig)

        results = []
        with patch("core.signal_logger._send_push_notification"), \
             patch("core.signal_logger._write_to_csv"):
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(worker_insert, i) for i in range(5)]
                for f in concurrent.futures.as_completed(futures):
                    results.append(f.result())
        
        success = sum(1 for r in results if r is True)
        fail = sum(1 for r in results if r is False)
        
        assert success == 1
        assert fail == 4
        
        # Verify in PG
        verify_sess = TestingSessionPG()
        count = verify_sess.query(SignalDB).filter(SignalDB.token == "PG_RACE_TOKEN").count()
        verify_sess.close()
        assert count == 1
