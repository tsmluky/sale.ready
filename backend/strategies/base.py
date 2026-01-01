# backend/strategies/base.py
"""
Base Strategy Class for TraderCopilot Signal Hub.

Define la interfaz abstracta que TODAS las estrategias deben implementar
para integrarse seamlessly con el Signal Hub.

Diseñado para:
1. Estrategias cuantitativas de trading_lab (RSI, MACD, Mean Reversion, etc.)
2. Reglas deterministas actuales (LITE v2)
3. Estrategias LLM-based (PRO, ADVISOR)
4. Estrategias custom de terceros

Flujo de integración:
1. Heredar de Strategy
2. Implementar generate_signals()
3. Devolver lista de instancias Signal
4. El hub automáticamente loguea y expone por API
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

# Import del schema unificado
import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))
from core.schemas import Signal


class StrategyMetadata(BaseModel):
    """
    Metadatos descriptivos de una estrategia.
    
    Se usa para catálogo, UI y gestión de estrategias disponibles.
    """
    
    id: str = Field(
        ...,
        description="ID único de la estrategia, ej: 'lite_v2', 'rsi_divergence_v1'",
        max_length=100,
    )
    
    name: str = Field(
        ...,
        description="Nombre legible, ej: 'LITE Rule Engine v2'",
        max_length=200,
    )
    
    description: str = Field(
        ...,
        description="Descripción breve de la estrategia y su enfoque",
        max_length=500,
    )
    
    version: str = Field(
        ...,
        description="Versión semántica, ej: '2.1.0'",
        max_length=20,
    )
    
    default_timeframe: str = Field(
        default="30m",
        description="Timeframe predeterminado, ej: '30m', '1h', '4h'",
        max_length=10,
    )
    
    universe: List[str] = Field(
        default_factory=list,
        description="Tokens soportados: ['ETH', 'BTC', 'SOL', 'XAU'] o ['*'] para todos",
    )
    
    risk_profile: Literal["low", "medium", "high", "custom"] = Field(
        default="medium",
        description="Perfil de riesgo de la estrategia",
    )
    
    mode: str = Field(
        ...,
        description="Modo principal: LITE | PRO | ADVISOR | CUSTOM",
        max_length=50,
    )
    
    source_type: Literal["ENGINE", "LLM", "HYBRID", "MANUAL", "LAB"] = Field(
        default="ENGINE",
        description="Tipo de origen de señales",
    )
    
    category: Literal["TREND", "REVERSION", "NEUTRAL"] = Field(
        default="NEUTRAL",
        description="Categoría de mercado: TREND (Tendencia) o REVERSION (Rango)",
    )
    
    enabled: bool = Field(
        default=True,
        description="Si está activa y disponible para uso",
    )
    
    config: Optional[Dict[str, Any]] = Field(
        None,
        description="Configuración específica de la estrategia (parámetros customizables)",
    )


class Strategy(ABC):
    """
    Clase base abstracta para TODAS las estrategias en TraderCopilot.
    
    Contrato:
    - Toda estrategia debe exponer metadata() para describirse
    - Toda estrategia debe implementar generate_signals() para producir señales
    - Las señales deben ser instancias del modelo Signal unificado
    
    Ejemplo de implementación:
    
    ```python
    from strategies.base import Strategy, StrategyMetadata
from backend.core.schemas import Signal
    from datetime import datetime
    
    class RSIMACDStrategy(Strategy):
        def metadata(self) -> StrategyMetadata:
            return StrategyMetadata(
                id="rsi_macd_v1",
                name="RSI + MACD Divergence",
                description="Detecta divergencias entre RSI y MACD para señales contrarian",
                version="1.0.0",
                universe=["ETH", "BTC", "SOL"],
                risk_profile="medium",
                mode="CUSTOM",
                source_type="ENGINE",
            )
        
        def generate_signals(
            self,
            tokens: List[str],
            timeframe: str,
            context: Optional[Dict[str, Any]] = None
        ) -> List[Signal]:
            signals = []
            for token in tokens:
                # Lógica de la estrategia aquí
                signal = Signal(
                    timestamp=datetime.utcnow(),
                    strategy_id=self.metadata().id,
                    mode="CUSTOM",
                    token=token,
                    timeframe=timeframe,
                    direction="long",
                    entry=3675.50,
                    tp=3720.00,
                    sl=3625.00,
                    confidence=0.75,
                    rationale="RSI divergence + MACD cross",
                    source="LAB",
                    extra={"rsi": 34.5, "macd": 2.3}
                )
                signals.append(signal)
            return signals
    ```
    """
    
    @abstractmethod
    def metadata(self) -> StrategyMetadata:
        """
        Devuelve los metadatos descriptivos de la estrategia.
        
        Se usa para:
        - Catálogo de estrategias disponibles en la UI
        - Validación de compatibilidad token/timeframe
        - Gestión de perfiles de riesgo
        
        Returns:
            StrategyMetadata con toda la info descriptiva
        """
        raise NotImplementedError("metadata() must be implemented by strategy class")
    
    @abstractmethod
    def generate_signals(
        self,
        tokens: List[str],
        timeframe: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Signal]:
        """
        Ejecuta la estrategia y devuelve señales para los tokens especificados.
        
        Args:
            tokens: Lista de tokens a analizar, ej: ["ETH", "BTC", "SOL"]
            timeframe: Timeframe del análisis, ej: "30m", "1h", "4h"
            context: Contexto adicional opcional (market data, config, etc.)
        
        Returns:
            Lista de instancias Signal generadas por la estrategia
            
        Nota:
        - Puede devolver lista vacía si no hay setups válidos
        - Las señales deben tener strategy_id coincidente con metadata().id
        - El timestamp debe ser UTC
        """
        raise NotImplementedError("generate_signals() must be implemented by strategy class")
    
    # === Helper methods opcionales para estrategias ===
    
    def validate_tokens(self, tokens: List[str]) -> List[str]:
        """
        Valida que los tokens estén soportados por esta estrategia.
        
        Returns:
            Lista de tokens válidos (filtrados)
        """
        meta = self.metadata()
        if "*" in meta.universe:
            return tokens
        return [t for t in tokens if t.upper() in meta.universe]
    
    def is_enabled(self) -> bool:
        """
        Verifica si la estrategia está activa.
        
        Returns:
            True si está habilitada, False en caso contrario
        """
        return self.metadata().enabled
    
    def __repr__(self) -> str:
        meta = self.metadata()
        return f"<Strategy {meta.id} - {meta.name} [{meta.mode}]>"

