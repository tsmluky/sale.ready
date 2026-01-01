from __future__ import annotations
from datetime import datetime
from typing import Optional, Literal, List

from pydantic import BaseModel, Field


# == Request models ==


from pydantic import BaseModel, Field, field_validator, ConfigDict

class LiteReq(BaseModel):
    token: str = Field(..., description="Token base: eth|btc|sol|xau")
    timeframe: str = Field(..., description="Timeframe, e.g. 30m, 1h, 4h")
    mode: Literal["LITE"] = "LITE" # Make mode explicit and validated
    message: Optional[str] = None # For Audit/Persistence Markers

    model_config = ConfigDict(extra="forbid")

    @field_validator('timeframe')
    def validate_timeframe(cls, v):
        allowed = {'5m', '15m', '30m', '1h', '4h', '1d', '1w'}
        if v not in allowed:
            raise ValueError(f"Timeframe must be one of {allowed}")
        return v


class ProReq(BaseModel):
    token: str = Field(..., description="Token base: eth|btc|sol|xau")
    timeframe: str = Field(..., description="Timeframe, e.g. 30m, 1h, 4h")
    user_message: Optional[str] = Field(
        None,
        description="Mensaje opcional del usuario para contextualizar el análisis PRO",
    )


class AdvisorReq(BaseModel):
    token: str = Field(..., description="Token base: eth|btc|sol|xau")
    direction: Literal["long", "short"] = Field(..., description="Dirección de la posición")
    entry: float = Field(..., description="Precio de entrada de la posición")
    tp: float = Field(..., description="Take profit previsto")
    sl: float = Field(..., description="Stop loss previsto")
    size_quote: float = Field(..., description="Tamaño de la posición en moneda de cotización (ej. USDT)")


# == Response models ==

class LiteSignal(BaseModel):
    """
    Señal LITE generada por el motor de reglas.

    Esquema oficial:
    {
     "timestamp":"2025-11-16T14:00:00Z",
     "token":"ETH","timeframe":"30m","direction":"long|short",
     "entry":3675.50,"tp":3720.00,"sl":3625.00,
     "confidence":0.68,"rationale":"≤240c","source":"lite-rule@v1"
    }
    """
    timestamp: datetime = Field(..., description="Timestamp UTC de generación de la señal")
    token: str = Field(..., description="Token analizado, en mayúsculas (ETH/BTC/SOL/XAU)")
    timeframe: str = Field(..., description="Timeframe, ej. 30m, 1h, 4h")
    direction: Literal["long", "short"] = Field(..., description="Dirección de la operación propuesta")
    entry: float = Field(..., description="Precio de entrada sugerido")
    tp: float = Field(..., description="Take profit sugerido")
    sl: float = Field(..., description="Stop loss sugerido")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confianza 0..1 de la señal")
    rationale: str = Field(..., description="Racional breve de la señal")
    # 🔧 Cambio clave: ahora tiene valor por defecto → si el backend no lo envía, no peta
    source: str = Field(
        default="lite-rule@v1",
        description="Identificador de la regla/versión, ej. lite-rule@v1",
    )
    source_exchange: Optional[str] = Field(
        None,
        description="Exchange fuente de los datos (binance, kucoin, mock)"
    )


class AdvisorAlternative(BaseModel):
    if_: str = Field(..., alias="if", description="Condición: si pasa esto…")
    action: str = Field(..., description="Acción táctica recomendada")
    rr_target: float = Field(..., description="RR objetivo asociado a este escenario")


class AdvisorResp(BaseModel):
    """
    Respuesta del asesor de posición abierta.

    Esquema oficial:
    {
     "token":"ETH","direction":"long","entry":3675.50,"size_quote":500,"tp":3720.00,"sl":3625.00,
     "alternatives":[{"if":"breaks 3700 with volume","action":"trail sl to 3668","rr_target":1.7},
                     {"if":"falls below 3640","action":"reduce 50%","rr_target":1.2}],
     "risk_score":0.44,"confidence":0.63
    }
    """
    token: str = Field(..., description="Token de la posición")
    direction: Literal["long", "short"] = Field(..., description="Dirección de la posición")
    entry: float = Field(..., description="Precio de entrada de la posición")
    size_quote: float = Field(..., description="Tamaño de la posición en moneda de cotización")
    tp: float = Field(..., description="Take profit actual o recomendado")
    sl: float = Field(..., description="Stop loss actual o recomendado")
    alternatives: List[AdvisorAlternative] = Field(
        default_factory=list,
        description="Escenarios alternativos con acciones condicionales",
    )
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Score de riesgo 0..1 (1 = riesgo muy bajo)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confianza en el plan propuesto")

class CopilotProfileBase(BaseModel):
    trader_style: Optional[str] = "BALANCED"
    risk_tolerance: Optional[str] = "MEDIUM"
    time_horizon: Optional[str] = "INTRADAY"
    custom_instructions: Optional[str] = None

class CopilotProfileCreate(CopilotProfileBase):
    pass

class CopilotProfileUpdate(CopilotProfileBase):
    pass

class CopilotProfileResp(CopilotProfileBase):
    id: int
    user_id: int
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
