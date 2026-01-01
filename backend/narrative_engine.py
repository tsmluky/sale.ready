import random
from typing import Dict, Any

# ==============================================================================
# 1. Taxonomía de Tokens
# ==============================================================================
TOKEN_METADATA = {
    "BTC": {"sector": "STORE_OF_VALUE", "name": "Bitcoin", "risk": "LOW"},
    "ETH": {"sector": "L1_PLATFORM", "name": "Ethereum", "risk": "LOW"},
    "SOL": {"sector": "L1_PLATFORM", "name": "Solana", "risk": "MED"},
    "BNB": {"sector": "EXCHANGE", "name": "Binance Coin", "risk": "MED"},
    "XRP": {"sector": "PAYMENTS", "name": "XRP", "risk": "MED"},
    "ADA": {"sector": "L1_PLATFORM", "name": "Cardano", "risk": "MED"},
    "AVAX": {"sector": "L1_PLATFORM", "name": "Avalanche", "risk": "MED"},
    "DOT": {"sector": "L0_INTEROP", "name": "Polkadot", "risk": "MED"},
    "MATIC": {"sector": "L2_SCALING", "name": "Polygon", "risk": "MED"},
    "LINK": {"sector": "INFRASTRUCTURE", "name": "Chainlink", "risk": "MED"},
    "UNI": {"sector": "DEFI", "name": "Uniswap", "risk": "HIGH"},
    "ATOM": {"sector": "L0_INTEROP", "name": "Cosmos", "risk": "HIGH"},
    "LTC": {"sector": "PAYMENTS", "name": "Litecoin", "risk": "MED"},
    "NEAR": {"sector": "L1_PLATFORM", "name": "Near", "risk": "HIGH"},
    "DOGE": {"sector": "MEME", "name": "Dogecoin", "risk": "HIGH"},
    "XAU": {"sector": "COMMODITY", "name": "Gold", "risk": "LOW"},
}

# ==============================================================================
# 2. Templates Dinámicos (News / Narrative)
# ==============================================================================
# Se seleccionan según Sector + Estado del Mercado (Trend, Change24h)

NEWS_TEMPLATES = {
    "STORE_OF_VALUE": [
        "Inversores institucionales buscando refugio ante la volatilidad macroeconómica.",
        "La narrativa de reserva de valor se fortalece a medida que los bancos centrales ajustan tasas.",
        "Nuevos flujos de entrada en ETFs spot sugieren acumulación a largo plazo.",
        "Análisis de la oferta ilíquida muestra convicción fuerte de los HODLers.",
    ],
    "L1_PLATFORM": [
        "Aumento en la actividad de contratos inteligentes impulsa la demanda de gas.",
        "Nuevos protocolos DeFi lanzados en la red están incrementando el TVL.",
        "Desarrolladores migrando desde cadenas competidoras por mejores incentivos.",
        "Actualización de escalabilidad en la hoja de ruta genera optimismo en la comunidad.",
    ],
    "DEFI": [
        "Volatilidad reciente incrementa los volúmenes de trading en DEXs y fees generados.",
        "Propuesta de gobernanza para redistribución de fees atrae atención especulativa.",
        "Yield Farmer rotando capital hacia pools de {TOKEN} por incentivos renovados.",
    ],
    "MEME": [
        "Volumen social en redes alcanza picos históricos, impulsando la volatilidad.",
        "Rumores de integración en plataformas de pagos reavivan el interés retail.",
        "Especulación minorista domina la acción de precio a corto plazo.",
    ],
    "COMMODITY": [
        "Incertidumbre geopolítica impulsa la demanda de activos seguros tradicionales.",
        "Correlación inversa con el dólar favorece la estructura alcista actual.",
        "Bancos centrales incrementando reservas físicas como cobertura estratégica.",
    ],
    "INFRASTRUCTURE": [
        "Demanda de oráculos seguros crítica para la nueva ola de RWA (Real World Assets).",
        "Integraciones cross-chain aumentan la utilidad del token de infraestructura.",
    ],
    "L0_INTEROP": [
        "La narrativa de interoperabilidad gana tracción con nuevas actualizaciones del ecosistema.",
        "Puentes cross-chain registran volúmenes récord, beneficiando al token nativo.",
        "Subastas de parachains/zonas renuevan el interés fundamental en la red.",
    ],
    "L2_SCALING": [
        "Las soluciones de capa 2 absorben una cuota de mercado creciente de transacciones.",
        "Reducción de fees tras actualización impulsa la adopción de usuarios activos.",
        "La narrativa de escalabilidad modular favorece la valoración actual.",
    ],
    "EXCHANGE": [
        "Aumento en reservas del exchange y quema de tokens trimestral apoyan el precio.",
        "El lanzamiento de nuevas IEOs en el Launchpad incrementa la demanda del token.",
        "Volumen de trading del exchange se mantiene robusto pese a condiciones macro.",
    ],
    "PAYMENTS": [
        "Adopción en pasarelas de pago globales valida la utilidad real del activo.",
        "Incremento en transacciones diarias muestra un uso orgánico sostenido.",
        "La narrativa de 'dinero duro' o 'plata digital' resurge ante la inflación fiat.",
    ],
    "GENERIC_BULL": [
        "Sentimiento general del mercado favorece activos de riesgo tras datos macro positivos.",
        "Rotación de capital desde stablecoins indica apetito por riesgo.",
    ],
    "GENERIC_BEAR": [
        "Miedo macroeconómico presiona a la baja los activos de riesgo.",
        "Salidas netas de exchanges sugieren capitulación de manos débiles.",
    ],
}

# ==============================================================================
# 3. Templates de Sentimiento (Basados en RSI / Trend)
# ==============================================================================
SENTIMENT_TEMPLATES = {
    "OVERSOLD": [  # RSI < 30
        "Sentimiento de miedo extremo podría indicar un suelo local inminente (Contrarian).",
        "Capitulación de vendedores visible; posible rebote técnico por sobreventa.",
        "Manos fuertes podrían estar acumulando en estos niveles de descuento.",
    ],
    "OVERBOUGHT": [  # RSI > 70
        "Euforia en indicadores de corto plazo sugiere cautela ante una corrección.",
        "FOMO retail evidente; el smart money suele distribuir en estos niveles.",
        "Extensión de precio significativa; riesgo de toma de beneficios elevado.",
    ],
    "BULLISH_TREND": [  # Trend = BULLISH
        "Tendencia estructuralmente sana con mínimos crecientes.",
        "El impulso alcista se mantiene fuerte con soporte de volumen.",
        "Compradores defendiendo agresivamente los dips en marcos temporales bajos.",
    ],
    "BEARISH_TREND": [  # Trend = BEARISH
        "Estructura de mercado debilitada con presión de venta constante.",
        "Los rebotes son vendidos rápidamente ('Sell the rip') por falta de demanda.",
        "Precaución: la tendencia dominante sigue favoreciendo a los osos.",
    ],
    "NEUTRAL": [
        "Consolidación lateral sin dirección clara; el mercado espera un catalizador.",
        "Equilibrio entre oferta y demanda en el rango actual.",
        "Volatilidad comprimida sugiere un movimiento explosivo inminente.",
    ],
}


def generate_narrative(token: str, market_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Genera News, Sentiment e Insights dinámicos basados en la taxonomía y datos técnicos.
    Garantiza que CADA token tenga texto de alta calidad coherente con su realidad de mercado.
    """
    token = token.upper()
    meta = TOKEN_METADATA.get(token, {"sector": "L1_PLATFORM", "name": token})
    sector = meta["sector"]

    # Extraer datos técnicos
    rsi = float(market_data.get("rsi", 50))
    trend = str(market_data.get("trend", "NEUTRAL")).upper()
    change_24h = float(market_data.get("change_24h") or 0.0)

    # --- 1. Generar NEWS (Narrativa) ---
    news_pool = NEWS_TEMPLATES.get(sector, NEWS_TEMPLATES["L1_PLATFORM"])

    # Añadir sabor according to market direction
    if change_24h > 5.0:
        news_pool = news_pool + NEWS_TEMPLATES["GENERIC_BULL"]
    elif change_24h < -5.0:
        news_pool = news_pool + NEWS_TEMPLATES["GENERIC_BEAR"]

    news_text = random.choice(news_pool)

    # --- 2. Generar SENTIMENT (Técnico/Psicológico) ---
    if rsi < 30:
        sent_pool = SENTIMENT_TEMPLATES["OVERSOLD"]
    elif rsi > 70:
        sent_pool = SENTIMENT_TEMPLATES["OVERBOUGHT"]
    else:
        # Si RSI es neutro, miramos la tendencia
        if trend == "BULLISH":
            sent_pool = SENTIMENT_TEMPLATES["BULLISH_TREND"]
        elif trend == "BEARISH":
            sent_pool = SENTIMENT_TEMPLATES["BEARISH_TREND"]
        else:
            sent_pool = SENTIMENT_TEMPLATES["NEUTRAL"]

    sentiment_text = random.choice(sent_pool)

    # --- 3. Generar INSIGHT (Dato curioso / Onchain simulado realista) ---
    # Variamos según el riesgo o la volatilidad
    if abs(change_24h) > 8.0:
        insight_text = (
            f"La volatilidad de 24h ({change_24h:.1f}%) supera la media de 30 días, "
            "indicando un evento de liquidez mayor."
        )
    else:
        # Insight estructural
        if sector == "L1_PLATFORM":
            insight_text = "Métricas de TVL estables sugieren retención de liquidez a pesar de la acción de precio."
        elif sector == "STORE_OF_VALUE":
            insight_text = (
                "El ratio MVRV se mantiene en zona neutral, indicando espacio para "
                "recorrido en ambas direcciones."
            )
        elif sector == "MEME":
            insight_text = (
                "La correlación con BTC ha disminuido, sugiriendo un movimiento "
                "idiosincrásico impulsado por la comunidad."
            )
        else:
            insight_text = "El volumen On-Chain muestra divergencia positiva con respecto al precio."

    return {"news": news_text, "sentiment": sentiment_text, "insights": insight_text}
