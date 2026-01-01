from __future__ import annotations

from typing import Dict


def _format_market_block(market: Dict) -> str:
    """
    Construye el bloque #CTXT# usando el dict que viene de market_data.snapshot(token).

    Esperamos algo así:
        {
            "token": "eth",
            "symbol": "ETH/USDT",
            "exchange": "mexc",
            "price": 3119.98,
            "change_24h": 3.27,
            "volume_24h": 409799.35,
            "ts": "2025-11-18T23:46:57.294000+00:00"
        }
    """
    token = str(market.get("token", "")).upper()
    symbol = str(market.get("symbol", "N/D"))
    exch = str(market.get("exchange", "N/D"))
    ts = str(market.get("ts", "N/D"))

    price = market.get("price")
    chg24 = market.get("change_24h")
    vol24 = market.get("volume_24h")

    if price is None:
        price_str = "N/D"
    else:
        try:
            price_str = f"~{float(price):.2f}"
        except Exception:
            price_str = "N/D"

    if chg24 is None:
        chg_str = "N/D"
    else:
        try:
            chg_str = f"{float(chg24):.2f}%"
        except Exception:
            chg_str = "N/D"

    if vol24 is None:
        vol_str = "N/D"
    else:
        try:
            vol_str = f"{float(vol24):.2f}"
        except Exception:
            vol_str = "N/D"

    block = [
        "#CTXT#",
        f"- Token: {token}",
        f"- Par / símbolo: {symbol}",
        f"- Exchange: {exch}",
        f"- Fecha (UTC): {ts}",
        f"- Precio spot aprox.: {price_str}",
        f"- Cambio 24h: {chg_str}",
        f"- Volumen 24h: {vol_str}",
    ]
    return "\\n".join(block)


def format_pro_prompt_v2(
    token: str,
    timeframe: str,
    user_message: str,
    market: Dict,
    brain_context: str,
) -> str:
    """
    Construye el prompt PRO completo para TraderCopilot.

    Se apoya en:
        - market: dict con snapshot de mercado (market_data.snapshot(token))
        - brain_context: texto agregado desde backend/brain/{token}/*.txt

    El modelo debe devolver SIEMPRE un bloque markdown delimitado por:
        #ANALYSIS_START
        ...
        #ANALYSIS_END
    con secciones internas claras.
    """
    token_up = token.upper()
    tf_str = timeframe

    ctxt_block = _format_market_block(market)

    brain_block = "#BRAIN#\\n"
    if brain_context.strip():
        brain_block += brain_context.strip()
    else:
        brain_block += "(Sin contexto adicional disponible para este token.)"

    user_block = f"#USER_MSG#\\n{user_message.strip()}"

    task_block = f"""#TASK#
Eres TraderCopilot PRO, un analista técnico y de contexto de nivel profesional.
Tu objetivo es evaluar el activo {token_up} en el timeframe {tf_str} y
proponer un plan operativo claro, realista y táctico.

Instrucciones estrictas:
- Usa SIEMPRE el bloque de contexto de mercado (#CTXT#) como referencia principal de precio actual.
- Usa el contexto de cerebro (#BRAIN#) solo para enriquecer el análisis (narrativa, on-chain, sentimiento, etc.).
- Ten en cuenta el mensaje del usuario (#USER_MSG#) para adaptar el análisis a su duda concreta.
- No inventes datos numéricos que contradigan el bloque #CTXT#.
- Si algún dato clave falta o está como N/D, sé explícito sobre esa limitación.
- Tu salida DEBE estar entre las etiquetas #ANALYSIS_START y #ANALYSIS_END.

Formato de salida (obligatorio, en markdown):

#ANALYSIS_START
#CTXT_RESUMEN#
- Resumen breve del estado actual del mercado para {token_up} ({tf_str}).

#TA#
- Análisis técnico estructurado: soportes, resistencias, tendencias, zonas de liquidez, volatilidad, etc.

#PLAN#
- Propuesta de plan operativo con escenarios (alcista / bajista / lateral).
- Incluye niveles aproximados (entrada, TP, SL) coherentes con el precio actual.

#INSIGHT#
- Comentario extra de valor (riesgos, correlaciones, contexto macro, timing, etc.).

#PARAMS#
- Nivel de riesgo (1-10, donde 1 = muy arriesgado, 10 = muy conservador).
- Horizonte temporal estimado de la operación.
- Confianza relativa en el escenario principal (porcentaje aproximado).

#ANALYSIS_END

Respeta el orden y los encabezados exactamente como se indican.
No añadas nada fuera del bloque #ANALYSIS_START ... #ANALYSIS_END.
"""

    parts = [
        ctxt_block,
        "",
        brain_block,
        "",
        user_block,
        "",
        task_block,
    ]
    return "\\n\\n".join(parts)
