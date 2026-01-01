from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.backtest_engine import BacktestEngine

router = APIRouter(prefix="/backtest", tags=["backtest"])


class BacktestRequest(BaseModel):
    strategy_id: str
    token: str = "BTC"
    timeframe: str = "1h"
    days: int = 30
    initial_capital: float = 1000.0


@router.post("/run")
def run_backtest(req: BacktestRequest):
    """
    Ejecuta una simulación histórica de una estrategia.
    """
    results = None
    try:
        engine = BacktestEngine(initial_capital=req.initial_capital)

        # Mapping simple names to IDs if needed, or pass direct ID
        # User might send "rsi_divergence" but file is "rsi_divergence.py"
        # engine.load_strategy expects filename without .py

        # Intento de normalización básica
        strat_id = req.strategy_id.replace(".py", "")

        results = engine.run(
            strategy_id=strat_id,
            # Engine/API expects lowercase usually? Market API handles both
            symbol=req.token.lower(),
            timeframe=req.timeframe,
            days=req.days,
        )

        return results

    except Exception as e:
        import traceback

        print(f"❌ [API CRITICAL BACKTEST ERROR]: {e}")
        traceback.print_exc()
        try:
            # Intentar ver si es error de serialización
            if results:
                from fastapi.encoders import jsonable_encoder

                jsonable_encoder(results)
        except Exception as se:
            print(f"❌ [SERIALIZATION ERROR]: {se}")
            raise HTTPException(status_code=500, detail=f"Serialization Error: {se}")

        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategies")
def list_backtestable_strategies():
    """
    Devuelve lista de estrategias disponibles para backtest
    (Simulado escaneando directorio de estrategias)
    """
    import os

    strategies = []
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    strat_dir = os.path.join(base_dir, "strategies")

    for f in os.listdir(strat_dir):
        if (
            f.endswith(".py")
            and f != "__init__.py"
            and f != "base.py"
            and f != "registry.py"
        ):
            strategies.append(f.replace(".py", ""))

    return {"strategies": strategies}
