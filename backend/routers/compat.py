from __future__ import annotations
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional
import pathlib


# === Cargar .env directamente desde backend/.env ===
BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
ENV_PATH = BASE_DIR / ".env"
# ==== Adaptadores /analyze/{lite,pro} ====
# NOTE: /analyze/advisor removed (unified in main.py via advisor router)

class LiteIn(BaseModel):
    token: str
    timeframe: str = "30m"



async def _call_analyze(payload: dict):
    # Preferimos llamada interna al método si existe; si no, fallback HTTP local
    try:
        # Truco para importar main.py desde routers/ sin ser paquete
        import sys
        import os
        
        # Añadir directorio padre (backend) al path si no está
        current = os.path.dirname(os.path.abspath(__file__))
        parent = os.path.dirname(current)
        if parent not in sys.path:
            sys.path.append(parent)
            
        import main
        
        # Reconstruir el objeto request usando la clase definida en main
        # Nota: main.AnalysisRequest debe estar disponible
        req = main.AnalysisRequest(**payload)
        return await main.analyze_token(req)
    except Exception as e:
        print(f"[COMPAT ERROR] Internal import failed: {e}")
        import httpx
        
        port = os.getenv("PORT", "8010")
        url = os.getenv("SELF_ANALYZE_URL", f"http://127.0.0.1:{port}/analyze")
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(url, json=payload)
            if r.status_code >= 400:
                raise HTTPException(status_code=r.status_code, detail=r.text)
            try:
                return r.json()
            except Exception:
                return {"raw": r.text}


@router.post("/analyze/lite")
async def analyze_lite(body: LiteIn):
    payload = {
        "token": body.token.lower(),
        "message": (
            f"Genera una señal LITE timeframe {body.timeframe}. "
            "Devuelve JSON compacto con entry/tp/sl/confidence y razón (≤240c)."
        ),
        "mode": "lite",
        "timeframe": body.timeframe,
    }
    return await _call_analyze(payload)


class ProIn(BaseModel):
    token: str
    timeframe: str = "30m"
    context: Optional[dict] = None


@router.post("/analyze/pro")
async def analyze_pro(body: ProIn):
    payload = {
        "token": body.token.lower(),
        "message": (
            "Análisis PRO en bloque #ANALYSIS_START..END con secciones "
            "#CTXT #TA #PLAN #INSIGHT #PARAMS. Sé estricto."
        ),
        "mode": "pro",
        "timeframe": body.timeframe,
    }
    return await _call_analyze(payload)



