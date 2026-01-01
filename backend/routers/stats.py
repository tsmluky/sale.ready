from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from datetime import datetime, timedelta
import models_db
from database import get_db
from routers.auth_new import get_current_user
from models_db import User, Signal, SignalEvaluation

router = APIRouter(
    tags=["Stats"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/dashboard")
def get_dashboard_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns aggregated stats and chart data for the dashboard.
    User-scoped: shows signals created by the user or system signals visible to them.
    """
    try:
        # 1. Calculate Summary Stats (Win Rate, Open Signals, PnL)
        summary = compute_stats_summary(db, current_user)
        
        # 2. Calculate Chart Data (7 Days Performance)
        chart_data = get_performance_chart(db, current_user)
        
        return {
            "summary": summary,
            "chart": chart_data
        }
    except Exception as e:
        print(f"[STATS] Error calculating dashboard stats: {e}")
        # Return safe defaults in case of error to prevent frontend crash
        return {
            "summary": {
                "win_rate_24h": 0,
                "signals_evaluated_24h": 0,
                "signals_total_evaluated": 0,
                "open_signals": 0,
                "pnl_7d": 0.0
            },
            "chart": []
        }

def compute_stats_summary(db: Session, user: User):
    day_ago = datetime.utcnow() - timedelta(hours=24)
    week_ago = datetime.utcnow() - timedelta(days=7)
    test_sources = ['audit_script', 'verification']
    
    # Base Query Helper
    def get_base_signal_query():
        q = db.query(Signal)
        q = q.filter(Signal.source.notin_(test_sources))
        
        # User Scoping
        if user.created_at:
             q = q.filter(Signal.timestamp >= user.created_at)
        
        # Owner/System logic
        # STRICT: Only show User's OWN Saved/Tracked signals for Dashboard Stats
        # This prevents transient scans or system noise from polluting "My Performance"
        q = q.filter(
            Signal.user_id == user.id,
            Signal.is_saved == 1
        )
        return q

    # 1. Total Evaluated (All Time)
    q_total = db.query(func.count(SignalEvaluation.id)).join(Signal)
    q_total = q_total.filter(
        Signal.source.notin_(test_sources),
        Signal.user_id == user.id,
        Signal.is_saved == 1
    )
    if user.created_at:
        q_total = q_total.filter(Signal.timestamp >= user.created_at)
    total_eval = q_total.scalar() or 0

    # 2. Evaluations Last 24h
    q_eval_24 = db.query(func.count(SignalEvaluation.id)).join(Signal)
    q_eval_24 = q_eval_24.filter(
        SignalEvaluation.evaluated_at >= day_ago,
        Signal.source.notin_(test_sources),
        Signal.user_id == user.id,
        Signal.is_saved == 1
    )
    if user.created_at:
        q_eval_24 = q_eval_24.filter(Signal.timestamp >= user.created_at)
    eval_24h_count = q_eval_24.scalar() or 0

    # 3. Wins Last 24h (for Win Rate)
    q_wins = db.query(func.count(SignalEvaluation.id)).join(Signal).filter(
        SignalEvaluation.evaluated_at >= day_ago,
        SignalEvaluation.result == 'WIN',
        Signal.source.notin_(test_sources),
        Signal.user_id == user.id,
        Signal.is_saved == 1
    )
    if user.created_at:
        q_wins = q_wins.filter(Signal.timestamp >= user.created_at)
    wins_24h = q_wins.scalar() or 0

    # Win Rate Calculation
    win_rate_24h = (wins_24h / eval_24h_count * 100) if eval_24h_count > 0 else 0

    # 4. Open Signals (Estimated: Created 24h - Evaluated 24h)
    # Count LITE/PRO signals created in last 24h
    q_created_24 = get_base_signal_query().filter(Signal.timestamp >= day_ago)
    created_24h = q_created_24.count()
    open_signals_est = max(0, created_24h - eval_24h_count) # Simplistic estimation

    # 5. PnL Last 7 Days
    q_pnl = db.query(func.sum(SignalEvaluation.pnl_r)).join(Signal).filter(
        SignalEvaluation.evaluated_at >= week_ago,
        Signal.source.notin_(test_sources),
        Signal.user_id == user.id,
        Signal.is_saved == 1
    )
    if user.created_at:
        q_pnl = q_pnl.filter(Signal.timestamp >= user.created_at)
    pnl_7d = q_pnl.scalar() or 0.0

    return {
        "win_rate_24h": round(win_rate_24h, 1),
        "signals_evaluated_24h": eval_24h_count,
        "signals_total_evaluated": total_eval,
        "open_signals": open_signals_est,
        "pnl_7d": round(pnl_7d, 2)
    }

def get_performance_chart(db: Session, user: User):
    """
    Returns daily Win/Loss counts for the last 7 days.
    """
    week_ago = datetime.utcnow() - timedelta(days=7)
    test_sources = ['audit_script', 'verification']

    # Query: Date, Result, Count
    # SQLite uses strftime, Postgres uses to_char. Assuming SQLite for now based on context, 
    # but let's try to be generic by grouping in Python or using a simple date truncation if possible.
    # For safety/compatibility, we fetch relevant evaluations and process in Python. 
    # It's less efficient but safe across DB types for this scale.
    
    active_evals = db.query(SignalEvaluation.evaluated_at, SignalEvaluation.result).join(Signal).filter(
        SignalEvaluation.evaluated_at >= week_ago,
        Signal.source.notin_(test_sources),
        Signal.user_id == user.id,
        Signal.is_saved == 1
    ).all()

    # Process in Python
    from collections import defaultdict
    daily_stats = defaultdict(lambda: {"wins": 0, "losses": 0, "date": ""})
    
    # Pre-fill last 7 days to ensure no gaps
    for i in range(7):
        d = (datetime.utcnow() - timedelta(days=6-i)).strftime("%a") # Mon, Tue...
        daily_stats[d]["date"] = d # Ensure key exists

    for ev in active_evals:
        if not ev.evaluated_at: continue
        day_str = ev.evaluated_at.strftime("%a") # Mon, Tue...
        res = str(ev.result).upper()
        
        if "WIN" in res or "TP" in res:
            daily_stats[day_str]["wins"] += 1
        elif "LOSS" in res or "SL" in res:
            daily_stats[day_str]["losses"] += 1
            
    # Convert to list sorted by date (trickier with just "Mon", but we filled in order)
    # Actually, let's just return the list in limits of 7 days sliding window
    # Re-generating keys based on current date to ensure order
    
    final_chart = []
    for i in range(7):
        d_obj = datetime.utcnow() - timedelta(days=6-i)
        day_label = d_obj.strftime("%a")
        final_chart.append({
            "date": day_label,
            "wins": daily_stats[day_label]["wins"],
            "losses": daily_stats[day_label]["losses"]
        })
        
    return final_chart
