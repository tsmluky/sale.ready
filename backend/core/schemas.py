# backend/core/schemas.py
"""
Unified Signal Schema for TraderCopilot Signal Hub.

Este archivo define el esquema estándar que usarán TODAS las señales,
independientemente de su origen (LLM, reglas, trading_lab, etc.).

Objetivo: Permitir un único punto de entrada para logging, API y evaluación.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, EmailStr


class Signal(BaseModel):
    """
    Modelo estándar unificado para TODAS las señales en TraderCopilot.

    Esquema común usado por:
    - LITE (reglas deterministas)
    - PRO (análisis LLM)
    - ADVISOR (gestión de posición)
    - EVALUATED (señales evaluadas)
    - CUSTOM (futuras estrategias de trading_lab)

    Campos principales:
    - timestamp: Momento de generación de la señal (UTC)
    - strategy_id: ID único de la estrategia que generó la señal
    - mode: Modo del análisis (LITE | PRO | ADVISOR | EVALUATED | CUSTOM)
    - token: Activo analizado (ETH, BTC, SOL, XAU, etc.)
    - timeframe: Temporalidad del análisis (30m, 1h, 4h, etc.)
    - direction: Dirección de la operación (long | short | neutral)
    - entry: Precio de entrada sugerido
    - tp: Take profit (opcional)
    - sl: Stop loss (opcional)
    - confidence: Nivel de confianza 0-1 (opcional)
    - rationale: Justificación breve de la señal (≤240 chars, opcional)
    - source: Origen de la señal (LLM | ENGINE | MANUAL | LAB | etc.)
    - extra: Metadatos adicionales específicos de cada estrategia (dict libre)
    """

    timestamp: datetime = Field(
        ...,
        description="Timestamp UTC de generación de la señal",
    )

    strategy_id: str = Field(
        ...,
        description="Identificador único de la estrategia, ej: 'lite_v1', 'rsi_macd_v2', 'deepseek_pro'",
        max_length=100,
    )

    mode: str = Field(
        ...,
        description="Modo de análisis: LITE | PRO | ADVISOR | EVALUATED | CUSTOM",
        max_length=50,
    )

    token: str = Field(
        ...,
        description="Token analizado, en mayúsculas (ETH, BTC, SOL, XAU, etc.)",
        max_length=50,
    )

    timeframe: str = Field(
        ...,
        description="Temporalidad del análisis, ej: 30m, 1h, 4h, 1d",
        max_length=10,
    )

    direction: str = Field(
        ...,
        description="Dirección de operación: 'long', 'short' o 'neutral'",
        max_length=10,
    )

    entry: float = Field(
        ...,
        description="Precio de entrada sugerido",
        gt=0,
    )

    tp: Optional[float] = Field(
        None,
        description="Take profit sugerido",
        gt=0,
    )

    sl: Optional[float] = Field(
        None,
        description="Stop loss sugerido",
        gt=0,
    )

    confidence: Optional[float] = Field(
        None,
        description="Nivel de confianza 0..1 (0 = sin confianza, 1 = máxima confianza)",
        ge=0.0,
        le=1.0,
    )

    rationale: Optional[str] = Field(
        None,
        description="Justificación breve de la señal",
    )

    source: str = Field(
        ...,
        description="Origen de la señal: 'LLM', 'ENGINE', 'MANUAL', 'LAB', etc.",
        max_length=50,
    )
    
    category: Optional[str] = Field(
        None,
        description="Categoría de estrategia: TREND | REVERSION",
        max_length=20
    )

    user_id: Optional[int] = Field(
        None,
        description="ID del usuario propietario de la señal (isolation). Null = Sistema/Global."
    )

    extra: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadatos adicionales específicos de cada estrategia (dict libre)",
    )

    is_saved: Optional[int] = Field(
        0,
        description="Estado de guardado por usuario: 0=No, 1=Si",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-11-21T16:00:00Z",
                "strategy_id": "lite_v2",
                "mode": "LITE",
                "token": "ETH",
                "timeframe": "30m",
                "direction": "long",
                "entry": 3675.50,
                "tp": 3720.00,
                "sl": 3625.00,
                "confidence": 0.68,
                "rationale": "RSI oversold + bullish divergence on 30m",
                "source": "ENGINE",
                "extra": {
                    "rsi": 34.5,
                    "macd_histogram": 2.3,
                    "volume_surge": True,
                },
            }
        }


class SignalCreate(BaseModel):
    """
    Modelo para CREAR una señal (sin timestamp automático en algunos casos).
    Se usa cuando el timestamp debe ser generado por el backend.
    """

    strategy_id: str = Field(..., description="ID de la estrategia", max_length=100)
    mode: str = Field(..., description="Modo del análisis", max_length=50)
    token: str = Field(..., description="Token analizado", max_length=50)
    timeframe: str = Field(..., description="Temporalidad", max_length=10)
    direction: str = Field(..., description="Dirección: long|short|neutral", max_length=10)
    entry: float = Field(..., description="Precio de entrada", gt=0)
    tp: Optional[float] = Field(None, description="Take profit", gt=0)
    sl: Optional[float] = Field(None, description="Stop loss", gt=0)
    confidence: Optional[float] = Field(None, description="Confianza 0-1", ge=0.0, le=1.0)
    rationale: Optional[str] = Field(None, description="Justificación breve")
    source: str = Field(..., description="Origen de la señal", max_length=50)
    extra: Optional[Dict[str, Any]] = Field(None, description="Metadatos adicionales")


class UserCreate(BaseModel):
    """
    Schema for user registration request.
    """
    email: EmailStr = Field(..., description="User email (unique)")
    password: str = Field(..., description="Password (min 8 chars)", min_length=8)
    name: str = Field("Trader", description="User display name")


class UserResponse(BaseModel):
    """
    Schema for user response (safe DTO, no password).
    """
    id: int
    email: str
    name: str
    role: str
    plan: str
    allowed_tokens: Optional[List[str]] = []
    telegram_chat_id: Optional[str] = None
    timezone: Optional[str] = "UTC"
    created_at: datetime
    
    class Config:
        from_attributes = True
