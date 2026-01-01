from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Signal(Base):
    __tablename__ = "signals"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    token = Column(String)
    timeframe = Column(String)
    direction = Column(String)
    entry = Column(Float)
    tp = Column(Float)
    sl = Column(Float)
    confidence = Column(Float)
    rationale = Column(Text)
    source = Column(String)
    mode = Column(String) # LITE, PRO, ADVISOR
    raw_response = Column(Text, nullable=True)
    strategy_id = Column(String, nullable=True)
    
    # Validation / Isolation
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Idempotency constraint (Strict)
    idempotency_key = Column(String, unique=True, index=True, nullable=True)
    
    # Relationship to evaluation
    evaluation = relationship(lambda: SignalEvaluation, back_populates="signal", uselist=False, viewonly=True)

    # Soft Delete / Admin Visibility
    is_hidden = Column(Integer, default=0) # 0=Visible, 1=Hidden (Boolean as Integer for SQLite/Postgres compatibility)
    is_saved = Column(Integer, default=0) # 0=Transient, 1=Saved/Tracked by user
    extra = Column(Text, nullable=True) # JSON Metadata encoded as string


class SignalEvaluation(Base):
    __tablename__ = "signal_evaluations"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    signal_id = Column(Integer, ForeignKey("signals.id"))
    evaluated_at = Column(DateTime, default=datetime.utcnow)
    result = Column(String) # WIN, LOSS, BE
    pnl_r = Column(Float)
    exit_price = Column(Float)
    
    signal = relationship(lambda: Signal, back_populates="evaluation", overlaps="signal")

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    name = Column(String)
    hashed_password = Column(String)
    role = Column(String, default="user") # Permissions: user, admin
    
    # Monetization / Entitlements
    plan = Column(String, default="FREE") # FREE, PRO, OWNER
    plan_status = Column(String, default="active") # active, inactive
    plan_expires_at = Column(DateTime, nullable=True)

    # Notifications
    telegram_chat_id = Column(String, nullable=True) # User's personal Chat ID
    timezone = Column(String, default="UTC") # User's preferred timezone

    created_at = Column(DateTime, default=datetime.utcnow)


class StrategyConfig(Base):
    """
    Configuración de estrategias 24/7 para el scheduler.
    
    Cada registro representa una estrategia que puede ejecutarse
    automáticamente en el backend.
    """
    __tablename__ = "strategy_configs"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    strategy_id = Column(String)  # ej: "rsi_macd_v1" (Logic Class ID) - NOT UNIQUE anymore
    persona_id = Column(String, unique=True, nullable=True) # ej: "trend_king_sol" (Instance ID)
    
    name = Column(String)  # Nombre legible
    description = Column(Text, nullable=True)
    version = Column(String, default="1.0.0")
    
    # Ownership & Marketplace
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # None = System
    is_public = Column(Integer, default=0) # 0=Private, 1=Public
    color = Column(String, default="indigo")
    icon = Column(String, default="Cpu")
    expected_roi = Column(String, nullable=True)
    
    # Configuración operativa
    enabled = Column(Integer, default=1)  # 1 = activa, 0 = pausada
    interval_seconds = Column(Integer, default=300)  # Cada cuánto ejecutar (5 min default)
    tokens = Column(String)  # JSON array: ["ETH", "BTC", "SOL"]
    timeframes = Column(String)  # JSON array: ["30m", "1h"]
    
    # Metadatos
    risk_profile = Column(String, default="medium")  # low | medium | high
    mode = Column(String, default="CUSTOM")  # LITE | PRO | CUSTOM
    source_type = Column(String, default="ENGINE")  # ENGINE | LLM | HYBRID
    
    # Estadísticas (actualizadas por evaluaciones)
    total_signals = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    avg_confidence = Column(Float, default=0.0)
    last_execution = Column(DateTime, nullable=True)
    
    # Config JSON (parámetros específicos de la estrategia)
    config_json = Column(Text, nullable=True)  # JSON: {"rsi_period": 14, ...}
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PushSubscription(Base):
    __tablename__ = "push_subscriptions"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    endpoint = Column(String, unique=True)
    p256dh = Column(String)
    auth = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class SchedulerLock(Base):
    """
    Lock distribuido para evitar múltiples instancias del scheduler.
    """
    __tablename__ = "scheduler_lock"
    __table_args__ = {'extend_existing': True}

    lock_name = Column(String, primary_key=True) # "main_scheduler"
    owner_id = Column(String) # UUID de la instancia
    expires_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AdminAuditLog(Base):
    """
    Registro inmutable de acciones administrativas.
    REQ: Trazabilidad completa (Sale-Ready).
    """
    __tablename__ = "admin_audit_logs"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String) # UPDATE_PLAN, HIDE_SIGNAL, UNHIDE_SIGNAL
    target_id = Column(String) # ID del recurso afectado (User ID o Signal ID)
    details = Column(Text) # JSON o texto descriptivo
    
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class DailyUsage(Base):
    """
    Control de cuotas diarias por usuario.
    Clave compuesta única: (user_id, feature, date).
    """
    __tablename__ = "daily_usage"
    __table_args__ = (
        UniqueConstraint('user_id', 'feature', 'date', name='uq_user_feature_date'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id")) # index=True removed to prevent duplicate metadata crash
    feature = Column(String)
    date = Column(String)     # YYYY-MM-DD
    count = Column(Integer, default=0)


    # Unique constraint to prevent race conditions (handled by DB logic usually, 
    # but index helps). In Postgres we'd use a UniqueConstraint.
    # For now, we rely on the application logic 'check_and_increment' doing a localized lock


class CopilotProfile(Base):
    """
    Perfil de preferencias del Copilot para personalización.
    Relación 1:1 con User.
    """
    __tablename__ = "copilot_profiles"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Preferencias
    trader_style = Column(String, default="BALANCED") # SCALPER, SWING, DAY, BALANCED
    risk_tolerance = Column(String, default="MEDIUM") # LOW, MEDIUM, HIGH, DEGEN
    time_horizon = Column(String, default="INTRADAY") # SCALP, INTRADAY, SWING, LONG_TERM
    
    # Contexto libre
    custom_instructions = Column(Text, nullable=True) # "Prefiero evitar meme coins..."
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación simple
    user = relationship("User")


