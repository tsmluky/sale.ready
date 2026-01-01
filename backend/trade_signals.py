from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import json  # Used in build_prompt

from app.signal_logger import log_trade_signal
from app.llm_client import LLMClient
from app.market import fetch_ohlcv, compute_indicators, latest_price

router = APIRouter(prefix="", tags=["signals"])

# ======== Modelos ========
class AnalyzeRequest(BaseModel):
    token: str
    timeframe: str
    price: Optional[float] = None
    indicators: Optional[Dict[str, Any]] = None
    mode: str = "LITE"

class AnalyzeResponse(BaseModel):
    ok: bool
    path: Optional[str] = None
    error: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None

# ======== Prompt helper ========
def build_prompt(
    token: str, 
    timeframe: str, 
    price: float | None = None, 
    indicators: Optional[Dict[str, Any]] = None
) -> str:
    try:
        with open("app/prompts/force_trade_signal.md", "r", encoding="utf-8") as f:
            tpl = f.read()
    except Exception:
        tpl = "# Tu respuesta:\n"
    rep = {
        "{{TOKEN}}": token,
        "{{TF}}": timeframe,
        "{{PRICE}}": str(price),
        "{{INDICATORS}}": json.dumps(indicators or {}, ensure_ascii=False)
    }
    for k, v in rep.items():
        tpl = tpl.replace(k, v)
    return tpl

# ======== LLM (DeepSeek/OpenAI-compatible) ========
def call_llm_force_trade_signal(
    prompt: str, 
    token: str, 
    timeframe: str, 
    price: float | None = None
) -> Dict[str, Any]:
    client = LLMClient()
    return client.generate_trade_signal(prompt)

# ======== Endpoint principal ========
@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
        # === Autocompletar precio/indicadores si no se pasan ===
    _price = req.price if (req.price is not None) else None
    _inds  = req.indicators or None
    if _price is None or _inds is None:
        symbol = f"{req.token}/USDT"
        df = fetch_ohlcv("binance", symbol, req.timeframe, limit=200)
        auto_price = latest_price(df)
        auto_inds  = compute_indicators(df)
        if _price is None:
            _price = auto_price
        if _inds is None:
            _inds = auto_inds
    prompt = build_prompt(req.token, req.timeframe, float(_price), _inds)
    try:
        llm_json = call_llm_force_trade_signal(
            prompt, req.token, req.timeframe, req.price
        )
        # Forzar timestamp del backend (UTC actual), aunque el LLM proponga otro
        llm_json["timestamp"] = datetime.now(timezone.utc).isoformat()
    except Exception as e:
        return AnalyzeResponse(ok=False, error=f"llm_error:{e}")

    ok, msg = log_trade_signal(llm_json, mode=req.mode)
    if not ok:
        return AnalyzeResponse(ok=False, error=msg, payload=llm_json)

    return AnalyzeResponse(ok=True, path=msg, payload=llm_json)




